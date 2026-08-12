"""Recommendation engine — selects best config per objective."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..benchmark.orchestrator import RunResult
from ..config import Objective


@dataclass
class Recommendation:
    objective: str
    recommended_label: str
    reasoning: str
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    ranked_results: list[dict[str, Any]] = field(default_factory=list)
    performix_insights: list[str] = field(default_factory=list)
    launch_command: str = ""


class RecommendationEngine:
    QUALITY_THRESHOLD = 0.5

    def recommend(
        self,
        results: list[RunResult],
        objective: Objective,
    ) -> Recommendation:
        valid = [
            r for r in results
            if r.metrics.avg_quality_score >= self.QUALITY_THRESHOLD
        ]
        if not valid:
            valid = results
        if not valid:
            return Recommendation(
                objective=objective.value,
                recommended_label="none",
                reasoning="No benchmark results available.",
            )

        if objective == Objective.LOW_LATENCY:
            sorted_results = sorted(valid, key=lambda r: r.metrics.p50_latency_seconds)
            best = sorted_results[0]
            reasoning = (
                f"'{best.label}' has the lowest P50 latency "
                f"({best.metrics.p50_latency_seconds:.3f}s)."
            )
        elif objective == Objective.HIGH_THROUGHPUT:
            sorted_results = sorted(
                valid, key=lambda r: r.metrics.aggregate_tokens_per_second, reverse=True
            )
            best = sorted_results[0]
            reasoning = (
                f"'{best.label}' achieves the highest throughput "
                f"({best.metrics.aggregate_tokens_per_second:.1f} tok/s)."
            )
        elif objective == Objective.LOW_MEMORY:
            sorted_results = sorted(valid, key=lambda r: r.metrics.peak_memory_mb)
            best = sorted_results[0]
            reasoning = (
                f"'{best.label}' uses the least peak memory "
                f"({best.metrics.peak_memory_mb:.0f} MB)."
            )
        else:  # BALANCED
            scored = [
                (
                    r,
                    self._balanced_score(r),
                )
                for r in valid
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            best = scored[0][0]
            reasoning = (
                f"'{best.label}' provides the best balance of latency, "
                f"throughput, and memory."
            )

        ranked = []
        for r in sorted_results if objective != Objective.BALANCED else [x[0] for x in scored]:
            ranked.append({
                "label": r.label,
                "p50_latency_s": round(r.metrics.p50_latency_seconds, 4),
                "p95_latency_s": round(r.metrics.p95_latency_seconds, 4),
                "throughput_tok_s": round(r.metrics.aggregate_tokens_per_second, 1),
                "peak_memory_mb": round(r.metrics.peak_memory_mb, 0),
                "quality_score": round(r.metrics.avg_quality_score, 2),
            })

        return Recommendation(
            objective=objective.value,
            recommended_label=best.label,
            reasoning=reasoning,
            metrics_summary={
                "p50_latency_s": round(best.metrics.p50_latency_seconds, 4),
                "p95_latency_s": round(best.metrics.p95_latency_seconds, 4),
                "throughput_tok_s": round(best.metrics.aggregate_tokens_per_second, 1),
                "peak_memory_mb": round(best.metrics.peak_memory_mb, 0),
                "quality_score": round(best.metrics.avg_quality_score, 2),
            },
            ranked_results=ranked,
        )

    def _balanced_score(self, result: RunResult) -> float:
        m = result.metrics
        latency_score = 1.0 / (m.p50_latency_seconds + 0.001)
        throughput_score = m.aggregate_tokens_per_second / 10.0
        memory_score = 1.0 / (m.peak_memory_mb / 1000.0 + 0.001)
        quality_score = m.avg_quality_score
        return latency_score * 0.3 + throughput_score * 0.3 + memory_score * 0.2 + quality_score * 0.2


__all__ = ["RecommendationEngine", "Recommendation"]
