# ArmTune Serve — Project Architecture

> Architecture discovery document following the project-architecture-discovery
> structure: context, facts vs assumptions, users, workflows, domain model,
> system boundary, architecture decisions, risks, blueprint, and roadmap.

**Project:** ArmTune Serve
**Track:** Arm Create: AI Optimization Challenge — Cloud AI
**Repository:** https://github.com/luxmikant/Arm-Tune
**License:** MIT
**Updated:** 2026-08-13

---

## Phase 0 — Project context

### 0.1 Project stage

| Classification | Status |
|---|---|
| idea only | past |
| problem discovery | past |
| requirements gathering | done |
| architecture exploration | done |
| prototype | done |
| initial repository | done |
| **first vertical slice** | **current** (real inference → benchmark → recommend → report works end-to-end on ARM64 CI) |
| pre-production | not yet |
| production evolution | not yet |

Decidable now: domain model, module boundaries, runtime abstraction, measurement
schema, recommendation rules, CI strategy.
Not decidable yet: NUMA/affinity tuning gains, vLLM adapter viability, SME/SME2
behavior — all require larger Arm hardware (M6).

### 0.2 Project thesis

> **ArmTune Serve** helps **developers deploying LLMs on Arm64 cloud servers**
> accomplish **a measured, reproducible inference configuration (quantization,
> threads, concurrency)** by accepting **a model (Hugging Face GGUF or local
> file), a profile, and a workload**, applying **hardware detection,
> Arm Performix profiling, llama.cpp benchmarking, and quality-gated
> recommendation**, and producing **reports (JSON/CSV/Markdown/charts), a
> recommended configuration, and a copy-paste launch command**.
> The most important design constraints are **4-core/15 GB CI runner limits,
> Arm-only hardware counters, and a fixed deadline**, and the riskiest
> assumptions are **that KleidiAI builds complete on the runner and that
> Performix CLI probing produces parseable output**.

### 0.3 Source material categorization

| Statement | Category | Confidence | Source | Consequence |
|---|---|---:|---|---|
| Runs on ARM64 GitHub Actions runner | FACT | 100% | CI logs (Neoverse-N2, 4C/15GB, SVE2) | Search space is small: threads 1-4, concurrency 1-2 |
| llama-cpp-python builds from source on runner | FACT | 100% | CI logs | Python bindings are a valid fallback |
| KleidiAI build improves Arm CPU inference | ASSUMPTION | 80% | Arm learning paths, llama.cpp docs | Verified by generic-vs-optimized benchmark in CI |
| Performix CLI is binary `apx` with unknown flags | FACT/UNKNOWN | 90% | CI download log | Profiler uses candidate-command probing |
| vLLM is deployable on a 4-core runner | ASSUMPTION | 20% | Arm vLLM learning path (needs 32 vCPU/64GB) | vLLM adapter deferred to M6, opt-in |
| Quality = valid JSON + expected category | DECISION | 90% | scorer.py | Quality gate rejects fast-but-wrong configs |
| Recommendation should be per-objective | DECISION | 100% | Devpost criteria | 4 objectives: latency/throughput/memory/balanced |
| Detect capabilities, not vendor names | DECISION | 100% | design | Covers Graviton/Cobalt/Axion/Ampere without hardcoding |
| HF token needed for gated models | UNKNOWN | — | not yet exercised | `HF_TOKEN` env passthrough already implemented |

### 0.4 Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---:|---|---|
| KleidiAI build fails/times out on runner | medium | high | build cached; generic-build fallback; report runtime evidence either way |
| Performix probe returns no parseable output | medium | medium | status recorded (`attempted-no-output`); raw output saved; patch flags after seeing `apx --help` |
| Mock adapter silently used in CI | medium | critical | report marks backend; reviewer checklist greps logs for "falling back to mock" |
| Runner hardware variance between runs | high | low | full hardware inventory recorded per run |
| Thread sweep doesn't change real threads | low | high | each sweep config recreates adapter → fresh llama-server |
| 60/90-minute job timeout | medium | high | build cache, quant limited to 3, requests limited |

---

## Phase 1 — Users and workflows

### 1.1 Actors

| Actor | Goal | Interaction | Frequency | Failure impact |
|---|---|---|---|---|
| ML engineer on Arm server | best latency/throughput config | CLI + dashboard | per deployment | wrong config, wasted resources |
| CI pipeline | regression evidence | `armtune benchmark` in workflow | per commit/weekly | silent performance regressions |
| Hackathon judge | reproducible evidence | README + artifacts + video | once | submission credibility |
| Hugging Face hub | model source | `hf_hub_download` | per pull | cached under `models/` |
| llama-server process | inference runtime | subprocess + HTTP API | per benchmark | invalid measurements |
| Arm Performix CLI (`apx`) | hardware counters | subprocess probe | per benchmark | missing IPC/cache evidence |

### 1.2 Core workflows

**W1 — Detect hardware**

```text
1. User runs `armtune detect`.
2. Detector reads platform.machine, /proc/cpuinfo, lscpu, psutil, /proc/meminfo.
3. Produces HardwareInfo (CPU, features, cores, memory, NUMA).
4. CLI renders a Rich table or JSON.
```

**W2 — Pull a model from Hugging Face**

```text
1. User runs `armtune models list <repo>` or the dashboard HF tab.
2. Hub connector lists *.gguf files and parses quantization tags.
3. User selects quantization; `armtune models pull` downloads with resume.
4. Model cached at models/<repo>__<file>; path returned.
```

**W3 — Benchmark a configuration (core vertical slice)**

```text
1. User runs `armtune benchmark --profile X --repo R --quant Q1,Q2 --threads 1,2,4`.
2. Profile is loaded (YAML via Pydantic); models resolved from HF cache.
3. Adapter factory selects runtime: llama-server binary > llama_cpp lib > mock.
4. For each quant variant: adapter starts llama-server (threads, ctx, slots),
   startup evidence captured (system_info, CPU_KLEIDIAI, NEON/SVE lines).
5. Warmup requests run (excluded from metrics).
6. Measurement: N requests x R repetitions; streaming /completion responses
   yield TTFT, decode tok/s, prompt tok/s, completion tokens.
7. Concurrently, PerformixCapture probes `apx` on the server PID for ~10s.
8. MetricsCollector samples system CPU, system RAM, and process RSS.
9. Adapter shut down; results stored as RunResult.
10. Optional sweeps: threads [1,2,4], concurrency [1,2] — each fresh adapter.
11. Recommendation engine ranks results by objective (quality gate >= 0.5).
12. ReportGenerator writes JSON, CSV, Markdown, and 4 chart PNGs.
13. CLI prints recommended config + copy-paste llama-server launch command.
```

**W4 — Recommend from stored results**

```text
1. User runs `armtune recommend --latest --objective low-latency`.
2. Loader reads newest results.json under results/.
3. Engine filters by quality threshold, ranks by objective score.
4. Rich table shows ranked configs; winner and reasoning printed.
```

**W5 — View the dashboard**

```text
1. User runs `armtune dashboard`.
2. Gradio app reads results dir (fallback: empty states).
3. Tabs: Hardware, Sweeps, Performix, Recommendation, Hugging Face.
4. HF tab can pull a model and run the full benchmark in one click
   (subprocess `armtune benchmark`) with live logs.
```

**W6 — CI benchmark pipeline**

```text
1. Workflow triggered on ubuntu-24.04-arm.
2. Hardware inventory recorded.
3. llama.cpp built twice: build-arm-opt (KleidiAI + -mcpu=native),
   build-generic (baseline); cached between runs.
4. Arm Performix CLI installed; models pulled from HF (3 quants).
5. Baseline benchmark with generic binary; optimized with KleidiAI binary.
6. Recommendation + report generated; artifacts uploaded.
```

### 1.3 Failure behavior

| Failure | Behavior |
|---|---|
| Model file missing | CLI falls back to mock with a visible warning |
| llama-server exits early | RuntimeError with tail of server stderr |
| Performix unavailable | status=`unavailable`, benchmark continues |
| Performix probe no output | status=`attempted-no-output`, command recorded |
| Sweep value invalid | ignored with warning |
| No results for recommend | clean exit with guidance |
| Gradio missing | exit with install hint (`pip install 'armtune-serve[dashboard]'`) |

---

## Phase 2 — Domain model and system boundary

### 2.1 Domain concepts

```text
HardwareInfo ── CPUInfo (arch, model, features[])
            ├── MemoryInfo (total/available/used, swap)
            ├── NUMAInfo (nodes, cores per node)
            └── GPUInfo (available, devices[])        [future]

Profile ── Objective (low-latency|high-throughput|low-memory|balanced)
        ├── ModelConfig (name, repo_id, quantization, context_size, batch_size)
        ├── RuntimeConfig (threads, batch_threads, concurrency, backend, mmap/mlock)
        ├── BenchmarkConfig (warmup, requests, repetitions, max_tokens, seed)
        └── PerformixConfig (enabled, sample_period_ms)

GenerationRequest ── prompt, max_tokens, temperature, seed
GenerationResponse ── text, prompt/completion tokens, ttft_s, total_s,
                      decode tok/s, prompt tok/s

RunResult ── label, BenchmarkMetrics, quality_scores, latencies,
             queue_delays, ttfts, runtime_evidence
BenchmarkResult ── profile_name, objective, metrics, hardware_info,
                   runtime_info, performix_profile, sweep_results

BenchmarkMetrics ── ttft, p50/p95/p99, stdev, queue_delay_mean,
                    aggregate tok/s, decode tok/s, prompt tok/s,
                    peak system RAM, peak process RSS, quality, counts

PerformixProfile ── status, command, version, stderr, raw_json,
                    counters (IPC, branch mispredict %, LLC miss %,
                    mem bandwidth, stall %, SIMD %), bottlenecks[]

Recommendation ── objective, recommended_label, reasoning,
                  metrics_summary, ranked_results, launch_command
```

### 2.2 Module boundaries

```text
┌──────────────────────────────────────────────────────────────┐
│  armtune.cli (Typer)                                         │
│  detect · benchmark · recommend · report · dashboard         │
│  models list · models pull                                   │
├──────────────┬───────────────┬───────────────────────────────┤
│ config.py    │ orchestration │ presentation                  │
│ (Pydantic    │ benchmark/    │ report/generator.py           │
│  models)     │ orchestrator.py│ dashboard/app.py (Gradio)     │
├──────────────┴───────┬───────┴───────────────────────────────┤
│                      │                                        │
│  detect/        runtime/            performix/                │
│  (hardware     base (ABC)          installer.py               │
│   inventory)   factory (auto       profiler.py (Capture)      │
│                select)             parser.py                  │
│                llama_server.py     models.py                  │
│                llama_cpp.py                                  │
│                mock.py                                       │
│                      │                                        │
│  models/hub.py      analyze/           prompts/               │
│  (Hugging Face      recommender.py     loader.py              │
│   connector)        scorer.py                                 │
└──────────────────────────────────────────────────────────────┘
```

Boundary rules:

1. `runtime/` is the only place that talks to llama.cpp — via subprocess or bindings.
2. `performix/` is the only place that talks to the Arm Performix CLI.
3. `models/hub.py` is the only place that talks to Hugging Face.
4. `benchmark/` owns measurement math; `analyze/` owns scoring and ranking.
5. `report/` and `dashboard/` are read-only consumers of result artifacts.
6. Every layer failure degrades gracefully: real → lib → mock; captured → attempted → unavailable.

### 2.3 Data contracts

**results.json**

```json
{
  "timestamp": 1755612345.0,
  "results": [
    {
      "profile_name": "baseline_Q4_K_M",
      "objective": "balanced",
      "metrics": {
        "ttft_seconds": 0.31,
        "p50_latency_seconds": 0.72,
        "p95_latency_seconds": 1.1,
        "p99_latency_seconds": 1.4,
        "aggregate_tokens_per_second": 18.4,
        "tokens_per_second": 17.9,
        "prompt_tokens_per_second": 42.0,
        "queue_delay_mean_seconds": 0.0,
        "peak_process_rss_mb": 980.0,
        "avg_quality_score": 0.86,
        "total_requests": 10,
        "successful_requests": 10
      },
      "hardware_info": {
        "architecture": "aarch64",
        "cpu_model": "Neoverse-N2",
        "physical_cores": 4,
        "features": ["fp", "asimd", "sve2", "i8mm", "bf16"]
      },
      "runtime_info": {
        "threads": 4,
        "batch_threads": 0,
        "concurrency": 1,
        "quantization": "Q4_K_M",
        "backend": "LlamaServerAdapter",
        "evidence": { "system_info:": "n_threads = 4 ... NEON = 1 | SVE = 1" }
      },
      "performix": {
        "status": "captured",
        "command": "apx profile --pid 1234 ...",
        "counters": { "instructions_per_cycle": 0.7, "ll_cache_miss_rate": 4.2 }
      }
    }
  ],
  "recommendation": {
    "recommended_label": "baseline_Q4_K_M",
    "reasoning": "...",
    "launch_command": "llama-server -m models/...gguf -t 4 -c 2048 -np 1"
  }
}
```

**CSV columns:** profile, ttft_s, prompt_tok_s, p50/p95/p99, queue_delay_s,
throughput_tok_s, avg_tok_s, peak_ram_mb, peak_rss_mb, avg_cpu_pct, quality,
runtime, threads, batch_threads, concurrency, quantization, performix_*.

---

## Phase 3 — Architecture decisions (ADRs)

### ADR-1: Runtime abstraction behind an adapter

- **Problem:** multiple inference engines (llama.cpp binary, Python bindings, later vLLM) must share one benchmark harness.
- **Alternatives:** hardcode llama_cpp bindings; separate benchmark scripts per engine.
- **Selected:** `RuntimeAdapter` ABC (`initialize/generate/shutdown/is_available/process_id/model_path`) + factory with auto-selection: `llama-server` on PATH/env → `llama_cpp` module → `MockAdapter`.
- **Consequences:** one measurement path for all runtimes; sweep configs spawn fresh adapters; vLLM can be added later as a new class.
- **Reconsider if:** the OpenAI-compatible server API diverges between engines (then move timing normalization into the adapter contract).

### ADR-2: Benchmark llama-server via subprocess, not Python bindings

- **Problem:** Python bindings cannot represent a KleidiAI/`-mcpu=native`-compiled binary, and the hackathon needs that Arm-specific evidence.
- **Alternatives:** use only llama-cpp-python; parse `llama-cli` stdout.
- **Selected:** subprocess `llama-server` + streaming `/completion` API; startup stderr captured for `system_info`/`CPU_KLEIDIAI` evidence; `ARMTUNE_LLAMA_SERVER` env selects the binary.
- **Consequences:** benchmarks the exact production artifact; native `timings` (prompt_per_second, predicted_per_second) feed metrics; process RSS measurable via PID.
- **Reconsider if:** a target platform cannot build llama-server (bindings remain as fallback).

### ADR-3: Performix probing instead of fixed CLI flags

- **Problem:** the `apx` CLI subcommands are not documented in a stable public spec.
- **Alternatives:** hardcode one command; skip Performix.
- **Selected:** probe a ranked list of candidate invocations in a background thread during inference; record command, exit code, stderr, version, and status (`captured | attempted-no-output | unavailable | failed`); parse any JSON produced.
- **Consequences:** never silently fails; one real `apx --help` capture lets us lock the flags.
- **Reconsider if:** official Performix CLI docs are available (then pin exact subcommands).

### ADR-4: Capability fingerprinting instead of vendor hardcoding

- **Problem:** Graviton/Cobalt/Axion/Ampere names hide actual ISA features.
- **Selected:** read `/proc/cpuinfo` features (NEON/DotProd/I8MM/SVE/SVE2/BF16) + cores + NUMA; store in every result; optional platform label is informational only.
- **Consequences:** the same search space works on any Arm server; feature presence can gate experiments (e.g., test i8mm-heavy quants only when i8mm present).

### ADR-5: Quality gate before recommendation

- **Problem:** speed optimizations can silently degrade output.
- **Selected:** structured JSON scorer (4 expected keys, valid enums) + correctness bonus against `expected_category` in prompts; configs below 0.5 are excluded from recommendations.
- **Consequences:** recommendations are speed+quality Pareto-aware.

### ADR-6: File-based results as the single source of truth

- **Problem:** dashboard, report, and recommendation must stay consistent without a database.
- **Selected:** every run writes a timestamped directory under `results/` with JSON/CSV/MD/charts; all consumers are read-only over these files; `--latest` picks the newest.
- **Consequences:** zero infra for the dashboard; artifacts are portable evidence for the hackathon.
- **Reconsider if:** multi-user production deployment (then a small store + REST API).

### ADR-7: Gradio over Streamlit

- **Problem:** which Python dashboard to ship with limited time.
- **Alternatives:** Streamlit, FastAPI+JS.
- **Selected:** Gradio — tabbed layout, one-click HF pull+benchmark with live logs, no JS build.
- **Consequences:** Gradio 6 API changes required compat fixes (no `show_copy_button`, no `interactive` on outputs).

### ADR-8: YAML profiles via Pydantic with safe defaults

- **Selected:** profiles as versioned YAML; new fields (batch_threads, repetitions, runtime_backend) default backward-compatibly; quantization tags auto-discovered from HF filenames feed `QuantizationFormat` enum.

---

## Phase 4 — Blueprint (Mode C)

### 4.1 Repository structure (as built)

```text
armtune/
├── cli.py               # Typer CLI + models subcommands + dashboard command
├── config.py            # Pydantic profile/objective/quant models
├── detect/              # detector.py, models.py (hardware inventory)
├── performix/           # installer, models, profiler (Capture), parser
├── runtime/             # base, factory, llama_server, llama_cpp, mock
├── benchmark/           # metrics.py, orchestrator.py
├── analyze/             # recommender.py, scorer.py
├── report/              # generator.py (JSON/CSV/MD/charts)
├── models/              # hub.py (Hugging Face connector)
├── dashboard/           # app.py (Gradio, 5 tabs)
└── prompts/             # loader.py (+ tickets.json data)
configs/                 # baseline, balanced, low-latency, high-throughput, low-memory
prompts/tickets.json     # 5 labeled tickets
scripts/                 # install-performix.sh, download-model.sh, build-llama-cpp.sh
tests/                   # 25 unit tests (offline)
docs/                    # PROJECT-PLAN, DELIVERABLES, REQUIREMENTS, ROADMAP, ARCHITECTURE
.github/workflows/       # test-arm64.yml, benchmark-arm64.yml
results/                 # gitignored benchmark artifacts
```

### 4.2 Milestone state

| M# | Name | Status |
|----|------|--------|
| M1 | Native ARM64 foundation | done |
| M2 | Baseline benchmark (real llama.cpp now) | done |
| M3 | Optimization sweeps (threads, concurrency, quants, KleidiAI vs generic) | done |
| M4 | Recommendation + reporting | done |
| M5 | Dashboard (Gradio) | done |
| M6 | Arm server validation (NUMA/affinity, larger models, vLLM adapter, pinned apx flags) | next |
| M7 | CPU-GPU extension | future |

### 4.3 Vertical slice already demonstrated

```text
HF pull → llama-server start → warmup → 10-request measurement
→ Performix capture → metrics aggregation → quality scoring
→ recommendation → report + launch command
```

Runs end-to-end in GitHub Actions on `ubuntu-24.04-arm` (workflow `Benchmark ARM64`).

### 4.4 Test strategy

| Layer | Strategy |
|---|---|
| Scorer / recommender | pure unit tests (offline) |
| HF filename quantization parsing | unit tests, no network |
| Config / prompts / metrics | unit tests with defaults |
| Hardware detection | unit tests on models; smoke test on ARM64 CI |
| llama-server integration | ARM64 CI workflow only (not run on Windows dev) |
| Performix capture | ARM64 CI, status-recorded, never failing the job |
| Lint / type | `ruff check`; mypy optional |

### 4.5 Local development setup

```bash
# Windows (dev only — detection works, benchmarks need ARM64)
pip install -e ".[dev]"
pip install -e ".[dashboard]"
armtune --version && armtune detect
pytest tests/ -q && ruff check armtune/ tests/
armtune dashboard   # http://127.0.0.1:7860

# ARM64 (real benchmarking)
git clone https://github.com/luxmikant/Arm-Tune && cd Arm-Tune
pip install -e .
bash scripts/install-performix.sh
bash scripts/build-llama-cpp.sh
export ARMTUNE_LLAMA_SERVER=llama.cpp/build-arm-opt/bin/llama-server
armtune benchmark --profile configs/balanced.yaml \
  --repo unsloth/Llama-3.2-1B-Instruct-GGUF \
  --quant Q4_K_M,Q4_0,Q8_0 --threads 1,2,4 --concurrency 1,2
armtune recommend --latest && armtune report --latest && armtune dashboard
```

### 4.6 Deployment concept

| Environment | Role | Artifacts |
|---|---|---|
| GitHub Actions `ubuntu-24.04-arm` | reproducible benchmark CI | report + charts + Performix JSON |
| Any Arm64 Linux server (Graviton/Cobalt/Axion/Ampere) | manual/automated tuning | same artifacts |
| Local machine | dashboard + development | Gradio on 127.0.0.1 |

---

## Phase 5 — Open questions and next experiments

| # | Unknown | Experiment |
|---|---|---|
| E1 | Real `apx` CLI flags | capture `apx --help` on the ARM64 runner; pin commands in profiler |
| E2 | KleidiAI speedup on Neoverse-N2 (4-core) | generic vs arm-opt benchmark in CI; expect smaller gap than Graviton4 |
| E3 | Best quantization for this CPU+workload | Q4_K_M vs Q4_0 vs Q8_0 sweep with quality gate |
| E4 | Thread oversubscription curve | threads 1,2,3,4 × batch_threads 1,2,4 |
| E5 | Prompt-cache benefit on repeated system prompt | enable_prompt_cache on/off with same prompts |
| E6 | vLLM vs llama.cpp on Arm server (M6) | VllmAdapter on a 32-vCPU instance |
| E7 | NUMA/affinity gains (M6) | taskset/numactl experiments on multi-NUMA server |
