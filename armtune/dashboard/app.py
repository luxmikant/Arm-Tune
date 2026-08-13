"""Gradio dashboard: Hardware | Sweeps | Performix | Recommendation | Hugging Face."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import gradio as gr
import pandas as pd

from ..detect.detector import detect_hardware
from ..models.hub import list_gguf_models


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
        return pd.DataFrame({"info": ["No benchmark results yet. Run: armtune benchmark"]})

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
        return "No recommendation yet. Run: armtune benchmark", ""

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


def _list_quants(repo_id: str) -> gr.Dropdown:
    if not repo_id.strip():
        return gr.Dropdown(choices=[], value=None)
    try:
        items = list_gguf_models(repo_id.strip())
    except Exception as e:
        return gr.Dropdown(choices=[], value=None, label=f"Error: {e}")
    quants = [i["quantization"] for i in items]
    return gr.Dropdown(choices=quants, value=quants[0] if quants else None)


def _pull_and_benchmark(
    repo_id: str,
    quant: str,
    profile: str,
    threads: str,
    concurrency: str,
) -> str:
    if not repo_id.strip():
        return "Enter a Hugging Face repo first."
    cmd = [sys.executable, "-m", "armtune.cli", "benchmark",
           "--repo", repo_id.strip(), "--profile", profile or "balanced"]
    if quant:
        cmd += ["--quant", quant]
    if threads.strip():
        cmd += ["--threads", threads.strip()]
    if concurrency.strip():
        cmd += ["--concurrency", concurrency.strip()]

    log = [f"$ {' '.join(cmd)}", ""]
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
            if len(log) > 200:
                log = log[-200:]
        proc.wait()
        log.append(f"\nExit code: {proc.returncode}")
        log.append("Done. Refresh the Sweeps/Recommendation tabs.")
    except Exception as e:
        log.append(f"Failed: {e}")
    return "\n".join(log)


def _chart_gallery(results_dir: str):
    run_dir = _latest_run_dir(results_dir)
    if run_dir is None:
        return None
    images = []
    for name in ("charts.png", "sweeps.png", "performix.png", "improvements.png"):
        path = run_dir / name
        if path.exists():
            images.append((str(path), name))
    return images if images else None


def build_dashboard(results_dir: str = "results") -> gr.Blocks:
    with gr.Blocks(title="ArmTune Serve") as demo:
        gr.Markdown("# ArmTune Serve — Arm64 LLM inference optimizer")

        with gr.Tab("Hardware"):
            hw_table = gr.Dataframe(value=_hardware_table())
            gr.Button("Refresh").click(
                lambda: _hardware_table(), outputs=hw_table
            )

        with gr.Tab("Sweeps"):
            results_table = gr.Dataframe(value=_results_table(results_dir))
            gallery = gr.Gallery(
                value=_chart_gallery(results_dir), label="Charts", columns=2
            )
            gr.Button("Refresh").click(
                lambda: (
                    _results_table(results_dir),
                    _chart_gallery(results_dir),
                ),
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

        with gr.Tab("Hugging Face"):
            gr.Markdown(
                "Pick a GGUF model from Hugging Face and benchmark it on this "
                "Arm machine in one click."
            )
            with gr.Row():
                repo_input = gr.Textbox(
                    label="Hugging Face repo",
                    placeholder="unsloth/Llama-3.2-1B-Instruct-GGUF",
                )
                quant_dropdown = gr.Dropdown(
                    label="Quantization", choices=[], value=None
                )
            with gr.Row():
                profile_input = gr.Textbox(label="Profile", value="balanced")
                threads_input = gr.Textbox(
                    label="Thread sweep (csv)", placeholder="1,2,4"
                )
                concurrency_input = gr.Textbox(
                    label="Concurrency sweep (csv)", placeholder="1,2,4"
                )
            log_box = gr.Textbox(label="Benchmark log", lines=15)
            run_btn = gr.Button("Pull model + run benchmark", variant="primary")
            repo_input.change(_list_quants, inputs=repo_input, outputs=quant_dropdown)
            run_btn.click(
                _pull_and_benchmark,
                inputs=[repo_input, quant_dropdown, profile_input, threads_input, concurrency_input],
                outputs=log_box,
            )

    return demo


__all__ = ["build_dashboard"]
