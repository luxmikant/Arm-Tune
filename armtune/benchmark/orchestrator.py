"""Benchmark orchestrator — runs inference with Performix profiling."""

from __future__ import annotations

import os
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import Objective, Profile
from ..detect.detector import detect_hardware
from ..performix.models import PerformixProfile
from ..performix.profiler import run_performix_sample
from ..runtime.base import GenerationRequest, RuntimeAdapter
from .metrics import BenchmarkMetrics, MetricsCollector


@dataclass
class RunResult:
    label: str
    metrics: BenchmarkMetrics
    quality_scores: list[float] = field(default_factory=list)
    latencies: list[float] = field(default_factory=list)
    performix_profile: PerformixProfile | None = None


@dataclass
class BenchmarkResult:
    profile_name: str
    objective: str
    metrics: BenchmarkMetrics
    hardware_info: dict[str, Any] = field(default_factory=dict)
    runtime_info: dict[str, Any] = field(default_factory=dict)
    quality_scores: list[float] = field(default_factory=list)
    avg_quality_score: float = 0.0
    timestamp: float = 0.0
    performix_profile: PerformixProfile | None = None
    sweep_results: list[RunResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "objective": self.objective,
            "metrics": self.metrics.__dict__,
            "hardware_info": self.hardware_info,
            "runtime_info": self.runtime_info,
            "quality_scores": self.quality_scores,
            "avg_quality_score": self.avg_quality_score,
            "timestamp": self.timestamp,
            "performix": (
                self.performix_profile.model_dump()
                if self.performix_profile else None
            ),
        }


class BenchmarkOrchestrator:
    def __init__(
        self,
        runtime: RuntimeAdapter,
        prompts: list[str],
        quality_scorer: Any | None = None,
        results_dir: Path | None = None,
    ) -> None:
        self.runtime = runtime
        self.prompts = prompts
        self.quality_scorer = quality_scorer
        self.results_dir = results_dir or Path("results")

    def run_single(
        self,
        profile: Profile,
        label: str = "",
    ) -> RunResult:
        label = label or profile.label or profile.name
        warmup = profile.benchmark.warmup_requests
        num_req = profile.benchmark.measurement_requests
        max_tokens = profile.benchmark.max_tokens

        requests = [
            GenerationRequest(
                prompt=self.prompts[i % len(self.prompts)],
                max_tokens=max_tokens,
                temperature=profile.benchmark.temperature,
                seed=profile.benchmark.seed + i,
            )
            for i in range(num_req)
        ]

        for _ in range(warmup):
            self.runtime.generate(requests[0])

        collector = MetricsCollector()
        collector.start()

        latencies: list[float] = []
        completion_tokens_list: list[int] = []
        ttfts: list[float] = []
        quality_scores: list[float] = []

        concurrency = profile.runtime.concurrency
        if concurrency <= 1:
            for req in requests:
                start = time.perf_counter()
                response = self.runtime.generate(req)
                latencies.append(time.perf_counter() - start)
                ttfts.append(response.ttft_seconds)
                completion_tokens_list.append(response.completion_tokens)
                if self.quality_scorer:
                    score = self.quality_scorer.score(response.text, req.prompt)
                    quality_scores.append(score)
                collector.sample()
        else:
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = {
                    executor.submit(self.runtime.generate, req): req
                    for req in requests
                }
                for future in as_completed(futures):
                    start = time.perf_counter()
                    try:
                        response = future.result()
                        latencies.append(time.perf_counter() - start)
                        ttfts.append(response.ttft_seconds)
                        completion_tokens_list.append(response.completion_tokens)
                        if self.quality_scorer:
                            score = self.quality_scorer.score(response.text, "")
                            quality_scores.append(score)
                    except Exception:
                        pass
                    collector.sample()

        system_metrics = collector.stop()
        total_tokens = sum(completion_tokens_list)
        total_time = sum(latencies) if latencies else 0.0
        avg_tps = (
            statistics.mean([
                tokens / lat
                for tokens, lat in zip(completion_tokens_list, latencies)
                if lat > 0 and tokens > 0
            ])
            if completion_tokens_list else 0.0
        )
        aggregate_tps = total_tokens / total_time if total_time > 0 else 0.0

        metrics = BenchmarkMetrics(
            ttft_seconds=statistics.mean(ttfts) if ttfts else 0.0,
            total_seconds=total_time,
            tokens_per_second=avg_tps,
            aggregate_tokens_per_second=aggregate_tps,
            p50_latency_seconds=_percentile(latencies, 50),
            p95_latency_seconds=_percentile(latencies, 95),
            peak_memory_mb=system_metrics.peak_memory_mb,
            avg_cpu_percent=system_metrics.avg_cpu_percent,
            total_requests=len(requests),
            successful_requests=len(latencies),
            failed_requests=len(requests) - len(latencies),
            total_completion_tokens=total_tokens,
            avg_quality_score=(
                statistics.mean(quality_scores) if quality_scores else 1.0
            ),
        )

        return RunResult(
            label=label,
            metrics=metrics,
            quality_scores=quality_scores,
            latencies=latencies,
        )

    def run(self, profile: Profile) -> BenchmarkResult:
        if profile.performix.enabled:
            pid = self.runtime.process_id or os.getpid()
            performix = run_performix_sample(
                pid=pid,
                sample_period_ms=profile.performix.sample_period_ms,
                output_dir=self.results_dir,
            )
        else:
            performix = None

        result = self.run_single(profile)

        hw = detect_hardware()

        return BenchmarkResult(
            profile_name=profile.name,
            objective=profile.objective.value,
            metrics=result.metrics,
            hardware_info={
                "architecture": hw.cpu.architecture,
                "cpu_model": hw.cpu.model_name,
                "physical_cores": hw.cpu.physical_cores,
                "logical_cores": hw.cpu.logical_cores,
                "memory_gb": hw.memory.total_gb,
            },
            runtime_info={
                "threads": profile.runtime.threads,
                "concurrency": profile.runtime.concurrency,
                "quantization": profile.model.quantization.value,
                "model": profile.model.name,
                "context_size": profile.model.context_size,
            },
            quality_scores=result.quality_scores,
            avg_quality_score=result.metrics.avg_quality_score,
            timestamp=time.time(),
            performix_profile=performix,
            sweep_results=[result],
        )

    def sweep(self, profiles: list[Profile], label_prefix: str = "") -> list[RunResult]:
        results: list[RunResult] = []
        for profile in profiles:
            r = self.run_single(profile, label=f"{label_prefix}{profile.name}")
            results.append(r)
        return results

    def thread_sweep(
        self, profile: Profile, thread_values: list[int]
    ) -> list[RunResult]:
        results: list[RunResult] = []
        base_threads = profile.runtime.threads
        for n in thread_values:
            profile.runtime.threads = n
            r = self.run_single(profile, label=f"thread_{n}")
            results.append(r)
        profile.runtime.threads = base_threads
        return results

    def concurrency_sweep(
        self, profile: Profile, concurrency_values: list[int]
    ) -> list[RunResult]:
        results: list[RunResult] = []
        base_concurrency = profile.runtime.concurrency
        for c in concurrency_values:
            profile.runtime.concurrency = c
            r = self.run_single(profile, label=f"concurrency_{c}")
            results.append(r)
        profile.runtime.concurrency = base_concurrency
        return results


def _percentile(data: list[float], percentile: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_data) - 1)
    if f == c:
        return sorted_data[f]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


__all__ = ["BenchmarkOrchestrator", "BenchmarkResult", "RunResult"]
