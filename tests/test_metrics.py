"""Tests for BenchmarkMetrics."""

from armtune.benchmark.metrics import BenchmarkMetrics


def test_metrics_defaults():
    m = BenchmarkMetrics()
    assert m.ttft_seconds == 0.0
    assert m.tokens_per_second == 0.0
    assert m.total_requests == 0


def test_metrics_with_values():
    m = BenchmarkMetrics(
        ttft_seconds=0.5,
        total_seconds=2.0,
        tokens_per_second=50.0,
        aggregate_tokens_per_second=45.0,
        p50_latency_seconds=1.0,
        p95_latency_seconds=2.5,
        peak_memory_mb=1024.0,
        avg_cpu_percent=75.0,
        total_requests=10,
        successful_requests=10,
        total_completion_tokens=100,
    )
    assert m.ttft_seconds == 0.5
    assert m.p95_latency_seconds == 2.5
    assert m.peak_memory_mb == 1024.0
