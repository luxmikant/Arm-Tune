"""Gradio dashboard: Console | Hardware | Sweeps | Performix | Recommendation.

The Console tab is a guided, terminal-style pipeline: search Hugging Face,
inspect the model card, pick quantizations, and run the benchmark with a
live streaming log — no copy-pasting repo names between HF and the CLI.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import gradio as gr
import pandas as pd

from ..detect.detector import detect_hardware
from ..models.hub import (
    get_model_card,
    human_size,
    list_gguf_models,
    search_models,
)


def _latest_run_dir(results_dir: str | Path) -> Path | None:
    base = Path(results_dir)
    if not base.exists():
        return None
    subdirs = sorted(
        [d for d in base.iterdir() if d.is_dir() and (d / "results.json").exists()],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    if not subdirs:
        json_file = base / "results.json"
        if json_file.exists():
            return base
        return None
    return subdirs[0]


def _load_results(results_dir: str | Path) -> dict:
    run_dir = _latest_run_dir(results_dir)
    if run_dir is None:
        return {}
    try:
        return json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


def _hardware_table() -> pd.DataFrame:
    hw = detect_hardware()
    rows = [
        ("Architecture", hw.cpu.architecture),
        ("CPU model", hw.cpu.model_name),
        ("Physical cores", hw.cpu.physical_cores),
        ("Logical cores", hw.cpu.logical_cores),
        ("Total RAM (GB)", hw.memory.total_gb),
        ("NUMA nodes", hw.numa.numa_nodes),
        ("ARM64", "Yes" if hw.is_arm64() else "No"),
        ("Arm features", " ".join(hw.cpu.features[:20])),
    ]
    return pd.DataFrame(rows, columns=["Property", "Value"])


def _results_table(results_dir: str) -> pd.DataFrame:
    data = _load_results(results_dir)
    results = data.get("results", [])
    if not results:
        return pd.DataFrame({"info": ["No benchmark results yet. Run the console or: armtune benchmark"]})

    rows = []
    for r in results:
        m = r.get("metrics", {})
        rt = r.get("runtime_info", {})
        rows.append({
            "profile": r.get("profile_name", "?"),
            "quantization": rt.get("quantization", ""),
            "runtime": rt.get("backend", ""),
            "threads": rt.get("threads", ""),
            "ttft_s": round(m.get("ttft_seconds", 0), 3),
            "p50_s": round(m.get("p50_latency_seconds", 0), 3),
            "p95_s": round(m.get("p95_latency_seconds", 0), 3),
            "p99_s": round(m.get("p99_latency_seconds", 0), 3),
            "tok_s": round(m.get("aggregate_tokens_per_second", 0), 1),
            "prompt_tok_s": round(m.get("prompt_tokens_per_second", 0), 1),
            "queue_s": round(m.get("queue_delay_mean_seconds", 0), 3),
            "peak_rss_mb": round(m.get("peak_process_rss_mb", 0), 0),
            "quality": round(m.get("avg_quality_score", 0), 2),
        })
    return pd.DataFrame(rows)


def _performix_table(results_dir: str) -> pd.DataFrame:
    data = _load_results(results_dir)
    rows = []
    for r in data.get("results", []):
        px = r.get("performix")
        if not px:
            continue
        c = px.get("counters", {})
        rows.append({
            "profile": r.get("profile_name", "?"),
            "status": px.get("status", "?"),
            "ipc": round(c.get("instructions_per_cycle", 0), 3),
            "branch_misp_pct": round(c.get("branch_mispredict_pct", 0), 2),
            "llc_miss_pct": round(c.get("ll_cache_miss_rate", 0), 2),
            "mem_read_mbs": round(c.get("memory_read_bandwidth_mbs", 0), 1),
            "mem_write_mbs": round(c.get("memory_write_bandwidth_mbs", 0), 1),
            "stall_frontend_pct": round(c.get("stall_frontend_pct", 0), 2),
            "stall_backend_pct": round(c.get("stall_backend_pct", 0), 2),
        })
    if not rows:
        return pd.DataFrame({"info": ["No Arm Performix profiles captured yet."]})
    return pd.DataFrame(rows)


def _recommendation_view(results_dir: str) -> tuple[str, str]:
    data = _load_results(results_dir)
    rec = data.get("recommendation")
    if not rec:
        return "No recommendation yet. Run the console or: armtune benchmark", ""

    lines = [
        f"**Objective:** {rec.get('objective', '')}",
        f"**Recommended:** `{rec.get('recommended_label', '')}`",
        "",
        rec.get("reasoning", ""),
        "",
        "**Metrics:**",
    ]
    for k, v in (rec.get("metrics_summary") or {}).items():
        lines.append(f"- {k}: {v}")
    launch = rec.get("launch_command", "")
    return "\n".join(lines), launch


def _chart_gallery(results_dir: str) -> list[tuple[str, str]] | None:
    run_dir = _latest_run_dir(results_dir)
    if run_dir is None:
        return None
    images = []
    for name in ("charts.png", "sweeps.png", "performix.png", "improvements.png"):
        path = run_dir / name
        if path.exists():
            images.append((str(path), name))
    return images if images else None


# ---------------------------------------------------------------------------
# Console: Hugging Face model search + guided benchmark
# ---------------------------------------------------------------------------

def _search_repos(query: str, limit: int = 8) -> tuple[gr.Dropdown, str]:
    if not query.strip():
        return gr.Dropdown(choices=[], value=None), "Type a model name to search Hugging Face."
    try:
        results = search_models(query.strip(), limit=limit)
    except Exception as e:
        return gr.Dropdown(choices=[], value=None), f"Search failed: {e}"
    if not results:
        return gr.Dropdown(choices=[], value=None), f"No models found for '{query}'."
    choices = [
        f"{r['repo_id']}  ({r['downloads']:,} downloads)" for r in results
    ]
    return gr.Dropdown(choices=choices, value=choices[0]), ""


def _repo_details(selection: str) -> tuple[gr.Dropdown, gr.CheckboxGroup, str]:
    if not selection:
        return (
            gr.Dropdown(choices=[], value=None),
            gr.CheckboxGroup(choices=[], value=[]),
            "Pick a model to inspect its card and quantizations.",
        )
    repo_id = selection.split("  (")[0]
    try:
        card = get_model_card(repo_id)
        items = list_gguf_models(repo_id)
    except Exception as e:
        return (
            gr.Dropdown(choices=[], value=None),
            gr.CheckboxGroup(choices=[], value=[]),
            f"Could not load {repo_id}: {e}",
        )

    quant_options = [
        f"{i['quantization']}  ({human_size(i['size_bytes'])})" for i in items
    ]
    default_quants = ["Q4_K_M", "Q4_0", "Q8_0"]
    defaults = [
        option for option in quant_options
        if option.split("  (")[0] in default_quants
    ]

    lines = [
        f"### {repo_id}",
        "",
        f"- Downloads: **{card['downloads']:,}**"
        if card["downloads"] is not None else "- Downloads: unknown",
        f"- Likes: {card['likes']:,}"
        if card["likes"] is not None else "- Likes: unknown",
        f"- License: `{card['license']}`" if card["license"] else "- License: check upstream repo",
        f"- Pipeline: {card['pipeline_tag']}" if card["pipeline_tag"] else "",
        f"- Tags: {' '.join('`' + t + '`' for t in card['tags'][:10])}"
        if card["tags"] else "",
    ]
    card_md = "\n".join(lines)
    return (
        gr.Dropdown(choices=quant_options, value=quant_options[0] if quant_options else None),
        gr.CheckboxGroup(choices=quant_options, value=defaults),
        card_md,
    )


def _run_console(
    repo_selection: str,
    quant_selection: list[str],
    profile: str,
    threads: str,
    concurrency: str,
):
    if not repo_selection:
        yield "Select a model from search results first."
        return
    repo_id = repo_selection.split("  (")[0]
    quants = [q.split("  (")[0] for q in quant_selection]

    cmd = [
        sys.executable, "-m", "armtune.cli", "benchmark",
        "--repo", repo_id,
        "--profile", profile.strip() or "balanced",
        "--output", "results",
    ]
    if quants:
        cmd += ["--quant", ",".join(quants)]
    if threads.strip():
        cmd += ["--threads", threads.strip()]
    if concurrency.strip():
        cmd += ["--concurrency", concurrency.strip()]

    log: list[str] = [f"$ {' '.join(cmd)}", ""]
    yield "\n".join(log)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            log.append(line.rstrip())
            log = log[-150:]
            yield "\n".join(log)
        proc.wait()
        log.append("")
        log.append(f"[exit {proc.returncode}]"
                   f"{'  — refresh Sweeps / Recommendation tabs.' if proc.returncode == 0 else ''}")
        yield "\n".join(log)
    except Exception as e:
        log.append(f"Failed: {e}")
        yield "\n".join(log)


def build_dashboard(results_dir: str = "results") -> gr.Blocks:
    dark = gr.themes.Base(
        primary_hue="green",
        neutral_hue="slate",
    ).set(
        body_background_fill="#090b0d",
        body_background_fill_dark="#090b0d",
        background_fill_primary="#101316",
        background_fill_secondary="#15191d",
        border_color_primary="#28312f",
        block_title_text_color="#b8f36b",
        body_text_color="#f1f5f2",
        body_text_color_subdued="#9aa5a1",
    )

    with gr.Blocks(title="ArmTune Serve") as demo:
        gr.Markdown(
            "# ArmTune Serve\n"
            "**Tune every token to the architecture it runs on.** "
            "Arm64 LLM inference optimization console."
        )

        with gr.Tab("Console"):
            gr.Markdown(
                "Guided pipeline: search Hugging Face, inspect the model card, "
                "pick quantizations, and run the benchmark — the terminal does "
                "the work, the log streams here."
            )
            with gr.Row():
                search_input = gr.Textbox(
                    label="1 · Search Hugging Face",
                    placeholder="e.g. llama 3.2 1b gguf, qwen 0.5b, ...",
                    scale=3,
                )
                search_button = gr.Button("Search", scale=1, variant="primary")
            repo_dropdown = gr.Dropdown(
                label="2 · Matching models", choices=[], interactive=True
            )
            search_status = gr.Markdown("")
            search_button.click(
                _search_repos,
                inputs=search_input,
                outputs=[repo_dropdown, search_status],
            )
            search_input.submit(
                _search_repos,
                inputs=search_input,
                outputs=[repo_dropdown, search_status],
            )

            gr.Markdown("---")
            card_md = gr.Markdown("Pick a model to inspect its card and quantizations.")
            quant_dropdown = gr.Dropdown(
                label="Primary quantization", choices=[], interactive=True
            )
            quant_group = gr.CheckboxGroup(
                label="3 · Quantizations to benchmark", choices=[], value=[]
            )
            repo_dropdown.change(
                _repo_details,
                inputs=repo_dropdown,
                outputs=[quant_dropdown, quant_group, card_md],
            )

            gr.Markdown("---")
            with gr.Row():
                profile_input = gr.Textbox(label="4 · Profile", value="balanced")
                threads_input = gr.Textbox(
                    label="Thread sweep (csv)", placeholder="1,2,4"
                )
                concurrency_input = gr.Textbox(
                    label="Concurrency sweep (csv)", placeholder="1,2"
                )
            run_button = gr.Button(
                "5 · Run benchmark", variant="primary", size="lg"
            )
            console_log = gr.Textbox(
                label="Terminal",
                lines=18,
                max_lines=18,
                value="$ waiting for input…",
            )
            run_button.click(
                _run_console,
                inputs=[
                    repo_dropdown,
                    quant_group,
                    profile_input,
                    threads_input,
                    concurrency_input,
                ],
                outputs=console_log,
            )

        with gr.Tab("Hardware"):
            hw_table = gr.Dataframe(value=_hardware_table())
            gr.Button("Refresh").click(lambda: _hardware_table(), outputs=hw_table)

        with gr.Tab("Sweeps"):
            results_table = gr.Dataframe(value=_results_table(results_dir))
            gallery = gr.Gallery(
                value=_chart_gallery(results_dir), label="Charts", columns=2
            )
            gr.Button("Refresh").click(
                lambda: (_results_table(results_dir), _chart_gallery(results_dir)),
                outputs=[results_table, gallery],
            )

        with gr.Tab("Performix"):
            px_table = gr.Dataframe(value=_performix_table(results_dir))
            gr.Button("Refresh").click(
                lambda: _performix_table(results_dir), outputs=px_table
            )

        with gr.Tab("Recommendation"):
            rec_md = gr.Markdown()
            launch_box = gr.Textbox(label="Deployment command")
            gr.Button("Refresh").click(
                lambda: _recommendation_view(results_dir),
                outputs=[rec_md, launch_box],
            )

    demo.armtune_theme = dark  # Gradio 6 passes theme at launch()
    return demo


__all__ = ["build_dashboard"]
