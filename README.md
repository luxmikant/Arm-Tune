# ArmTune Serve

[![Test ARM64](https://github.com/luxmikant/Arm-Tune/actions/workflows/test-arm64.yml/badge.svg)](https://github.com/luxmikant/Arm-Tune/actions/workflows/test-arm64.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-7ee787.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Arm64%20Linux-0091bd.svg)](https://www.arm.com/architecture)

[Product site](https://luxmikant.github.io/Arm-Tune/) · [Documentation](docs/USAGE.md) · [Hugging Face model card](huggingface/README.md)

**Tune every token to the architecture it runs on.**

ArmTune Serve is an Arm64-aware LLM inference optimization toolkit. It takes a
Hugging Face GGUF model and a fixed workload, measures quantization, CPU
threads, prefill threads, and request concurrency on the target machine, then
returns a quality-gated deployment recommendation with reproducible evidence.

It is not a new inference engine. It is the measurement and decision layer
around `llama.cpp`, with Arm Performix hardware analysis built into the loop.

```text
Hugging Face model
        |
        v
  ArmTune Serve  ---- Arm Performix counters
        |
        v
llama.cpp / llama-server ---- Arm64 CPU
        |
        v
recommendation + report + deploy command
```

## Why it exists

An LLM configuration that is fast on one Arm server can be poor on another.
The useful settings depend on the ISA extensions, core count, memory bandwidth,
NUMA topology, model quantization, context size, and request mix.

ArmTune answers a practical deployment question:

> Which model and runtime configuration gives the best latency, throughput, or
> memory efficiency on this exact Arm64 machine without breaking output quality?

The result is a command a developer can deploy, not just a chart.

## What it measures

| Layer | Measurements |
|---|---|
| Model | GGUF quantization, model file size, context configuration |
| Inference | TTFT, prompt tok/s, decode tok/s, total tokens |
| Server | P50/P95/P99 latency, queue delay, aggregate throughput |
| System | CPU utilization, peak process RSS, RAM, NUMA, ISA features |
| Quality | Structured JSON validity and expected ticket category |
| Arm microarchitecture | IPC, cache misses, branch misses, stalls, memory bandwidth |

Arm Performix is used for the hardware-level evidence. The project also builds
two llama.cpp variants on Arm64: a generic CPU baseline and an Arm-optimized
KleidiAI/native build.

## Quick start on Arm64 Linux

```bash
git clone https://github.com/luxmikant/Arm-Tune.git
cd Arm-Tune

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Install the optional Arm/runtime tooling.
bash scripts/install-performix.sh
bash scripts/build-llama-cpp.sh

# Inspect the machine and available Hugging Face quantizations.
armtune detect
armtune models list unsloth/Llama-3.2-1B-Instruct-GGUF

# Benchmark the model and sweep Arm CPU settings.
export ARMTUNE_LLAMA_SERVER=llama.cpp/build-arm-opt/bin/llama-server
armtune benchmark \
  --profile configs/balanced.yaml \
  --repo unsloth/Llama-3.2-1B-Instruct-GGUF \
  --quant Q4_K_M,Q4_0,Q8_0 \
  --threads 1,2,4 \
  --concurrency 1,2

# Inspect the recommendation and open the local dashboard.
armtune recommend --latest --objective balanced
armtune dashboard
```

Open `http://127.0.0.1:7860` for the Gradio dashboard.

## Hugging Face in one command

```bash
armtune models pull unsloth/Llama-3.2-1B-Instruct-GGUF --quant Q4_K_M
armtune benchmark --repo unsloth/Llama-3.2-1B-Instruct-GGUF \
  --quant Q4_K_M,Q8_0 --threads 1,2,4
```

Models are cached below `models/`. Set `HF_TOKEN` for gated repositories.

## GitHub Actions on native Arm64

The benchmark workflow runs on `ubuntu-24.04-arm` and records the runner's
Neoverse hardware inventory. It builds the generic and KleidiAI llama.cpp
variants, downloads selected GGUF files, runs the baseline and optimized
matrix, and uploads JSON, CSV, Markdown, chart, and Performix artifacts.

Run it from **Actions > Benchmark ARM64 > Run workflow**. The workflow is the
reproducible reference environment; any Arm64 Linux server can run the same
commands manually.

## CPU-first Arm optimization

The first-class optimization path is deliberately CPU-focused:

1. Detect NEON, DotProd, I8MM, SVE, SVE2, BF16, cores, RAM, and NUMA.
2. Build llama.cpp with `GGML_CPU_KLEIDIAI=ON` and `-mcpu=native`.
3. Compare Q4/Q8 quantizations against the same prompt set.
4. Sweep decode threads, batch threads, and server concurrency.
5. Profile the real inference process with Arm Performix.
6. Reject configurations below the output-quality threshold.

The same design can later measure CPU+GPU deployments. Even with a GPU, the CPU
still handles tokenization, scheduling, queueing, KV-cache management, memory
transfers, and CPU-offloaded layers.

## Documentation

| Document | Purpose |
|---|---|
| [Beginner's guide](docs/USAGE.md) | Install and run the complete flow |
| [Architecture](docs/ARCHITECTURE.md) | Domain model, workflows, ADRs, contracts |
| [Use-case justification](docs/JUSTIFICATION.md) | Why CPU-side Arm optimization matters |
| [Project plan](docs/PROJECT-PLAN.md) | Scope and milestones |
| [Deliverables](docs/DELIVERABLES.md) | Hackathon evidence and outputs |
| [Requirements](docs/REQUIREMENTS.md) | Devpost criteria mapping |
| [Roadmap](docs/ROADMAP.md) | Current status and next milestones |
| [PyPI release](docs/PYPI.md) | Build and publish instructions |
| [Hugging Face model card](huggingface/README.md) | Model repository content and upload flow |

## Repository layout

```text
armtune/
├── cli.py              # detect, benchmark, recommend, report, dashboard
├── detect/             # Arm64 hardware and capability fingerprint
├── models/             # Hugging Face GGUF connector
├── runtime/            # llama-server, llama.cpp, and mock adapters
├── benchmark/          # workload orchestration and metrics
├── performix/          # Arm Performix installation and profiling
├── analyze/            # quality scoring and recommendations
├── report/             # JSON, CSV, Markdown, and charts
└── dashboard/          # Gradio product interface
configs/                # deployment profiles
prompts/                # fixed evaluation workload
scripts/                # Arm setup and llama.cpp build scripts
docs/                   # architecture, usage, release, and hackathon docs
site/                   # static product and documentation website
huggingface/            # publishable model-card content
tests/                  # offline unit tests
```

## Release status

The package is currently installable from source. The repository includes a
PyPI trusted-publishing workflow and release instructions. Publish a versioned
tag only after the Arm64 benchmark evidence has been reviewed.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, reproducible benchmark
results, new Arm platform profiles, and documentation improvements are welcome.

## License

MIT. See [LICENSE](LICENSE).
