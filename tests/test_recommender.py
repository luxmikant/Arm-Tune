"""Tests for the recommendation engine."""

from armtune.analyze.recommender import RecommendationEngine
from armtune.benchmark.metrics import BenchmarkMetrics
from armtune.benchmark.orchestrator import RunResult
from armtune.config import Objective


def _make_result(label: str, p50: float, tps: float, mem: float, quality: float = 0.8) -> RunResult:
    m = BenchmarkMetrics(
        p50_latency_seconds=p50,
        p95_latency_seconds=p50 * 2,
        tokens_per_second=tps,
        aggregate_tokens_per_second=tps,
        peak_memory_mb=mem,
        avg_quality_score=quality,
        total_requests=10,
        successful_requests=10,
    )
    return RunResult(label=label, metrics=m, quality_scores=[quality] * 10, latencies=[p50] * 10)


def test_low_latency_picks_fastest():
    engine = RecommendationEngine()
    results = [
        _make_result("fast", p50=0.5, tps=50, mem=2000),
        _make_result("slow", p50=2.0, tps=10, mem=1000),
    ]
    rec = engine.recommend(results, Objective.LOW_LATENCY)
    assert rec.recommended_label == "fast"


def test_high_throughput_picks_highest_tps():
    engine = RecommendationEngine()
    results = [
        _make_result("low_tps", p50=0.5, tps=10, mem=2000),
        _make_result("high_tps", p50=1.0, tps=80, mem=3000),
    ]
    rec = engine.recommend(results, Objective.HIGH_THROUGHPUT)
    assert rec.recommended_label == "high_tps"


def test_low_memory_picks_smallest():
    engine = RecommendationEngine()
    results = [
        _make_result("big", p50=0.5, tps=50, mem=5000),
        _make_result("small", p50=1.0, tps=30, mem=1000),
    ]
    rec = engine.recommend(results, Objective.LOW_MEMORY)
    assert rec.recommended_label == "small"


def test_filters_low_quality():
    engine = RecommendationEngine()
    results = [
        _make_result("fast_bad", p50=0.3, tps=100, mem=2000, quality=0.1),
        _make_result("slow_good", p50=1.5, tps=20, mem=1500, quality=0.9),
    ]
    rec = engine.recommend(results, Objective.LOW_LATENCY)
    assert rec.recommended_label == "slow_good"


def test_recommendation_has_reasoning():
    engine = RecommendationEngine()
    results = [_make_result("test", p50=1.0, tps=30, mem=2000)]
    rec = engine.recommend(results, Objective.BALANCED)
    assert len(rec.reasoning) > 0
    assert rec.recommended_label == "test"
