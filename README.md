# ArmTune Serve

> Arm64 LLM inference optimization toolkit powered by **Arm Performix**.
>
> Finds and demonstrates the best deployment configuration — model quantization,
> CPU threads, request concurrency — then serves it with reproducible
> benchmark evidence validated by Arm performance hardware counters.

---

## What it solves

Running an LLM on an Arm64 CPU server involves many choices (quantization
level, thread count, concurrency, caching). There is no universal answer — the
best config on a 4-core Ampere VM differs from a 32-core Graviton server.

ArmTune Serve automates the exploration by:

1. **Detecting hardware** — architecture, CPU model, cores, memory, NUMA
2. **Profiling with Arm Performix** — hardware performance counters (cache
   misses, branch predictions, IPC, memory bandwidth) provide exact Arm-native
   evidence for every configuration
3. **Benchmarking against llama.cpp** — TTFT, tokens/sec, P50/P95 latency,
   quality scores across config variants
4. **Recommending** the best configuration for your objective (low-latency,
   high-throughput, low-memory, balanced)

## Why Arm Performix

Arm Performix is Arm's free performance analysis toolkit for Neoverse
platforms. It captures CPU microarchitecture-level metrics that generic
benchmarks miss:

- **Cache behavior** — L1/L2/L3 hit rates, cache-line utilization
- **Branch prediction** — mispredict rates, indirect branch efficiency
- **Instruction throughput** — IPC, stall cycles, backend/frontend bound
- **Memory bandwidth** — read/write bandwidth, NUMA locality
- **Vectorization** — NEON/SVE utilization

These insights let ArmTune Serve explain *why* one config outperforms another,
not just *that* it does.

## CLI

```bash
armtune detect                      # Show hardware info
armtune benchmark --profile balanced # Run full benchmark sweep
armtune recommend --objective low-latency  # Get recommendation
armtune report --latest             # Generate report (JSON + CSV + MD + charts)
```

## Quick start (GitHub Actions)

```yaml
runs-on: ubuntu-24.04-arm  # native ARM64
steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with: { python-version: "3.12" }
  - run: pip install -e .
  - run: bash scripts/install-performix.sh
  - run: armtune detect
  - run: armtune benchmark --profile balanced
  - run: armtune recommend --objective low-latency
  - run: armtune report --latest
```

## Architecture

```text
┌───────────────────────────────────────────────────────────┐
│  armtune CLI                                              │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌────────┐ ┌─────┐ │
│  │ detect  │→│ benchmark │→│ analyze  │→│ report │      │ │
│  └────┬────┘ └─────┬─────┘ └────┬─────┘ └───┬────┘      │ │
│       │            │            │            │            │ │
│       ▼            ▼            ▼            ▼            │ │
│  Hardware      llama.cpp    Recommendation  JSON/CSV/MD   │ │
│  Detection     (runtime)    Engine          Charts        │ │
│       │            │                                      │ │
│       └────────────┴────────┐                              │ │
│                             ▼                              │ │
│                    Arm Performix CLI                       │ │
│                  (Hardware counter profiling)              │ │
└───────────────────────────────────────────────────────────┘
```

## Metrics collected

| Metric | Source |
|--------|--------|
| TTFT, tokens/sec, P50/P95 | llama.cpp (our collector) |
| Peak RAM, CPU utilization | psutil (our collector) |
| Quality score | Structured output validator |
| Cache misses, IPC, branch mispredicts | **Arm Performix** |
| Memory bandwidth, NUMA locality | **Arm Performix** |
| NEON/SVE utilization | **Arm Performix** |

## Project structure

```text
armtune/
├── cli.py              # Typer CLI
├── config.py           # Pydantic config models
├── detect/             # Hardware detection
├── performix/          # Arm Performix integration
├── runtime/            # llama.cpp adapter
├── benchmark/          # Orchestrator + metrics
├── analyze/            # Recommendation + quality scorer
└── report/             # Reporting (JSON/CSV/MD/charts)
configs/                # YAML profiles
prompts/                # Evaluation workload
scripts/                # Install/setup scripts
tests/                  # Unit tests
.github/workflows/      # CI/CD (ubuntu-24.04-arm)
```

## License

MIT — see [LICENSE](LICENSE).
