"""Metrics collection during benchmark runs."""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

import psutil


@dataclass
class BenchmarkMetrics:
    ttft_seconds: float = 0.0
    total_seconds: float = 0.0
    tokens_per_second: float = 0.0
    aggregate_tokens_per_second: float = 0.0
    prompt_tokens_per_second: float = 0.0
    p50_latency_seconds: float = 0.0
    p95_latency_seconds: float = 0.0
    p99_latency_seconds: float = 0.0
    latency_stdev_seconds: float = 0.0
    queue_delay_mean_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    peak_process_rss_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_completion_tokens: int = 0
    total_prompt_tokens: int = 0
    avg_quality_score: float = 1.0


class MetricsCollector:
    def __init__(self, pid: int | None = None) -> None:
        self._lock = Lock()
        self._start_time: float = 0.0
        self._peak_memory: float = 0.0
        self._peak_rss: float = 0.0
        self._cpu_samples: list[float] = []
        self._pid = pid
        self._proc: psutil.Process | None = None
        if pid is not None:
            try:
                self._proc = psutil.Process(pid)
            except Exception:
                self._proc = None

    def start(self) -> None:
        with self._lock:
            self._start_time = time.perf_counter()
            self._peak_memory = 0.0
            self._peak_rss = 0.0
            self._cpu_samples = []

    def sample(self) -> None:
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)
        with self._lock:
            self._cpu_samples.append(cpu)
            mem_mb = mem.used / (1024 * 1024)
            if mem_mb > self._peak_memory:
                self._peak_memory = mem_mb
            if self._proc is not None:
                try:
                    rss_mb = self._proc.memory_info().rss / (1024 * 1024)
                    if rss_mb > self._peak_rss:
                        self._peak_rss = rss_mb
                except Exception:
                    pass

    def stop(self) -> BenchmarkMetrics:
        with self._lock:
            avg_cpu = (
                sum(self._cpu_samples) / len(self._cpu_samples)
                if self._cpu_samples else 0.0
            )
            return BenchmarkMetrics(
                peak_memory_mb=self._peak_memory,
                peak_process_rss_mb=self._peak_rss,
                avg_cpu_percent=avg_cpu,
            )


__all__ = ["BenchmarkMetrics", "MetricsCollector"]
