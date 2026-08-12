"""ArmTune Serve CLI — detect, benchmark, recommend, report."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .analyze.recommender import RecommendationEngine
from .benchmark.metrics import BenchmarkMetrics
from .benchmark.orchestrator import BenchmarkOrchestrator, BenchmarkResult, RunResult
from .config import Objective, load_all_profiles, load_profile
from .detect.detector import detect_hardware
from .performix.installer import is_performix_available
from .prompts.loader import load_prompts
from .report.generator import ReportGenerator
from .runtime.factory import get_runtime_adapter

app = typer.Typer(
    name="armtune",
    help="ArmTune Serve — Arm64 LLM inference optimization powered by Arm Performix.",
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"armtune v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool | None = typer.Option(  # noqa: B008
        None, "--version", callback=version_callback, help="Show version."
    ),
) -> None:
    pass


@app.command()
def detect(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Detect and display hardware information."""
    hw = detect_hardware()

    if json_output:
        console.print(json.dumps(hw.to_dict(), indent=2, default=str))
        return

    table = Table(title=f"Hardware: {hw.hostname}")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Architecture", hw.cpu.architecture)
    table.add_row("CPU Model", hw.cpu.model_name)
    table.add_row("Vendor", hw.cpu.vendor)
    table.add_row("Physical Cores", str(hw.cpu.physical_cores))
    table.add_row("Logical Cores", str(hw.cpu.logical_cores))
    if hw.cpu.frequency_mhz:
        table.add_row("Frequency", f"{hw.cpu.frequency_mhz:.0f} MHz")
    table.add_row("Total RAM", f"{hw.memory.total_gb:.1f} GB")
    table.add_row("Available RAM", f"{hw.memory.available_gb:.1f} GB")
    table.add_row("NUMA Nodes", str(hw.numa.numa_nodes))
    table.add_row("Kernel", hw.kernel)
    table.add_row("OS", hw.os_release)
    table.add_row("ARM64", "Yes" if hw.is_arm64() else "No")

    console.print(table)

    if not hw.is_arm64():
        console.print(
            "\n[bold yellow]Warning:[/] Not running on ARM64. "
            "ArmTune Serve is optimized for ARM64 systems.",
        )


@app.command()
def benchmark(
    profile: str = typer.Option("balanced", "--profile", "-p", help="Profile name or path."),
    prompts_file: str = typer.Option("", "--prompts", help="Path to prompts JSON file."),
    output_dir: str = typer.Option("results", "--output", "-o", help="Results directory."),
) -> None:
    """Run inference benchmarks with Arm Performix profiling."""
    console.print("[bold]ArmTune Benchmark[/]")

    prompt_texts = load_prompts(prompts_file if prompts_file else None)
    console.print(f"Loaded {len(prompt_texts)} prompts")

    profile_path = Path(profile)
    if profile_path.suffix in {".yaml", ".yml", ".json"}:
        p = load_profile(profile)
    else:
        profiles = load_all_profiles()
        if profile not in profiles:
            console.print(f"[red]Profile '{profile}' not found. Available: {list(profiles.keys())}[/]")
            raise typer.Exit(1)
        p = profiles[profile]

    console.print(f"Profile: {p.name} ({p.objective.value})")

    if p.performix.enabled and not is_performix_available():
        console.print("[yellow]Arm Performix not installed. Running without hardware counter profiling.[/]")

    adapter = get_runtime_adapter("mock")
    adapter.initialize()

    orchestrator = BenchmarkOrchestrator(
        runtime=adapter,
        prompts=prompt_texts,
        results_dir=Path(output_dir),
    )

    console.print("Running benchmark...")
    result = orchestrator.run(p)
    results: list[BenchmarkResult] = [result]

    if p.runtime.threads <= 1:
        thread_vals = _suggested_threads()
        console.print(f"Sweeping threads: {thread_vals}")
        sweep = orchestrator.thread_sweep(p, thread_vals)
        for r in sweep:
            results.append(BenchmarkResult(
                profile_name=r.label,
                objective=p.objective.value,
                metrics=r.metrics,
                sweep_results=[r],
            ))

    recommendation = None
    if results:
        engine = RecommendationEngine()
        all_runs: list[RunResult] = []
        for r in results:
            all_runs.extend(r.sweep_results)
        if not all_runs:
            for r in results:
                if r.sweep_results:
                    all_runs.extend(r.sweep_results)
                else:
                    all_runs.append(RunResult(
                        label=r.profile_name,
                        metrics=r.metrics,
                        quality_scores=r.quality_scores,
                    ))

        recommendation = engine.recommend(all_runs, Objective(p.objective))

    generator = ReportGenerator(output_dir)
    report_path = generator.generate(results, recommendation)
    console.print(f"[green]Report saved to {report_path}[/]")

    adapter.shutdown()


@app.command()
def recommend(
    objective: str = typer.Option(
        "balanced", "--objective", "-o",
        help="Optimization objective: low-latency, high-throughput, low-memory, balanced.",
    ),
    results_dir: str = typer.Option("results", "--results", "-r", help="Results directory."),
    latest: bool = typer.Option(False, "--latest", help="Use latest results."),
) -> None:
    """Recommend a deployment configuration."""
    results_path = Path(results_dir)

    if latest:
        subdirs = sorted(
            [d for d in results_path.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if subdirs:
            results_path = subdirs[0]

    json_file = results_path / "results.json"
    if not json_file.exists():
        console.print(f"[red]No results found in {results_path}[/]")
        raise typer.Exit(1)

    data = json.loads(json_file.read_text(encoding="utf-8"))
    console.print(f"[green]Loaded results from {json_file}[/]")

    obj = Objective(objective)
    engine = RecommendationEngine()
    result_list = data.get("results", [])
    if not result_list:
        console.print("[yellow]No benchmark results in file.[/]")
        raise typer.Exit(0)

    runs: list[RunResult] = []
    for r in result_list:
        m = r.get("metrics", {})
        bm = BenchmarkMetrics(
            p50_latency_seconds=m.get("p50_latency_seconds", 0),
            p95_latency_seconds=m.get("p95_latency_seconds", 0),
            tokens_per_second=m.get("tokens_per_second", 0),
            aggregate_tokens_per_second=m.get("aggregate_tokens_per_second", 0),
            peak_memory_mb=m.get("peak_memory_mb", 0),
            avg_quality_score=m.get("avg_quality_score", r.get("avg_quality_score", 1)),
            total_requests=m.get("total_requests", 0),
            successful_requests=m.get("successful_requests", 0),
        )
        runs.append(RunResult(
            label=r.get("profile_name", "unknown"),
            metrics=bm,
            quality_scores=r.get("quality_scores", []),
        ))

    rec = engine.recommend(runs, obj)

    table = Table(title=f"Recommendation — {objective}")
    table.add_column("Rank", style="cyan")
    table.add_column("Config", style="green")
    table.add_column("P50 (s)", style="yellow")
    table.add_column("tok/s", style="yellow")
    table.add_column("RAM (MB)", style="yellow")
    table.add_column("Quality", style="yellow")

    for rank, entry in enumerate(rec.ranked_results, 1):
        marker = " *" if entry["label"] == rec.recommended_label else ""
        table.add_row(
            str(rank),
            entry["label"] + marker,
            str(round(entry["p50_latency_s"], 3)),
            str(round(entry["throughput_tok_s"], 1)),
            str(round(entry["peak_memory_mb"], 0)),
            str(round(entry["quality_score"], 2)),
        )

    console.print(table)
    console.print(f"\n[bold]Recommended:[/] {rec.recommended_label}")
    console.print(rec.reasoning)


@app.command()
def report(
    results_dir: str = typer.Option("results", "--results", "-r", help="Results directory."),
    latest: bool = typer.Option(True, "--latest", help="Use latest results."),
) -> None:
    """Generate a report from benchmark results."""
    results_path = Path(results_dir)

    if latest:
        subdirs = sorted(
            [d for d in results_path.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        if not subdirs:
            console.print("[red]No results found.[/]")
            raise typer.Exit(1)
        results_path = subdirs[0]

    json_file = results_path / "results.json"
    if not json_file.exists():
        console.print(f"[red]No results.json found in {results_path}[/]")
        raise typer.Exit(1)

    data = json.loads(json_file.read_text(encoding="utf-8"))
    console.print(f"[green]Results found: {len(data.get('results', []))} runs[/]")

    report_md = results_path / "report.md"
    if report_md.exists():
        console.print(report_md.read_text(encoding="utf-8"))
    else:
        console.print("[yellow]Report not generated. Run 'armtune benchmark' first.[/]")


def _suggested_threads() -> list[int]:
    import psutil
    logical = psutil.cpu_count(logical=True) or 4
    if logical <= 4:
        return [1, 2, 4]
    return [1, 2, 4, logical // 2, logical]


if __name__ == "__main__":
    app()
