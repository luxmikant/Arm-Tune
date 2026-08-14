# ArmTune Serve — ROADMAP

## Current status (2026-08-14)

| Milestone | Status | Evidence |
|-----------|--------|----------|
| M1 — Native ARM64 foundation | Done | CI on `ubuntu-24.04-arm` (Neoverse-N2), `armtune detect` works |
| M2 — Baseline benchmark | Done | Real llama.cpp inference via LlamaServerAdapter (chat template, TTFT/tok-s/P50-P99/RSS) |
| M3 — Optimization sweeps | Done | Threads, concurrency, quantization (HF), KleidiAI vs generic builds |
| M4 — Recommendation & reporting | Done | 4 objectives, quality gate, JSON/CSV/MD + 4 chart sets, launch command |
| M5 — Dashboard | Done | Gradio Console: live HF search, model cards, streaming terminal |
| M6 — Arm server validation | Next | Persistent Arm server: NUMA/affinity, larger models, vLLM adapter, pin apx flags |
| M7 — CPU-GPU extension | Future | GPU detection, utilization, pipeline balance |

## Hackathon evidence pipeline

The public `Benchmark ARM64` workflow builds generic + KleidiAI llama.cpp on
the runner, downloads GGUF models from Hugging Face, runs the real
llama-server matrix, and uploads JSON/CSV/Markdown/chart artifacts. The
committed evidence lives in `docs/evidence/`.

A silent-fallback bug was caught during preparation: the adapter factory
honored `llama-server` on PATH but not the `ARMTUNE_LLAMA_SERVER` env var,
so CI briefly produced mock numbers. Fixed with a regression test and a loud
CLI warning — no mock result can masquerade as a measurement again.

## Implemented feature set

- Hardware capability fingerprint (NEON/DotProd/I8MM/SVE2/BF16, cores, NUMA)
- Arm Performix integration (installer, concurrent capture, status-transparent probing)
- llama-server subprocess adapter with startup `system_info`/`CPU_KLEIDIAI` evidence
- Chat-template benchmarking via `/v1/chat/completions` (real quality scoring)
- Hugging Face connector (`models list/pull`, live search, model cards, sizes)
- Quality scorer with expected-label correctness bonus
- Recommendation engine with quality threshold + launch command export
- Report generator: JSON, CSV, Markdown, 4 chart sets (incl. sweeps + Performix + improvements)
- Gradio Console (guided pipeline) + dark theme
- Next.js 16 product/docs site on Vercel, evidence-driven results section
- GitHub Actions: test-arm64.yml (always), benchmark-arm64.yml (dispatch/schedule)
- PyPI trusted-publishing workflow + release docs
- 31 offline unit tests, ruff clean

## Known limitations

- Mock adapter exists for dev; CI now guarantees it can't be selected silently
- Performix CLI flags are probed (candidate commands) until `apx --help` is captured
- CI runner is 4-core/15 GB — larger-model claims need M6 hardware
- vLLM adapter deferred (build requirements exceed runner capacity)
- Windows dev only; benchmarking targets ARM64 Linux
