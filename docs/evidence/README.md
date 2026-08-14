# ArmTune Serve — Benchmark Evidence

Real measurements captured by the public `Benchmark ARM64` GitHub Actions
workflow on a native ARM64 runner. Nothing in this directory is hand-edited.

## Provenance

| Field | Value |
|---|---|
| Workflow run | https://github.com/luxmikant/Arm-Tune/actions/runs/31790177140 |
| Runner | GitHub `ubuntu-24.04-arm` |
| CPU | Neoverse-N2, 4 physical cores, aarch64 |
| Memory | 15.6 GB |
| Arm features | NEON, DotProd, I8MM, SVE, SVE2, BF16 |
| Model | unsloth/Llama-3.2-1B-Instruct-GGUF |
| Runtime | llama.cpp `llama-server` (commit 885c5bb), chat-template completion |
| Workload | 5 support-ticket prompts, 1 warmup + 6 measured requests, 128 max tokens, temp 0, seed 42+i |
| Quality gate | strict JSON + expected-category agreement, threshold 0.5 |

## Headline results (tuned run, 20260814_100451)

| Metric | Q4_K_M · 4 threads | Q4_0 · 4 threads | Change |
|---|---:|---:|---:|
| Decode throughput | 26.1 tok/s | 33.0 tok/s | +26% |
| Time to first token | 0.45 s | 0.33 s | -27% |
| P95 latency | 2.52 s | 1.91 s | -24% |
| Peak process RSS | 1701 MB | 1616 MB | -5% |
| Quality score | 1.00 | 1.00 | gate held |

Thread sweep (Q4_K_M, tuned run): 1 thread 8.1 tok/s -> 2 threads 15.1 tok/s ->
4 threads 28.1 tok/s (3.5x).

Generic vs KleidiAI builds were within noise for short-prompt decode on this
4-core N2 (27.3 vs 26.1 tok/s) — expected, since decode is memory-bound GEMV;
KleidiAI's i8mm kernels accelerate quantized GEMM (prefill).
The KleidiAI build flag was verified in a follow-up run (31791857839):
`GGML_CPU_KLEIDIAI:BOOL=ON` in CMakeCache, and the rerun reproduced the
numbers (28.5 vs 33.5 tok/s). See `docs/evidence/README-notes.md` for the
full reading.

## Directories

| Directory | Contents |
|---|---|
| `baseline-generic/` | generic llama.cpp build, configs/baseline.yaml |
| `tuned-armopt/` | KleidiAI + `-mcpu=native` build, configs/balanced.yaml |
| `hardware-inventory.txt` | full runner inventory (lscpu, cpuinfo, NUMA, meminfo) |
| `hardware.json` | `armtune detect --json` output |

## Reproduce

```bash
gh workflow run "Benchmark ARM64" --repo luxmikant/Arm-Tune \
  -f profile=balanced \
  -f repo=unsloth/Llama-3.2-1B-Instruct-GGUF \
  -f quant=Q4_K_M,Q4_0 -f threads=1,2,4 -f concurrency=1
```

Then download the artifact from the finished run.
