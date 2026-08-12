# ArmTune Serve — REQUIREMENTS & SCORING

## Hackathon: Arm Create — AI Optimization Challenge

**Track:** Cloud AI
**Platform:** Arm Neoverse (AWS Graviton / Azure Cobalt / Google Axion / Ampere)
**Tool requirement:** Arm Performix

---

## Judging criteria mapping

### 1. Model size — Reduce size on disk or in memory

**ArmTune Serve approach:**
- Quantization format sweep (Q2_K → F16)
- Peak RAM measurement via psutil
- Disk size reported per model file
- `low-memory` profile optimizes for smallest footprint

**Evidence:** `results.csv` column `peak_ram_mb`, config comparison table

---

### 2. Model quality — Improve fine-tuning or output quality for a given model size

**ArmTune Serve approach:**
- Structured JSON quality scorer grades output correctness
- Validates: summary completeness, category accuracy, priority validity, recommendation clarity
- Quality threshold (0.5) prevents recommending fast-but-broken configs
- Balances quality vs speed in the `balanced` objective

**Evidence:** `results.csv` column `quality`, quality scores per request

---

### 3. Model speed — Improve tokens/sec, time-to-first-token, latency

**ArmTune Serve approach:**
- TTFT (time-to-first-token) measured per request
- Decode tokens/sec measured per request
- Aggregate tokens/sec measured for throughput
- Thread sweep finds optimal parallelism
- `low-latency` profile minimizes P50 latency

**Evidence:** `results.csv` columns `ttft_s`, `avg_tok_s`, `throughput_tok_s`

---

### 4. Inference server speed — Improve throughput, latency, P50/P95

**ArmTune Serve approach:**
- P50 and P95 latency measured
- Request concurrency sweep finds optimal in-flight requests
- `high-throughput` profile maximizes aggregate tokens/sec
- Concurrent request handling via ThreadPoolExecutor

**Evidence:** `results.csv` columns `p50_latency_s`, `p95_latency_s`

---

### 5. Developer experience — Improve tools, workflows, setup, documentation

**ArmTune Serve approach:**
- Single `armtune` CLI (Typer + Rich) — intuitive commands
- YAML profiles for configuration — no code changes needed
- `pip install -e .` for local dev
- Ready-to-run GitHub Actions workflows (`ubuntu-24.04-arm`)
- `scripts/install-performix.sh` — one-command setup
- `scripts/download-model.sh` — one-command model download
- 20 unit tests with clean lint (ruff)
- Comprehensive docs in `docs/`

**Evidence:** README, docs/, passing CI, clean ruff check

---

### 6. Arm-specific optimization — Implement optimizations for Arm

**ArmTune Serve approach:**
- **Arm Performix CLI integration** — first-class support for hardware counter profiling
- Reads `/proc/cpuinfo` for Arm-specific feature flags (NEON, SVE, etc.)
- NUMA topology detection via `lscpu` and `numactl`
- Performance counter data: IPC, cache hierarchy, branch prediction, memory bandwidth
- Bottleneck identification with Arm-specific recommendations
- GitHub Actions runs on native `ubuntu-24.04-arm` runners

**Evidence:** `performix/` module, `results.csv` Performix columns, Markdown report with bottleneck analysis

---

## Commitment to Arm Performix

Per the hackathon requirement, Arm Performix is integrated as a **core profiling
component** (not optional), with:

- Automatic download and install on ARM64 runners
- Runtime process attachment for hardware counter collection
- Structured output parsing with multi-schema compatibility
- Bottleneck scoring integrated into recommendation engine
- Detailed reporting with Perforfix-derived insights

---

## Quality threshold

Every recommended configuration must pass a quality check:

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| Quality score | >= 0.5 | Ensures output is valid JSON with correct fields |
| Successful requests | >= 80% | Ensures the runtime is stable |

Configs failing the quality threshold are excluded from recommendations.

---

## Reproducibility

Every benchmark run records:

| Metadata | Source |
|----------|--------|
| Architecture | `uname -m` |
| CPU model / cores | `/proc/cpuinfo` |
| Memory total / available | `free -h` |
| Kernel version | `uname -r` |
| Runtime version | `llama.cpp` version |
| Profile YAML | Checked into repo |
| Seed | Fixed per run (42 + offset) |
| Prompts | Fixed prompt set (`prompts/tickets.json`) |
