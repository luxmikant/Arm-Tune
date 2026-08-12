"""Report generator — JSON, CSV, Markdown, and evaluation charts."""

from __future__ import annotations

import csv
import json
import time
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
        self._write_charts(run_dir, results, recommendation)

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
                "prompt_tok_s": round(m.prompt_tokens_per_second, 1),
                "p50_latency_s": round(m.p50_latency_seconds, 4),
                "p95_latency_s": round(m.p95_latency_seconds, 4),
                "p99_latency_s": round(m.p99_latency_seconds, 4),
                "latency_stdev_s": round(m.latency_stdev_seconds, 4),
                "queue_delay_s": round(m.queue_delay_mean_seconds, 4),
                "throughput_tok_s": round(m.aggregate_tokens_per_second, 1),
                "avg_tok_s": round(m.tokens_per_second, 1),
                "peak_ram_mb": round(m.peak_memory_mb, 0),
                "peak_rss_mb": round(m.peak_process_rss_mb, 0),
                "avg_cpu_pct": round(m.avg_cpu_percent, 1),
                "quality": round(m.avg_quality_score, 2),
                "successful": m.successful_requests,
                "total_requests": m.total_requests,
                "total_completion_tokens": m.total_completion_tokens,
                "total_prompt_tokens": m.total_prompt_tokens,
                "runtime": r.runtime_info.get("backend", "unknown"),
                "threads": r.runtime_info.get("threads", ""),
                "batch_threads": r.runtime_info.get("batch_threads", ""),
                "concurrency": r.runtime_info.get("concurrency", ""),
                "quantization": r.runtime_info.get("quantization", ""),
            }
            if r.performix_profile and not r.performix_profile.is_empty():
                p = r.performix_profile.counters
                row["performix_status"] = r.performix_profile.status
                row["ipc"] = round(p.instructions_per_cycle, 3)
                row["branch_misp_pct"] = round(p.branch_mispredict_pct, 2)
                row["ll_cache_miss_pct"] = round(p.ll_cache_miss_rate, 2)
                row["mem_read_mbs"] = round(p.memory_read_bandwidth_mbs, 1)
                row["mem_write_mbs"] = round(p.memory_write_bandwidth_mbs, 1)
                row["stall_frontend_pct"] = round(p.stall_frontend_pct, 2)
                row["stall_backend_pct"] = round(p.stall_backend_pct, 2)
            else:
                row["performix_status"] = (
                    r.performix_profile.status if r.performix_profile else "n/a"
                )
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
                f"- NUMA nodes: {hw.get('numa_nodes', '?')}",
            ]
            features = hw.get("features") or []
            if features:
                key = ["sve2", "sve", "i8mm", "bf16", "asimddp", "asimd", "fp"]
                present = [k for k in key if k in features]
                if present:
                    lines.append(f"- Arm features: `{' '.join(present)}`")
            lines.append("")

        lines += ["## Results", ""]
        lines += [
            "| Profile | Quant | Threads | TTFT (s) | P50 (s) | P95 (s) | P99 (s) | tok/s | Prompt tok/s | Peak RSS (MB) | Quality | Runtime |",
            "|---------|-------|---------|----------|---------|---------|---------|-------|--------------|---------------|---------|---------|",
        ]

        for r in results:
            m = r.metrics
            rt = r.runtime_info
            lines.append(
                f"| {r.profile_name} | {rt.get('quantization', '')} | {rt.get('threads', '')} "
                f"| {m.ttft_seconds:.3f} | {m.p50_latency_seconds:.3f} | {m.p95_latency_seconds:.3f} "
                f"| {m.p99_latency_seconds:.3f} | {m.aggregate_tokens_per_second:.1f} "
                f"| {m.prompt_tokens_per_second:.1f} | {m.peak_process_rss_mb:.0f} "
                f"| {m.avg_quality_score:.2f} | {rt.get('backend', '')} |"
            )

        if results and any(
            r.performix_profile and not r.performix_profile.is_empty()
            for r in results
        ):
            lines += [
                "",
                "## Arm Performix Insights",
                "",
                "| Profile | Status | IPC | Branch Misp. % | LLC Miss % | Mem Read MB/s | Mem Write MB/s |",
                "|---------|--------|-----|----------------|------------|---------------|----------------|",
            ]
            for r in results:
                if r.performix_profile:
                    p = r.performix_profile.counters
                    lines.append(
                        f"| {r.profile_name} | {r.performix_profile.status} "
                        f"| {p.instructions_per_cycle:.3f} | {p.branch_mispredict_pct:.1f} "
                        f"| {p.ll_cache_miss_rate:.1f} | {p.memory_read_bandwidth_mbs:.0f} "
                        f"| {p.memory_write_bandwidth_mbs:.0f} |"
                    )
            lines.append("")
            for r in results:
                if r.performix_profile and r.performix_profile.bottlenecks:
                    lines.append(f"### {r.profile_name} bottlenecks")
                    for b in r.performix_profile.bottlenecks:
                        lines.append(
                            f"- **{b.category}** ({b.severity}): "
                            f"{b.description} -> {b.recommendation}"
                        )
                    lines.append("")

        if results and any(r.runtime_info.get("evidence") for r in results):
            lines += ["## Runtime evidence", ""]
            for r in results:
                evidence = r.runtime_info.get("evidence") or {}
                if evidence:
                    lines.append(f"### {r.profile_name}")
                    for key in ("system_info:", "CPU_KLEIDIAI"):
                        if key in evidence:
                            lines.append(f"```\n{evidence[key]}\n```")
                    break
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
            ]
            if recommendation.launch_command:
                lines += [
                    "### Deploy it",
                    "",
                    "```bash",
                    recommendation.launch_command,
                    "```",
                    "",
                ]
            lines += ["### Metrics", ""]
            for k, v in recommendation.metrics_summary.items():
                lines.append(f"- **{k}:** {v}")

        (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_charts(
        self,
        run_dir: Path,
        results: list[BenchmarkResult],
        recommendation: Recommendation | None,
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
            p99 = [r.metrics.p99_latency_seconds for r in results]
            tps = [r.metrics.aggregate_tokens_per_second for r in results]
            ttft = [r.metrics.ttft_seconds for r in results]
            rss = [r.metrics.peak_process_rss_mb for r in results]
            quality = [r.metrics.avg_quality_score for r in results]
            queue = [r.metrics.queue_delay_mean_seconds for r in results]
            x = range(len(names))

            fig, axes = plt.subplots(2, 3, figsize=(16, 10))
            fig.suptitle("ArmTune Serve Benchmark Results", fontsize=14)

            ax = axes[0][0]
            width = 0.25
            ax.bar([i - width for i in x], p50, width, label="P50", color="#2196F3")
            ax.bar(x, p95, width, label="P95", color="#FF9800")
            ax.bar([i + width for i in x], p99, width, label="P99", color="#F44336")
            ax.set_title("Latency percentiles (s)")
            ax.set_xticks(list(x))
            ax.set_xticklabels(names, fontsize=7)
            ax.legend()

            axes[0][1].bar(x, tps, color="#4CAF50")
            axes[0][1].set_title("Aggregate throughput (tok/s)")
            axes[0][1].set_xticks(list(x))
            axes[0][1].set_xticklabels(names, fontsize=7)

            axes[0][2].bar(x, ttft, color="#00BCD4")
            axes[0][2].set_title("Time to first token (s)")
            axes[0][2].set_xticks(list(x))
            axes[0][2].set_xticklabels(names, fontsize=7)

            axes[1][0].bar(x, rss, color="#9C27B0")
            axes[1][0].set_title("Peak process RSS (MB)")
            axes[1][0].set_xticks(list(x))
            axes[1][0].set_xticklabels(names, fontsize=7)

            axes[1][1].scatter(tps, quality, c="#00BCD4", s=60)
            for i, name in enumerate(names):
                axes[1][1].annotate(name, (tps[i], quality[i]), fontsize=6)
            axes[1][1].set_title("Quality vs throughput (Pareto)")
            axes[1][1].set_xlabel("tok/s")
            axes[1][1].set_ylabel("quality")
            axes[1][1].set_ylim(0, 1.1)

            axes[1][2].bar(x, queue, color="#795548")
            axes[1][2].set_title("Mean queue delay (s)")
            axes[1][2].set_xticks(list(x))
            axes[1][2].set_xticklabels(names, fontsize=7)

            plt.tight_layout()
            plt.savefig(run_dir / "charts.png", dpi=150)
            plt.close()

            self._write_sweep_chart(run_dir, results)
            self._write_performix_chart(run_dir, results)
            self._write_improvement_chart(run_dir, results)
        except Exception:
            pass

    def _write_sweep_chart(self, run_dir: Path, results: list[BenchmarkResult]) -> None:
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            thread_results = [r for r in results if r.profile_name.startswith("thread_")]
            concurrency_results = [
                r for r in results if r.profile_name.startswith("concurrency_")
            ]
            if not thread_results and not concurrency_results:
                return

            n_panels = 2 if thread_results and concurrency_results else 1
            fig, axes = plt.subplots(1, n_panels, figsize=(7 * n_panels, 5))
            if n_panels == 1:
                axes = [axes]

            panel = 0
            if thread_results:
                ax = axes[panel]
                panel += 1
                threads = [
                    int(r.profile_name.split("_")[1]) for r in thread_results
                ]
                decode = [r.metrics.tokens_per_second for r in thread_results]
                agg = [r.metrics.aggregate_tokens_per_second for r in thread_results]
                order = sorted(range(len(threads)), key=lambda i: threads[i])
                threads = [threads[i] for i in order]
                decode = [decode[i] for i in order]
                agg = [agg[i] for i in order]
                ax.plot(threads, decode, "o-", label="decode tok/s", color="#2196F3")
                ax.plot(threads, agg, "s--", label="aggregate tok/s", color="#FF9800")
                ax.set_title("Thread sweep")
                ax.set_xlabel("threads")
                ax.set_ylabel("tok/s")
                ax.legend()
                ax.grid(alpha=0.3)

            if concurrency_results:
                ax = axes[panel]
                conc = [int(r.profile_name.split("_")[1]) for r in concurrency_results]
                p95 = [r.metrics.p95_latency_seconds for r in concurrency_results]
                agg = [r.metrics.aggregate_tokens_per_second for r in concurrency_results]
                order = sorted(range(len(conc)), key=lambda i: conc[i])
                conc = [conc[i] for i in order]
                p95 = [p95[i] for i in order]
                agg = [agg[i] for i in order]
                ax.plot(conc, agg, "o-", label="aggregate tok/s", color="#4CAF50")
                ax2 = ax.twinx()
                ax2.plot(conc, p95, "s--", label="P95 latency (s)", color="#F44336")
                ax.set_title("Concurrency sweep")
                ax.set_xlabel("concurrent requests")
                ax.set_ylabel("tok/s")
                ax2.set_ylabel("P95 latency (s)")
                lines = ax.get_lines() + ax2.get_lines()
                ax.legend(lines, [line.get_label() for line in lines], loc="upper left")
                ax.grid(alpha=0.3)

            plt.tight_layout()
            plt.savefig(run_dir / "sweeps.png", dpi=150)
            plt.close()
        except Exception:
            pass

    def _write_performix_chart(self, run_dir: Path, results: list[BenchmarkResult]) -> None:
        profiled = [
            r for r in results
            if r.performix_profile and not r.performix_profile.is_empty()
        ]
        if not profiled:
            return
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            names = [r.profile_name for r in profiled]
            ipc = [r.performix_profile.counters.instructions_per_cycle for r in profiled]
            branch = [r.performix_profile.counters.branch_mispredict_pct for r in profiled]
            ll_miss = [r.performix_profile.counters.ll_cache_miss_rate for r in profiled]
            x = range(len(names))

            fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
            fig.suptitle("Arm Performix hardware counters", fontsize=14)

            axes[0].bar(x, ipc, color="#3F51B5")
            axes[0].set_title("Instructions per cycle (higher is better)")
            axes[0].set_xticks(list(x))
            axes[0].set_xticklabels(names, fontsize=7)

            axes[1].bar(x, branch, color="#FF9800")
            axes[1].set_title("Branch misprediction % (lower is better)")
            axes[1].set_xticks(list(x))
            axes[1].set_xticklabels(names, fontsize=7)

            axes[2].bar(x, ll_miss, color="#F44336")
            axes[2].set_title("LLC miss rate (lower is better)")
            axes[2].set_xticks(list(x))
            axes[2].set_xticklabels(names, fontsize=7)

            plt.tight_layout()
            plt.savefig(run_dir / "performix.png", dpi=150)
            plt.close()
        except Exception:
            pass

    def _write_improvement_chart(self, run_dir: Path, results: list[BenchmarkResult]) -> None:
        if not results:
            return
        baseline = results[0]
        others = results[1:]
        if not others:
            return
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            names = [r.profile_name for r in others]
            base_tps = max(baseline.metrics.aggregate_tokens_per_second, 1e-6)
            base_ttft = max(baseline.metrics.ttft_seconds, 1e-6)
            base_rss = max(baseline.metrics.peak_process_rss_mb, 1e-6)

            tps_delta = [
                (r.metrics.aggregate_tokens_per_second - base_tps) / base_tps * 100
                for r in others
            ]
            ttft_delta = [
                (base_ttft - r.metrics.ttft_seconds) / base_ttft * 100
                for r in others
            ]
            rss_delta = [
                (base_rss - r.metrics.peak_process_rss_mb) / base_rss * 100
                for r in others
            ]

            x = range(len(names))
            width = 0.25
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.axhline(0, color="black", linewidth=0.8)
            ax.bar([i - width for i in x], tps_delta, width, label="tok/s %", color="#4CAF50")
            ax.bar(x, ttft_delta, width, label="TTFT %", color="#00BCD4")
            ax.bar([i + width for i in x], rss_delta, width, label="RSS %", color="#9C27B0")
            ax.set_title(f"Relative improvement vs baseline ({baseline.profile_name})")
            ax.set_ylabel("% change (positive = better)")
            ax.set_xticks(list(x))
            ax.set_xticklabels(names, fontsize=7)
            ax.legend()
            plt.tight_layout()
            plt.savefig(run_dir / "improvements.png", dpi=150)
            plt.close()
        except Exception:
            pass


__all__ = ["ReportGenerator"]
