# Installing ArmTune Serve with pip

The easiest way to install ArmTune Serve is from PyPI with `pip`.

## Quick install (PyPI)

```bash
pip install armtune-serve
```

Verify:

```bash
armtune --version
```

Expected output:

```text
armtune v0.1.0
```

## Optional extras

The dashboard (Gradio Console) is an optional extra:

```bash
pip install "armtune-serve[dashboard]"
```

Development dependencies (tests + lint) for contributors:

```bash
pip install "armtune-serve[dev]"
```

## Install from GitHub instead (if PyPI is not yet available)

```bash
pip install git+https://github.com/luxmikant/Arm-Tune.git

# with the dashboard:
pip install "armtune-serve[dashboard] @ git+https://github.com/luxmikant/Arm-Tune.git"
```

## Upgrade

```bash
pip install --upgrade armtune-serve
```

## What pip installs

The pip package contains the Python control plane: the `armtune` CLI
(detect, benchmark, recommend, report, dashboard, models) plus all Python
dependencies (psutil, pydantic, httpx, huggingface-hub, matplotlib, etc.).

It intentionally does **not** bundle:

- the `llama-server` inference binary (platform-specific, built separately);
- the Arm Performix CLI (downloaded separately);
- model weights (pulled from Hugging Face on demand).

## One-time runtime setup on Arm64 Linux

These steps install the platform-specific pieces the benchmark needs. Run
them once after `pip install`:

```bash
# 1. llama.cpp with Arm-optimized kernels (KleidiAI + native build)
bash scripts/build-llama-cpp.sh

# 2. Arm Performix CLI (hardware counters) — optional but recommended
bash scripts/install-performix.sh
```

> The scripts live in the GitHub repository. On a fresh machine without the
> repo, download them first:
>
> ```bash
> curl -O https://raw.githubusercontent.com/luxmikant/Arm-Tune/main/scripts/build-llama-cpp.sh
> curl -O https://raw.githubusercontent.com/luxmikant/Arm-Tune/main/scripts/install-performix.sh
> chmod +x build-llama-cpp.sh install-performix.sh
> ```

After the build, point ArmTune at the optimized server:

```bash
export ARMTUNE_LLAMA_SERVER=llama.cpp/build-arm-opt/bin/llama-server
```

## Try it

```bash
armtune detect
armtune models list unsloth/Llama-3.2-1B-Instruct-GGUF
armtune benchmark \
  --repo unsloth/Llama-3.2-1B-Instruct-GGUF \
  --quant Q4_K_M,Q4_0 \
  --threads 1,2,4
armtune recommend --latest
```

## Dashboard (GUI console)

```bash
armtune dashboard
```

Opens the guided console at http://127.0.0.1:7860 — live Hugging Face model
search, model-card inspection, quantization picker, streaming terminal.

## Platform support

| Environment | Works | Notes |
|---|---|---|
| Arm64 Linux (Graviton/Cobalt/Axion/Ampere/CI) | Full | real benchmarks |
| GitHub Actions `ubuntu-24.04-arm` | Full | one-click workflow |
| Windows / macOS x86 | Partial | `detect`, tests, mock benchmark; real inference needs Arm64 |

## Troubleshooting

**`armtune: command not found`**
The pip script directory is not on PATH. Check with
`python -m pip show armtune-serve`, then run `python -m armtune.cli --help`
as a fallback, or add the scripts dir to PATH:
`python -m site --user-site`.

**Benchmark reports using the mock adapter**
The factory falls back to a mock when no `llama-server` binary is found.
Install/build it (see above) or set `ARMTUNE_LLAMA_SERVER` to the binary
path. The CLI prints a loud warning when the mock is used.

**Hugging Face download needs a token (gated models)**
```bash
export HF_TOKEN=hf_...
```

## Verify the installed version

```bash
python -c "import armtune; print(armtune.__version__)"
```