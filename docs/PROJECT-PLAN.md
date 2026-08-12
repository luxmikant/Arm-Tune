# ArmTune Serve — PROJECT PLAN

> **Arm64-aware observability, benchmarking, and configuration-recommendation toolkit for LLM inference.**
> Built for: **Arm Create — AI Optimization Challenge (Cloud AI track)**

---

## Project summary

ArmTune Serve finds and demonstrates the best LLM deployment configuration
(model quantization, CPU threads, request concurrency) for a specific Arm64
cloud server, then serves that configuration with reproducible benchmark
evidence validated by **Arm Performix** hardware performance counters.

**Core question:** _How can a developer select and deploy the best CPU-only LLM
configuration for a specific Arm64 cloud server?_

## The problem

Running an LLM on an Arm CPU server involves many interdependent choices:

| Choice | Example trade-offs |
|--------|-------------------|
| Model quantization | INT4 reduces memory but may degrade quality |
| CPU thread count | More threads improve throughput but hurt latency |
| Request concurrency | Higher concurrency increases tok/s but worsens P95 |
| Prompt caching | Helps repeated prompts but uses KV-cache memory |

There is no universal answer. The optimal config on a 4-core Ampere VM
differs from a 32-core Graviton server.

## Solution

ArmTune Serve automates trial-and-error configuration exploration:

1. **Hardware detection** — reads architecture, CPU model, core count, memory,
   NUMA topology, and CPU features
2. **Arm Performix profiling** — collects hardware performance counters (IPC,
   cache misses, branch prediction, memory bandwidth) for exact Arm-native
   evidence
3. **Inference benchmarking** — runs config sweep across quantizations, thread
   counts, and concurrency levels via `llama.cpp`
4. **Quality scoring** — structured JSON output validation ensures we never
   recommend a fast-but-broken config
5. **Recommendation engine** — selects the best config per objective
   (low-latency, high-throughput, low-memory, balanced)
6. **Reproducible reports** — JSON, CSV, Markdown, and charts with full
   hardware + runtime metadata

## Demonstration workload

Support-ticket classification with structured JSON summarization:

```json
{
  "summary": "Customer reports duplicate billing.",
  "category": "billing",
  "priority": "high",
  "recommended_action": "Review invoices and initiate a refund if confirmed."
}
```

Uses a fixed prompt set so benchmark results are comparable across
configurations.

## Architecture

```text
┌───────────────────────────────────────────────────────────────┐
│  armtune CLI (Typer)                                          │
│  ┌──────────┐ ┌────────────┐ ┌───────────┐ ┌────────┐        │
│  │ detect   │→│ benchmark  │→│ analyze   │→│ report │        │
│  └────┬─────┘ └──────┬─────┘ └─────┬─────┘ └───┬────┘        │
│       │              │             │            │              │
│       ▼              ▼             ▼            ▼              │
│  Hardware       llama.cpp    Recommendation  JSON / CSV       │
│  Detection      (runtime)     Engine         / Markdown       │
│       │              │                      / Charts          │
│       └──────────────┴─────────────────┐                      │
│                                        ▼                      │
│                             Arm Performix CLI                 │
│                        (Hardware counter profiling)            │
└───────────────────────────────────────────────────────────────┘
```

## Arm Performix integration

Arm Performix is Arm's free performance analysis toolkit for Neoverse
platforms (AWS Graviton, Azure Cobalt, Google Axion). It provides:

- **IPC (instructions per cycle)** — CPU efficiency
- **Cache miss rates (L1/L2/LLC)** — memory hierarchy efficiency
- **Branch misprediction rate** — control flow efficiency
- **Memory bandwidth (read/write)** — memory subsystem pressure
- **Frontend/backend stalls** — where cycles are wasted
- **NEON/SVE utilization** — SIMD vectorization

ArmTune Serve downloads Performix CLI during the GitHub Actions workflow and
profiles the `llama.cpp` process during benchmarks.

## Roadmap (milestones)

| M# | Name | Status |
|----|------|--------|
| M1 | Native ARM64 foundation | Complete |
| M2 | Baseline benchmark | Complete |
| M3 | Optimization sweeps | Complete |
| M4 | Recommendation & reporting | Complete |
| M5 | Dashboard (Streamlit) | Planned |
| M6 | Arm server validation | Planned |
| M7 | CPU-GPU extension | Future |

## Hackathon submission criteria checklist

- [x] Runs natively on ARM64 GitHub Actions runner
- [x] Detects and records hardware
- [ ] Executes real CPU LLM inference (mock adapter works; real model pending runner size)
- [x] Compares baseline and optimized configurations
- [x] Produces measurable results (JSON / CSV / Markdown / charts)
- [x] Preserves a defined quality threshold
- [x] Recommends a configuration transparently
- [x] Generates a reproducible report
- [x] Public source code and instructions

## Technologies

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| CLI | Typer + Rich |
| Inference runtime | llama.cpp (via llama-cpp-python) |
| Hardware profiling | **Arm Performix CLI** |
| Metrics | psutil, custom collector |
| Quality scoring | JSON validator + structured grading |
| Recommendation | Multi-objective scoring engine |
| Reporting | Jinja2, matplotlib, pandas |
| CI/CD | GitHub Actions (`ubuntu-24.04-arm`) |
| Config | YAML via Pydantic |
