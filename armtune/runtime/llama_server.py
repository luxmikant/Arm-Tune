"""llama-server subprocess adapter — OpenAI-compatible API with timing evidence.

This adapter launches the llama.cpp ``llama-server`` binary as a managed
subprocess and measures inference through its REST API. Using the server
binary (rather than the Python bindings) lets ArmTune benchmark the exact
binary that was compiled with Arm KleidiAI / -mcpu=native optimizations,
and capture its startup ``system_info`` evidence (NEON, I8MM, SVE, ...).

The binary is resolved from, in order: the ``binary`` argument, the
``ARMTUNE_LLAMA_SERVER`` environment variable, or ``llama-server`` on PATH.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import httpx

from .base import GenerationRequest, GenerationResponse, RuntimeAdapter

EVIDENCE_MARKERS = (
    "system_info:",
    "CPU_KLEIDIAI",
    "CPU_AARCH64",
    "NEON",
    "I8MM",
    "SVE",
    "llm_load_tensors:",
    "n_threads",
    "KV buffer size",
)


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class LlamaServerAdapter(RuntimeAdapter):
    def __init__(
        self,
        model_path: str | None = None,
        binary: str | None = None,
        n_threads: int = 4,
        n_threads_batch: int = 0,
        n_ctx: int = 2048,
        n_parallel: int = 1,
        batch_size: int = 512,
        enable_mmap: bool = True,
        enable_mlock: bool = False,
        enable_prompt_cache: bool = False,
        prompt_cache_path: str | None = None,
        port: int = 0,
        extra_args: list[str] | None = None,
    ) -> None:
        self._model_path = model_path
        self._binary = (
            binary
            or os.environ.get("ARMTUNE_LLAMA_SERVER")
            or shutil.which("llama-server")
            or "llama-server"
        )
        self._threads = n_threads
        self._threads_batch = n_threads_batch
        self._ctx = n_ctx
        self._parallel = n_parallel
        self._batch = batch_size
        self._mmap = enable_mmap
        self._mlock = enable_mlock
        self._prompt_cache = enable_prompt_cache
        self._prompt_cache_path = prompt_cache_path
        self._port = port or find_free_port()
        self._extra_args = extra_args or []
        self._proc: subprocess.Popen | None = None
        self._stderr_lines: list[str] = []
        self._reader: threading.Thread | None = None
        self.evidence: dict = {}

    @property
    def model_path(self) -> str | None:
        return self._model_path

    @property
    def process_id(self) -> int | None:
        return self._proc.pid if self._proc else None

    def initialize(self) -> None:
        if not self._model_path or not Path(self._model_path).exists():
            raise FileNotFoundError(f"Model not found: {self._model_path}")

        cmd = [
            self._binary,
            "-m", self._model_path,
            "--host", "127.0.0.1",
            "--port", str(self._port),
            "-t", str(self._threads),
            "-c", str(self._ctx),
            "-np", str(self._parallel),
            "-b", str(self._batch),
        ]
        if self._threads_batch > 0:
            cmd += ["-tb", str(self._threads_batch)]
        if not self._mmap:
            cmd += ["--no-mmap"]
        if self._mlock:
            cmd += ["--mlock"]
        if self._prompt_cache:
            cmd += ["--prompt-cache"]
            if self._prompt_cache_path:
                cmd += [self._prompt_cache_path]
        cmd += self._extra_args

        self._stderr_lines = []
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._reader = threading.Thread(target=self._collect_stderr, daemon=True)
        self._reader.start()

        deadline = time.time() + 120
        while time.time() < deadline:
            if self._proc.poll() is not None:
                raise RuntimeError(
                    f"llama-server exited early (code {self._proc.returncode}): "
                    f"{''.join(self._stderr_lines[-15:])}"
                )
            try:
                r = httpx.get(f"http://127.0.0.1:{self._port}/health", timeout=1.0)
                if r.status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("llama-server did not become ready in time")

        self._extract_evidence()

    def _collect_stderr(self) -> None:
        assert self._proc is not None and self._proc.stderr is not None
        for line in self._proc.stderr:
            self._stderr_lines.append(line.rstrip())

    def _extract_evidence(self) -> None:
        for line in self._stderr_lines:
            if any(marker in line for marker in EVIDENCE_MARKERS):
                stripped = line.strip()
                if "=" in stripped or ":" in stripped:
                    key = stripped.split(":", 1)[0].strip()
                    if len(key) < 60:
                        self.evidence[key] = stripped

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if self._proc is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        payload = {
            "prompt": request.prompt,
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "seed": request.seed,
            "stream": True,
        }

        start = time.perf_counter()
        first_token_time: float | None = None
        text_parts: list[str] = []
        chunks = 0
        timings: dict = {}

        with httpx.stream(
            "POST",
            f"http://127.0.0.1:{self._port}/completion",
            json=payload,
            timeout=600.0,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                content = data.get("content", "")
                if content:
                    text_parts.append(content)
                if "timings" in data and isinstance(data["timings"], dict):
                    timings = data["timings"]
                chunks += 1

        end = time.perf_counter()
        ttft = (first_token_time - start) if first_token_time else 0.0
        total = end - start

        prompt_tokens = int(timings.get("prompt_n", 0))
        completion_tokens = int(
            timings.get("predicted_n", 0) or max(chunks, len(text_parts))
        )
        prompt_tps = float(timings.get("prompt_per_second", 0.0))
        decode_tps = float(timings.get("predicted_per_second", 0.0))
        if decode_tps <= 0 and total > 0 and completion_tokens > 0:
            decode_tps = (completion_tokens - 1) / max(total - ttft, 1e-6)

        return GenerationResponse(
            text="".join(text_parts),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            ttft_seconds=ttft,
            total_seconds=total,
            tokens_per_second=decode_tps,
            prompt_tokens_per_second=prompt_tps,
        )

    def shutdown(self) -> None:
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=10)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None
        if self._reader is not None:
            self._reader.join(timeout=2)
            self._reader = None

    def is_available(self) -> bool:
        return shutil.which(self._binary) is not None


__all__ = ["LlamaServerAdapter", "find_free_port"]
