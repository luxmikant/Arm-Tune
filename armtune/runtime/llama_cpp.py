"""llama.cpp runtime adapter."""

from __future__ import annotations

import os
import time
from importlib.util import find_spec

from .base import GenerationRequest, GenerationResponse, RuntimeAdapter


class LlamaCppAdapter(RuntimeAdapter):
    def __init__(
        self,
        model_path: str | None = None,
        n_threads: int | None = None,
        n_ctx: int = 2048,
    ) -> None:
        self._model_path = model_path
        self.n_threads = n_threads
        self.n_ctx = n_ctx
        self._model: object | None = None
        self._pid: int | None = None

    @property
    def model_path(self) -> str | None:
        return self._model_path

    @property
    def process_id(self) -> int | None:
        return self._pid

    def initialize(self) -> None:
        try:
            from llama_cpp import Llama  # type: ignore[import-untyped]
        except ImportError as e:
            raise RuntimeError(
                "llama-cpp-python is not installed. "
                "Install with: pip install llama-cpp-python"
            ) from e

        if not self._model_path or not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Model not found: {self._model_path}")

        kwargs = {
            "model_path": self._model_path,
            "n_ctx": self.n_ctx,
            "verbose": False,
        }
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads

        self._model = Llama(**kwargs)
        self._pid = os.getpid()

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if self._model is None:
            raise RuntimeError("Model not initialized. Call initialize() first.")

        start = time.perf_counter()
        first_token_time = None
        completion_tokens = 0
        response_text = ""

        stream = self._model(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            seed=request.seed,
            stream=True,
        )

        for token_data in stream:
            if first_token_time is None:
                first_token_time = time.perf_counter()
            token_text = token_data.get("choices", [{}])[0].get("text", "")
            response_text += token_text
            completion_tokens += 1

        end = time.perf_counter()
        ttft = (first_token_time - start) if first_token_time else 0.0
        total = end - start
        tps = completion_tokens / total if total > 0 and completion_tokens > 0 else 0.0

        return GenerationResponse(
            text=response_text,
            completion_tokens=completion_tokens,
            total_tokens=completion_tokens,
            ttft_seconds=ttft,
            total_seconds=total,
            tokens_per_second=tps,
        )

    def shutdown(self) -> None:
        self._model = None
        self._pid = None

    def is_available(self) -> bool:
        return find_spec("llama_cpp") is not None


__all__ = ["LlamaCppAdapter"]
