# ArmTune Serve — Beginner's Guide

A step-by-step walkthrough for a developer who has never used ArmTune before.

## What ArmTune is (one paragraph)

You have an Arm64 server (AWS Graviton, Azure Cobalt, Google Axion, Ampere, or
even a free GitHub Actions ARM64 runner). You want to run an LLM on it, but you
don't know which model quantization, how many CPU threads, or how much request
concurrency gives the best result. ArmTune measures all of those combinations
for you — including Arm hardware counters from Arm Performix — and tells you
the best configuration with a copy-paste launch command and the evidence to
back it up.

## Use flow in 6 steps

```text
1. Install                 pip install armtune-serve
2. Detect your hardware    armtune detect
3. Pull a model            armtune models pull <hf-repo> --quant Q4_K_M
4. Benchmark               armtune benchmark --repo <hf-repo> --threads 1,2,4
5. Get the recommendation  armtune recommend --latest
6. Explore results         armtune dashboard
```

### Step 1 — Install

```bash
# From PyPI (once published) or from GitHub today:
pip install git+https://github.com/luxmikant/Arm-Tune.git
# Optional dashboard:
pip install "armtune-serve[dashboard]"

# One-time runtime setup (Arm64 Linux):
bash scripts/install-performix.sh     # Arm Performix CLI (hardware counters)
bash scripts/build-llama-cpp.sh       # llama.cpp with KleidiAI Arm kernels
```

### Step 2 — Detect your hardware

```bash
armtune detect
```

Output shows CPU model, cores, RAM, NUMA, and Arm feature flags
(NEON, DotProd, I8MM, SVE2, BF16). This fingerprint is stored with every
benchmark result so results are always reproducible.

### Step 3 — Pull a model from Hugging Face

```bash
armtune models list unsloth/Llama-3.2-1B-Instruct-GGUF
armtune models pull unsloth/Llama-3.2-1B-Instruct-GGUF --quant Q4_K_M
```

Models are cached under `models/`. You can also benchmark straight from the
repo without pulling first — see step 4.

### Step 4 — Benchmark

```bash
armtune benchmark \
  --profile configs/balanced.yaml \
  --repo unsloth/Llama-3.2-1B-Instruct-GGUF \
  --quant Q4_K_M,Q4_0,Q8_0 \
  --threads 1,2,4 \
  --concurrency 1,2
```

What happens for each combination:

- llama-server starts with that config (threads, quant, context, slots)
- 2 warmup requests (not measured), then 10 measured requests
- TTFT, P50/P95/P99, decode tok/s, prompt tok/s, queue delay, process RSS
- Arm Performix captures IPC, cache misses, branch mispredictions, memory bandwidth
- output quality is scored so fast-but-broken configs are rejected

### Step 5 — Get the recommendation

```bash
armtune recommend --latest --objective low-latency
```

Prints a ranked table and the winning config, plus:

```bash
llama-server -m models/....gguf -t 4 -c 2048 -np 1  # quantization: Q4_K_M
```

### Step 6 — Dashboard

```bash
armtune dashboard
```

Opens http://127.0.0.1:7860 with five tabs: Hardware, Sweeps, Performix,
Recommendation, and Hugging Face (pull + benchmark in one click).

## Where it works

| Environment | detect | benchmark | notes |
|---|---|---|---|
| GitHub Actions ARM64 runner | yes | yes | free, native, 4 cores / 15 GB |
| AWS Graviton (r/m/c/g8g) | yes | yes | script works as-is |
| Azure Cobalt (Dpsv6/Dplsv6) | yes | yes | script works as-is |
| Google Axion (C4A) | yes | yes | script works as-is |
| Ampere Altra servers | yes | yes | script works as-is |
| Any Arm64 Linux (Raspberry Pi 5, etc.) | yes | yes | smaller search space |
| Windows / macOS x86 | yes | no | development only, mock adapter for testing |

## Publishing to PyPI

The package is PyPI-ready (setuptools, wheel + sdist build, twine-checked):

```bash
pip install build twine
python -m build
python -m twine upload dist/*
```

Until then, install directly from GitHub:

```bash
pip install git+https://github.com/luxmikant/Arm-Tune.git
```

Note: the llama.cpp server binary is intentionally NOT bundled — it is a
separate build (see `scripts/build-llama-cpp.sh`) so users keep their own
optimized runtime builds.

## Frequently asked questions

**Do I need a GPU?**
No. The Cloud AI track of the challenge is explicitly about CPU-based
inference on Arm servers. GPU support is a planned extension.

**My machine is not Arm64. Can I still try it?**
Yes — `detect`, tests, and the mock benchmark work anywhere. Real
benchmarks run on the Arm64 CI workflow or an Arm server.

**Is the model bundled?**
No. You pull GGUF files from Hugging Face (they stay in your `models/`
cache). ArmTune is the measurement layer, not a model distributor.

**Does it replace llama.cpp / vLLM?**
No. It is the optimization and observability layer around them.
You keep using your runtime — ArmTune tells you how to configure it.

**What does the "launch command" do?**
It is the exact `llama-server` command ArmTune recommends for your
hardware. Paste it into your deployment (or Docker entrypoint).

**Can I use it in CI to catch performance regressions?**
Yes. The benchmark workflow produces JSON/CSV artifacts; commit them or
compare across runs. This is the reproducibility story.
