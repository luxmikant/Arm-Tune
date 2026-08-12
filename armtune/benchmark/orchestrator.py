"""Benchmark orchestrator — runs real inference with Performix profiling."""

from __future__ import annotations

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..config import Profile
from ..detect.detector import detect_hardware
from ..performix.models import PerformixProfile
from ..performix.profiler import PerformixCapture
from ..runtime.base import GenerationRequest, GenerationResponse
from ..runtime.factory import AdapterFactory, build_adapter_factory
from .metrics import BenchmarkMetrics, MetricsCollector


@dataclass
class RunResult:
    label: str
    metrics: BenchmarkMetrics
    quality_scores: list[float] = field(default_factory=list)
    latencies: list[float] = field(default_factory=list)
    queue_delays: list[float] = field(default_factory=list)
    ttfts: list[float] = field(default_factory=list)
    prompt_tps_values: list[float] = field(default_factory=list)
    performix_profile: PerformixProfile | None = None
    runtime_evidence: dict = field(default_factory=dict)


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
        prompts: list[str],
        quality_scorer: Any | None = None,
        results_dir: Path | None = None,
        adapter_factory: AdapterFactory | None = None,
    ) -> None:
        self.prompts = prompts
        self.quality_scorer = quality_scorer
        self.results_dir = results_dir or Path("results")
        self._factory: AdapterFactory = adapter_factory or build_adapter_factory()

    def run_single(
        self,
        profile: Profile,
        label: str = "",
        capture: PerformixCapture | None = None,
    ) -> RunResult:
        label = label or profile.label or profile.name
        warmup = profile.benchmark.warmup_requests
        num_req = profile.benchmark.measurement_requests
        max_tokens = profile.benchmark.max_tokens
        repetitions = profile.benchmark.repetitions

        requests = [
            GenerationRequest(
                prompt=self.prompts[i % len(self.prompts)],
                max_tokens=max_tokens,
                temperature=profile.benchmark.temperature,
                seed=profile.benchmark.seed + i,
            )
            for i in range(num_req)
        ]

        adapter = self._factory(profile)
        adapter.initialize()

        try:
            if capture is not None:
                capture.pid = adapter.process_id or _self_pid()
                capture.start()

            for _ in range(warmup):
                adapter.generate(requests[0])

            latencies: list[float] = []
            queue_delays: list[float] = []
            ttfts: list[float] = []
            prompt_tps_values: list[float] = []
            completion_tokens_list: list[int] = []
            prompt_tokens_list: list[int] = []
            quality_scores: list[float] = []
            response_texts: list[tuple[str, str]] = []

            collector = MetricsCollector(pid=adapter.process_id)
            collector.start()

            wall_start = time.perf_counter()

            for _ in range(repetitions):
                if profile.runtime.concurrency <= 1:
                    for req in requests:
                        start = time.perf_counter()
                        response = adapter.generate(req)
                        wall = time.perf_counter() - start
                        latencies.append(wall)
                        queue_delays.append(max(0.0, wall - response.total_seconds))
                        self._record(
                            response, req, ttfts, prompt_tps_values,
                            completion_tokens_list, prompt_tokens_list,
                            quality_scores, response_texts,
                        )
                        collector.sample()
                else:
                    with ThreadPoolExecutor(
                        max_workers=profile.runtime.concurrency
                    ) as executor:
                        futures = {}
                        for req in requests:
                            submit_time = time.perf_counter()
                            futures[executor.submit(adapter.generate, req)] = (
                                submit_time,
                                req,
                            )
                        for future in as_completed(futures):
                            submit_time, req = futures[future]
                            done = time.perf_counter()
                            try:
                                response = future.result()
                            except Exception:
                                continue
                            wall = done - submit_time
                            latencies.append(wall)
                            queue_delays.append(
                                max(0.0, wall - response.total_seconds)
                            )
                            self._record(
                                response, req, ttfts, prompt_tps_values,
                                completion_tokens_list, prompt_tokens_list,
                                quality_scores, response_texts,
                            )
                            collector.sample()

            wall_total = time.perf_counter() - wall_start

            system_metrics = collector.stop()

            total_tokens = sum(completion_tokens_list)
            decode_tps_values = [
                tokens / (resp_latency)
                for tokens, resp_latency in zip(
                    completion_tokens_list, latencies, strict=False
                )
                if resp_latency > 0 and tokens > 0
            ]
            avg_tps = (
                statistics.mean(decode_tps_values) if decode_tps_values else 0.0
            )
            aggregate_tps = total_tokens / wall_total if wall_total > 0 else 0.0
            prompt_tps = (
                statistics.mean(prompt_tps_values)
                if prompt_tps_values else 0.0
            )

            metrics = BenchmarkMetrics(
                ttft_seconds=statistics.mean(ttfts) if ttfts else 0.0,
                total_seconds=wall_total,
                tokens_per_second=avg_tps,
                aggregate_tokens_per_second=aggregate_tps,
                prompt_tokens_per_second=prompt_tps,
                p50_latency_seconds=_percentile(latencies, 50),
                p95_latency_seconds=_percentile(latencies, 95),
                p99_latency_seconds=_percentile(latencies, 99),
                latency_stdev_seconds=(
                    statistics.stdev(latencies) if len(latencies) > 1 else 0.0
                ),
                queue_delay_mean_seconds=(
                    statistics.mean(queue_delays) if queue_delays else 0.0
                ),
                peak_memory_mb=system_metrics.peak_memory_mb,
                peak_process_rss_mb=system_metrics.peak_process_rss_mb,
                avg_cpu_percent=system_metrics.avg_cpu_percent,
                total_requests=len(requests) * repetitions,
                successful_requests=len(latencies),
                failed_requests=len(requests) * repetitions - len(latencies),
                total_completion_tokens=total_tokens,
                total_prompt_tokens=sum(prompt_tokens_list),
                avg_quality_score=(
                    statistics.mean(quality_scores) if quality_scores else 1.0
                ),
            )

            evidence = dict(getattr(adapter, "evidence", {}) or {})
            evidence["backend"] = adapter.__class__.__name__

            if capture is not None:
                capture.stop()

            return RunResult(
                label=label,
                metrics=metrics,
                quality_scores=quality_scores,
                latencies=latencies,
                queue_delays=queue_delays,
                ttfts=ttfts,
                prompt_tps_values=prompt_tps_values,
                runtime_evidence=evidence,
            )
        finally:
            adapter.shutdown()

    def _record(
        self,
        response: GenerationResponse,
        request: GenerationRequest,
        ttfts: list[float],
        prompt_tps_values: list[float],
        completion_tokens_list: list[int],
        prompt_tokens_list: list[int],
        quality_scores: list[float],
        response_texts: list[tuple[str, str]],
    ) -> None:
        ttfts.append(response.ttft_seconds)
        if response.prompt_tokens_per_second > 0:
            prompt_tps_values.append(response.prompt_tokens_per_second)
        completion_tokens_list.append(response.completion_tokens)
        prompt_tokens_list.append(response.prompt_tokens)
        response_texts.append((response.text, request.prompt))
        if self.quality_scorer:
            score = self.quality_scorer.score(response.text, request.prompt)
            quality_scores.append(score)

    def run(self, profile: Profile) -> BenchmarkResult:
        hw = detect_hardware()

        capture: PerformixCapture | None = None
        if profile.performix.enabled:
            capture = PerformixCapture(
                pid=0,
                output_dir=self.results_dir,
                seconds=10,
            )

        result = self.run_single(profile, capture=capture)
        performix = (
            capture.profile if capture is not None
            else PerformixProfile(status="disabled")
        )

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
                "features": hw.cpu.features,
                "numa_nodes": hw.numa.numa_nodes,
            },
            runtime_info={
                "threads": profile.runtime.threads,
                "batch_threads": profile.runtime.batch_threads,
                "concurrency": profile.runtime.concurrency,
                "quantization": profile.model.quantization.value,
                "model": profile.model.name,
                "repo_id": profile.model.repo_id,
                "context_size": profile.model.context_size,
                "backend": result.runtime_evidence.get("backend", "unknown"),
                "evidence": result.runtime_evidence,
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


def _self_pid() -> int:
    import os

    return os.getpid()


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
