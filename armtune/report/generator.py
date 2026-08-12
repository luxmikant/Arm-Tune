"""Report generator — produces JSON, CSV, Markdown, and chart files."""

from __future__ import annotations

import csv
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..analyze.recommender import Recommendation
from ..benchmark.orchestrator import BenchmarkResult


class ReportGenerator:
    def __init__(self, output_dir: Path | str = "results") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        results: list[BenchmarkResult],
        recommendation: Recommendation | None = None,
        label: str = "",
    ) -> Path:
        ts = label or time.strftime("%Y%m%d_%H%M%S")
        run_dir = self.output_dir / ts
        run_dir.mkdir(parents=True, exist_ok=True)

        self._write_json(run_dir, results, recommendation)
        self._write_csv(run_dir, results)
        self._write_markdown(run_dir, results, recommendation)
        self._write_charts(run_dir, results)

        return run_dir

    def _write_json(
        self,
        run_dir: Path,
        results: list[BenchmarkResult],
        recommendation: Recommendation | None,
    ) -> None:
        data = {
            "timestamp": time.time(),
            "results": [r.to_dict() for r in results],
            "recommendation": recommendation.__dict__ if recommendation else None,
        }
        (run_dir / "results.json").write_text(
            json.dumps(data, indent=2, default=str),
            encoding="utf-8",
        )

    def _write_csv(self, run_dir: Path, results: list[BenchmarkResult]) -> None:
        rows: list[dict[str, Any]] = []
        for r in results:
            m = r.metrics
            row = {
                "profile": r.profile_name,
                "objective": r.objective,
                "ttft_s": round(m.ttft_seconds, 4),
                "p50_latency_s": round(m.p50_latency_seconds, 4),
                "p95_latency_s": round(m.p95_latency_seconds, 4),
                "throughput_tok_s": round(m.aggregate_tokens_per_second, 1),
                "avg_tok_s": round(m.tokens_per_second, 1),
                "peak_ram_mb": round(m.peak_memory_mb, 0),
                "avg_cpu_pct": round(m.avg_cpu_percent, 1),
                "quality": round(m.avg_quality_score, 2),
                "successful": m.successful_requests,
                "total_requests": m.total_requests,
                "total_completion_tokens": m.total_completion_tokens,
            }
            for i, qs in enumerate(r.quality_scores):
                row[f"quality_req_{i}"] = round(qs, 2)
            if r.performix_profile and not r.performix_profile.is_empty():
                p = r.performix_profile.counters
                row["ipc"] = round(p.instructions_per_cycle, 3)
                row["branch_misp_pct"] = round(p.branch_mispredict_pct, 2)
                row["ll_cache_miss_pct"] = round(p.ll_cache_miss_rate, 2)
                row["mem_read_mbs"] = round(p.memory_read_bandwidth_mbs, 1)
                row["mem_write_mbs"] = round(p.memory_write_bandwidth_mbs, 1)
            rows.append(row)

        if rows:
            with open(run_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def _write_markdown(
        self,
        run_dir: Path,
        results: list[BenchmarkResult],
        recommendation: Recommendation | None,
    ) -> None:
        lines = [
            "# ArmTune Serve Benchmark Report",
            "",
            f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
            "",
        ]

        if results:
            hw = results[0].hardware_info
            lines += [
                "## Hardware",
                "",
                f"- Architecture: `{hw.get('architecture', 'unknown')}`",
                f"- CPU: {hw.get('cpu_model', 'unknown')}",
                f"- Cores: {hw.get('physical_cores', '?')}P / {hw.get('logical_cores', '?')}L",
                f"- Memory: {hw.get('memory_gb', '?')} GB",
                "",
            ]

        lines += ["## Results", ""]
        lines += [
            "| Profile | TTFT (s) | P50 (s) | P95 (s) | tok/s | Peak RAM (MB) | Quality |",
            "|---------|----------|---------|---------|-------|---------------|---------|",
        ]

        for r in results:
            m = r.metrics
            lines.append(
                f"| {r.profile_name} | {m.ttft_seconds:.3f} | {m.p50_latency_seconds:.3f} "
                f"| {m.p95_latency_seconds:.3f} | {m.aggregate_tokens_per_second:.1f} "
                f"| {m.peak_memory_mb:.0f} | {m.avg_quality_score:.2f} |"
            )

        if results and any(
            r.performix_profile and not r.performix_profile.is_empty()
            for r in results
        ):
            lines += [
                "",
                "## Arm Performix Insights",
                "",
                "| Profile | IPC | Branch Misp. % | LLC Miss % | Mem Read MB/s | Mem Write MB/s |",
                "|---------|-----|----------------|------------|---------------|----------------|",
            ]
            for r in results:
                if r.performix_profile and not r.performix_profile.is_empty():
                    p = r.performix_profile.counters
                    lines.append(
                        f"| {r.profile_name} | {p.instructions_per_cycle:.3f} "
                        f"| {p.branch_mispredict_pct:.1f} | {p.ll_cache_miss_rate:.1f} "
                        f"| {p.memory_read_bandwidth_mbs:.0f} | {p.memory_write_bandwidth_mbs:.0f} |"
                    )

            lines += [""]
            for r in results:
                if (
                    r.performix_profile
                    and r.performix_profile.bottlenecks
                ):
                    lines.append(f"### {r.profile_name} bottlenecks")
                    for b in r.performix_profile.bottlenecks:
                        lines.append(
                            f"- **{b.category}** ({b.severity}): "
                            f"{b.description} → {b.recommendation}"
                        )
                    lines.append("")

        if recommendation:
            lines += [
                "## Recommendation",
                "",
                f"**Objective:** {recommendation.objective}",
                f"**Recommended:** `{recommendation.recommended_label}`",
                "",
                recommendation.reasoning,
                "",
                "### Metrics",
                "",
            ]
            for k, v in recommendation.metrics_summary.items():
                lines.append(f"- **{k}:** {v}")

        (run_dir / "report.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )

    def _write_charts(
        self,
        run_dir: Path,
        results: list[BenchmarkResult],
    ) -> None:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            if not results:
                return

            names = [r.profile_name for r in results]
            p50 = [r.metrics.p50_latency_seconds for r in results]
            p95 = [r.metrics.p95_latency_seconds for r in results]
            tps = [r.metrics.aggregate_tokens_per_second for r in results]
            mem = [r.metrics.peak_memory_mb for r in results]
            quality = [r.metrics.avg_quality_score for r in results]

            x = range(len(names))

            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle("ArmTune Serve Benchmark Results", fontsize=14)

            ax = axes[0][0]
            ax.bar(x, p50, width=0.35, label="P50", color="#2196F3")
            ax.bar([i + 0.35 for i in x], p95, width=0.35, label="P95", color="#FF9800")
            ax.set_title("Latency (seconds)")
            ax.set_xticks([i + 0.175 for i in x])
            ax.set_xticklabels(names, fontsize=8)
            ax.legend()

            axes[0][1].bar(x, tps, color="#4CAF50")
            axes[0][1].set_title("Throughput (tokens/sec)")
            axes[0][1].set_xticks(x)
            axes[0][1].set_xticklabels(names, fontsize=8)

            axes[1][0].bar(x, mem, color="#9C27B0")
            axes[1][0].set_title("Peak RAM (MB)")
            axes[1][0].set_xticks(x)
            axes[1][0].set_xticklabels(names, fontsize=8)

            axes[1][1].bar(x, quality, color="#00BCD4")
            axes[1][1].set_title("Quality Score")
            axes[1][1].set_xticks(x)
            axes[1][1].set_xticklabels(names, fontsize=8)
            axes[1][1].set_ylim(0, 1.1)

            plt.tight_layout()
            plt.savefig(run_dir / "charts.png", dpi=150)
            plt.close()
        except Exception:
            pass


__all__ = ["ReportGenerator"]
