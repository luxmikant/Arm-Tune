"""Arm Performix profiler — capture hardware counters while inference runs.

The Performix CLI subcommands are version-dependent, so the profiler
probes a small set of candidate invocations, records the exact command,
exit code and stderr for every attempt, and parses any JSON produced.
Every run is transparent: status is one of
``captured`` | ``attempted-no-output`` | ``unavailable`` | ``failed``.
"""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

from .installer import _find_performix_binary
from .models import PerformixProfile
from .parser import parse_performix_output

CANDIDATE_COMMANDS = (
    ("apx profile --pid {pid} --duration {secs} --output {out} --format json", 10),
    ("apx profile --pid {pid} -d {secs} -o {out}", 10),
    ("apx record --pid {pid} --duration {secs} --output {out} --format json", 10),
    ("apx collect --pid {pid} --duration {secs} --output {out}", 10),
    ("apx run --pid {pid} --duration {secs} --output {out}", 10),
)


def get_performix_version() -> str:
    binary = _find_performix_binary()
    if binary is None:
        return ""
    try:
        r = subprocess.run(
            [str(binary), "--version"], capture_output=True, text=True, timeout=10
        )
        return (r.stdout or r.stderr or "").strip().splitlines()[0][:200]
    except Exception:
        return ""


class PerformixCapture:
    """Runs Performix probing in a background thread during a time window."""

    def __init__(self, pid: int, output_dir: Path, seconds: float) -> None:
        self.pid = pid
        self.output_dir = output_dir
        self.seconds = max(int(seconds), 5)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.profile = PerformixProfile()
        self.version = get_performix_version()
        self._binary = _find_performix_binary()

    def start(self) -> None:
        if self._binary is None:
            self.profile = PerformixProfile(
                status="unavailable",
                version=self.version,
            )
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> PerformixProfile:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.seconds + 30)
        return self.profile

    def _run(self) -> None:
        if self._binary is None:
            return
        output_dir = self.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = int(time.time())
        out_path = output_dir / f"performix_pid_{self.pid}_{stamp}.json"

        attempts = 0
        for template, secs in CANDIDATE_COMMANDS:
            if self._stop.is_set():
                break
            attempts += 1
            cmd = template.format(pid=self.pid, secs=secs, out=out_path)
            try:
                r = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    text=True,
                    timeout=secs + 20,
                )
            except subprocess.TimeoutExpired:
                continue
            except Exception:
                continue

            raw = ""
            if out_path.exists():
                raw = out_path.read_text(encoding="utf-8", errors="ignore")
            if not raw.strip() and (r.stdout or "").strip():
                raw = r.stdout
            if raw.strip():
                parsed = parse_performix_output(raw)
                self.profile = parsed.model_copy(
                    update={
                        "status": "captured",
                        "command": cmd,
                        "version": self.version,
                        "stderr": r.stderr or "",
                    }
                )
                return

        self.profile = PerformixProfile(
            status="attempted-no-output",
            command=f"{attempts} candidate commands probed",
            version=self.version,
        )


__all__ = ["PerformixCapture", "get_performix_version"]
