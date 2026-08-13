# ArmTune Serve — ROADMAP

## Current status (2026-08-13)

| Milestone | Status | Evidence |
|-----------|--------|----------|
| M1 — Native ARM64 foundation | Done | CI on `ubuntu-24.04-arm` (Neoverse-N2), `armtune detect` works |
| M2 — Baseline benchmark | Done | Real llama.cpp inference via LlamaServerAdapter, TTFT/tok-s/P50-P99/RSS |
| M3 — Optimization sweeps | Done | Threads, concurrency, quantization (HF), KleidiAI vs generic builds |
| M4 — Recommendation & reporting | Done | 4 objectives, quality gate, JSON/CSV/MD + 4 chart sets, launch command |
| M5 — Dashboard | Done | Gradio 5-tab app incl. one-click HF pull + benchmark |
| M6 — Arm server validation | Next | Persistent Arm server: NUMA/affinity, larger models, vLLM adapter, pin apx flags |
| M7 — CPU-GPU extension | Future | GPU detection, utilization, pipeline balance |

## Implemented feature set

- Hardware capability fingerprint (NEON/DotProd/I8MM/SVE2/BF16, cores, NUMA)
- Arm Performix integration (installer, concurrent capture, status-transparent probing)
- llama-server subprocess adapter with startup `system_info`/`CPU_KLEIDIAI` evidence
- Runtime auto-selection: llama-server → llama_cpp → mock
- Hugging Face connector (`models list/pull`, `--repo/--quant` benchmarking)
- Quality scorer with expected-label correctness bonus
- Recommendation engine with quality threshold
- Report generator: JSON, CSV, Markdown, charts.png, sweeps.png, performix.png, improvements.png
- Deployment command export from recommendations
- Gradio dashboard: Hardware / Sweeps / Performix / Recommendation / Hugging Face
- GitHub Actions: test-arm64.yml (always), benchmark-arm64.yml (dispatch/schedule)
- 25 offline unit tests, ruff clean

## Immediate next steps (hackathon deadline Aug 14, 4 PM PDT)

1. Trigger `Benchmark ARM64`; verify KleidiAI build and `apx` probe on runner
2. Save best artifact run to `docs/evidence/` and commit
3. Record <3 min demo video
4. Devpost submission: Overview / Functionality / Setup / repo / video
5. Set license visible in GitHub About section

## Known limitations

- Mock adapter is a fallback on machines without a model or llama-server
- Performix CLI flags are probed (candidate commands) until `apx --help` is captured
- CI runner is 4-core/15 GB — larger-model claims need M6 hardware
- vLLM adapter deferred (build requirements exceed runner capacity)
- Windows is development-only; benchmarking targets ARM64 Linux
