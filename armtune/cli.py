"""ArmTune Serve CLI — detect, benchmark, recommend, report, dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .analyze.recommender import Recommendation, RecommendationEngine
from .analyze.scorer import QualityScorer
from .benchmark.metrics import BenchmarkMetrics
from .benchmark.orchestrator import BenchmarkOrchestrator, BenchmarkResult, RunResult
from .config import Objective, QuantizationFormat, load_all_profiles, load_profile
from .detect.detector import detect_hardware
from .models.hub import list_gguf_models, resolve_model
from .performix.installer import is_performix_available
from .prompts.loader import load_prompts
from .report.generator import ReportGenerator
from .runtime.factory import build_adapter_factory

app = typer.Typer(
    name="armtune",
    help="ArmTune Serve — Arm64 LLM inference optimization powered by Arm Performix.",
)
models_app = typer.Typer(help="Manage models from Hugging Face.")
app.add_typer(models_app, name="models")

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


@models_app.command("list")
def models_list(
    repo: str = typer.Argument(..., help="Hugging Face repo, e.g. unsloth/Llama-3.2-1B-Instruct-GGUF"),
) -> None:
    """List GGUF quantizations available in a Hugging Face repo."""
    try:
        items = list_gguf_models(repo)
    except Exception as e:
        console.print(f"[red]Failed to list {repo}: {e}[/]")
        raise typer.Exit(1) from e

    if not items:
        console.print(f"[yellow]No GGUF files found in {repo}[/]")
        raise typer.Exit(0)

    table = Table(title=f"GGUF models in {repo}")
    table.add_column("Quantization", style="cyan")
    table.add_column("Filename", style="green")
    for item in items:
        table.add_row(item["quantization"], item["filename"])
    console.print(table)


@models_app.command("pull")
def models_pull(
    repo: str = typer.Argument(..., help="Hugging Face repo"),
    quant: str = typer.Option("", "--quant", "-q", help="Quantization tag, e.g. Q4_K_M"),
    output: str = typer.Option("models", "--output", "-o", help="Cache directory."),
) -> None:
    """Download a GGUF model from Hugging Face."""
    path, actual_quant = resolve_model(repo, quant or None, cache_dir=output)
    console.print(f"[green]Downloaded {repo} ({actual_quant}) -> {path}[/]")


@app.command()
def benchmark(
    profile: str = typer.Option("balanced", "--profile", "-p", help="Profile name or path."),
    model_path: str = typer.Option("", "--model-path", help="Local GGUF path."),
    repo: str = typer.Option("", "--repo", help="Hugging Face repo to pull from."),
    quant: str = typer.Option(
        "", "--quant",
        help="Comma-separated quantizations, e.g. Q4_K_M,Q8_0 (requires --repo).",
    ),
    prompts_file: str = typer.Option("", "--prompts", help="Path to prompts JSON file."),
    output_dir: str = typer.Option("results", "--output", "-o", help="Results directory."),
    threads: str = typer.Option("", "--threads", help="Comma-separated thread sweep, e.g. 1,2,4"),
    concurrency: str = typer.Option("", "--concurrency", help="Comma-separated concurrency sweep."),
    runtime_backend: str = typer.Option(
        "auto", "--runtime",
        help="Runtime backend: auto, llama-server, llama-lib, mock.",
    ),
) -> None:
    """Run inference benchmarks with Arm Performix profiling."""
    console.print("[bold]ArmTune Benchmark[/]")

    prompt_texts = load_prompts(prompts_file if prompts_file else None)
    console.print(f"Loaded {len(prompt_texts)} prompts")

    profile_path = Path(profile)
    if profile_path.suffix in {".yaml", ".yml", ".json"}:
        base_profile = load_profile(profile)
    else:
        profiles = load_all_profiles()
        if profile not in profiles:
            console.print(
                f"[red]Profile '{profile}' not found. Available: {list(profiles.keys())}[/]"
            )
            raise typer.Exit(1)
        base_profile = profiles[profile]

    console.print(f"Profile: {base_profile.name} ({base_profile.objective.value})")
    if base_profile.performix.enabled and not is_performix_available():
        console.print(
            "[yellow]Arm Performix not installed. "
            "Proceeding without hardware counter profiling.[/]"
        )

    factory = build_adapter_factory(
        base_profile.runtime.runtime_backend
        if base_profile.runtime.runtime_backend != "auto"
        else runtime_backend
    )

    variants: list[tuple[str, str, str]] = []
    if model_path:
        variants.append((base_profile.name, model_path, base_profile.model.quantization.value))
    elif repo:
        quants = [q.strip().upper() for q in quant.split(",") if q.strip()]
        if quants:
            for q in quants:
                path, actual = resolve_model(repo, q, cache_dir="models")
                variants.append((f"{base_profile.name}_{actual}", str(path), actual))
        else:
            path, actual = resolve_model(repo, None, cache_dir="models")
            variants.append((f"{base_profile.name}_{actual}", str(path), actual))
    else:
        discovered = _discover_model()
        if discovered:
            variants.append(
                (base_profile.name, discovered, base_profile.model.quantization.value)
            )
        else:
            console.print(
                "[yellow]No model found: pass --model-path or --repo "
                "(falling back to mock adapter).[/]"
            )
            variants.append((base_profile.name, "", base_profile.model.quantization.value))

    orchestrator = BenchmarkOrchestrator(
        prompts=prompt_texts,
        quality_scorer=QualityScorer(),
        results_dir=Path(output_dir),
        adapter_factory=factory,
    )

    results: list[BenchmarkResult] = []
    all_runs: list[RunResult] = []

    for label, path, quant_tag in variants:
        p = base_profile.model_copy(deep=True)
        p.label = label
        p.model.model_path = path or None
        try:
            p.model.quantization = QuantizationFormat(quant_tag)
        except ValueError:
            console.print(f"[yellow]Unknown quantization tag {quant_tag}; keeping default.[/]")

        console.print(f"\n[bold cyan]Benchmarking {label}[/] "
                      f"(model={path or 'mock'}, quant={quant_tag}, "
                      f"threads={p.runtime.threads})")
        result = orchestrator.run(p)
        results.append(result)
        all_runs.extend(result.sweep_results)

        thread_values = _parse_int_list(threads)
        if thread_values:
            console.print(f"Sweeping threads: {thread_values}")
            sweep = orchestrator.thread_sweep(p, thread_values)
            for r in sweep:
                results.append(
                    BenchmarkResult(
                        profile_name=r.label,
                        objective=p.objective.value,
                        metrics=r.metrics,
                        sweep_results=[r],
                    )
                )
                all_runs.append(r)

        concurrency_values = _parse_int_list(concurrency)
        if concurrency_values:
            console.print(f"Sweeping concurrency: {concurrency_values}")
            sweep = orchestrator.concurrency_sweep(p, concurrency_values)
            for r in sweep:
                results.append(
                    BenchmarkResult(
                        profile_name=r.label,
                        objective=p.objective.value,
                        metrics=r.metrics,
                        sweep_results=[r],
                    )
                )
                all_runs.append(r)

    recommendation: Recommendation | None = None
    if all_runs:
        engine = RecommendationEngine()
        recommendation = engine.recommend(all_runs, Objective(base_profile.objective))
        recommendation.launch_command = _build_launch_command(
            recommendation, base_profile, variants
        )

    generator = ReportGenerator(output_dir)
    report_path = generator.generate(results, recommendation)
    console.print(f"[green]Report saved to {report_path}[/]")

    if recommendation:
        console.print(
            f"\n[bold]Recommended:[/] {recommendation.recommended_label}\n"
            f"{recommendation.reasoning}\n"
            f"[bold]Launch:[/] {recommendation.launch_command}"
        )


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
            p99_latency_seconds=m.get("p99_latency_seconds", 0),
            tokens_per_second=m.get("tokens_per_second", 0),
            aggregate_tokens_per_second=m.get("aggregate_tokens_per_second", 0),
            peak_memory_mb=m.get("peak_memory_mb", 0),
            peak_process_rss_mb=m.get("peak_process_rss_mb", 0),
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


@app.command()
def dashboard(
    results_dir: str = typer.Option("results", "--results", "-r", help="Results directory."),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host."),
    port: int = typer.Option(7860, "--port", help="Bind port."),
) -> None:
    """Launch the Gradio analysis dashboard."""
    try:
        import gradio  # noqa: F401
    except ImportError as e:
        console.print(
            "[red]Gradio is not installed. Run: pip install 'armtune-serve[dashboard]'[/]"
        )
        raise typer.Exit(1) from e

    from .dashboard.app import build_dashboard

    demo = build_dashboard(results_dir)
    console.print(f"[green]Dashboard: http://{host}:{port}[/]")
    demo.launch(
        server_name=host,
        server_port=port,
        theme=getattr(demo, "armtune_theme", None),
    )


def _discover_model() -> str | None:
    models_dir = Path("models")
    if models_dir.is_dir():
        ggufs = sorted(models_dir.rglob("*.gguf"))
        if ggufs:
            return str(ggufs[-1])
    return None


def _parse_int_list(raw: str) -> list[int]:
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            values.append(int(part))
        except ValueError:
            console.print(f"[yellow]Ignoring invalid sweep value: {part}[/]")
    return values


def _build_launch_command(
    recommendation: Recommendation,
    profile,
    variants: list[tuple[str, str, str]],
) -> str:
    label = recommendation.recommended_label
    model_path = ""
    quant = profile.model.quantization.value
    for v_label, path, v_quant in variants:
        if v_label == label or label.startswith(v_label):
            model_path = path
            quant = v_quant
            break
    threads = profile.runtime.threads
    batch_threads = profile.runtime.batch_threads
    concurrency = profile.runtime.concurrency

    if label.startswith("thread_"):
        try:
            threads = int(label.split("_")[1])
        except (IndexError, ValueError):
            pass
    if label.startswith("concurrency_"):
        try:
            concurrency = int(label.split("_")[1])
        except (IndexError, ValueError):
            pass

    cmd = f"llama-server -m {model_path or '<model.gguf>'} "
    cmd += f"-t {threads} "
    if batch_threads:
        cmd += f"-tb {batch_threads} "
    cmd += f"-c {profile.model.context_size} -np {concurrency}"
    if profile.runtime.enable_prompt_cache:
        cmd += " --prompt-cache"
    cmd += f"  # quantization: {quant}"
    return cmd


if __name__ == "__main__":
    app()
