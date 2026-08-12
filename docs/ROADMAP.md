# ArmTune Serve — ROADMAP

## Current status: M1-M4 complete

| Milestone | Status | Evidence |
|-----------|--------|----------|
| M1 — Native ARM64 foundation | Done | Package installs, `detect` CLI works, ARM64 CI workflow |
| M2 — Baseline benchmark | Done | Benchmark orchestrator with mock adapter, metrics collection |
| M3 — Optimization sweeps | Done | Thread sweep, concurrency sweep, quantization comparison via profiles |
| M4 — Recommendation & reporting | Done | Recommendation engine (4 objectives), report generator (JSON/CSV/MD/charts) |

## What's broken / needs fixing

1. **Benchmark workflow exit code 1** — partly caused by duplicate `Arm-Tune/` nested repo.
   Fixed: removed from tracking, actions updated to v5/v6, workflow made resilient with `continue-on-error`.
2. **No artifacts produced** — results directory wasn't created before benchmark runs.
   Fixed: `mkdir -p results` added as first step.
3. **File duplication** — `Arm-Tune/` was a nested repo clone.
   Fixed: added to `.gitignore`, will be deleted manually.
4. **Git exit 128** — caused by nested `.git` directory.
   Fixed: excluded from tracking.

## Immediate next steps

1. **Run on real ARM64 runner** — push to GitHub, watch `test-arm64.yml` run
2. **Test with small model** — use Qwen2.5-0.5B or TinyLlama to fit runner RAM
3. **Validate Performix** — once on ARM64, verify the CLI downloads and profiles correctly
4. **Polish reports** — ensure charts render, CSV is clean

## Remaining milestones

### M5 — Dashboard (medium priority)

Streamlit dashboard showing:
- Hardware profile
- Live CPU/memory metrics
- Config comparison table
- Recommended configuration card

### M6 — Arm server validation (high priority)

- Request access from Works on Arm / Open Source Lab
- Test on persistent Graviton/Cobalt/Axion server
- Run larger models (7B, 13B)
- Validate NUMA and memory bandwidth analysis

### M7 — CPU-GPU extension (future)

- GPU detection (PCIe, Vulkan, CUDA MIG)
- GPU utilization and memory tracking
- CPU-GPU pipeline balance measurement
- Heterogeneous deployment recommendations

## Known limitations

- Mock adapter used for local testing (no real model on CI yet)
- Performix requires ARM64 hardware — tested on CI but not yet on persistent server
- GitHub Actions runner has limited CPU/RAM — large models may not fit
- Charts require matplotlib (optional dependency)
