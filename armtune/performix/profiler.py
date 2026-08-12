"""Arm Performix profiler — attach to running process, collect hardware counters."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

from .installer import ensure_performix, is_performix_available
from .models import PerformixProfile
from .parser import parse_performix_output


def profile_process(
    pid: int,
    duration_seconds: float = 10.0,
    sample_period_ms: int = 10,
    output_dir: Path | None = None,
) -> PerformixProfile:
    """Run Arm Performix profiling on a process by PID.

    Args:
        pid: Process ID to profile.
        duration_seconds: How long to profile.
        sample_period_ms: Sampling interval in milliseconds.
        output_dir: Directory for Performix output files.

    Returns:
        PerformixProfile with parsed performance counters and bottlenecks.
    """
    if not is_performix_available():
        return PerformixProfile()

    binary = ensure_performix()
    output_dir = output_dir or Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"performix_pid_{pid}_{int(time.time())}.json"

    cmd = [
        str(binary),
        "profile",
        "--pid", str(pid),
        "--duration", str(int(duration_seconds)),
        "--sample-period", str(sample_period_ms),
        "--output", str(output_file),
        "--format", "json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=int(duration_seconds) + 30,
        )

        if output_file.exists():
            raw = output_file.read_text(encoding="utf-8", errors="ignore")
            return parse_performix_output(raw)

        if result.stdout.strip():
            return parse_performix_output(result.stdout)

    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return PerformixProfile()


def attach_profile(
    pid: int,
    duration_seconds: float = 60.0,
    sample_period_ms: int = 10,
    output_dir: Path | None = None,
) -> Iterator[PerformixProfile]:
    """Continuously sample a process with Performix, yielding profiles.

    Use this as a context manager / generator to collect perf data
    over the lifetime of a benchmark run.
    """
    start = time.time()
    while (time.time() - start) < duration_seconds:
        profile = profile_process(
            pid=pid,
            duration_seconds=min(5.0, duration_seconds - (time.time() - start)),
            sample_period_ms=sample_period_ms,
            output_dir=output_dir,
        )
        if not profile.is_empty():
            yield profile
        time.sleep(1.0)


def run_performix_sample(
    pid: int,
    sample_period_ms: int = 10,
    output_dir: Path | None = None,
) -> PerformixProfile:
    """Take a single Performix sample (5-second snapshot)."""
    return profile_process(
        pid=pid,
        duration_seconds=5.0,
        sample_period_ms=sample_period_ms,
        output_dir=output_dir,
    )


__all__ = ["attach_profile", "profile_process", "run_performix_sample"]
