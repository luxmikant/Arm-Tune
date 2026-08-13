# ArmTune Serve — Use-Case Justification

Why this project matters, who it helps, and how to defend the claim that
CPU-side optimization on Arm matters — even in a GPU world.

## The problem (from a developer's day)

```text
You: "My LLM endpoint on my Arm VM is too slow / costs too much.
     Which quantization? How many threads? Should I add concurrency?"
Docs: "llama.cpp has 15 flags. Here are benchmarks for an 8-core x86
     machine and a 32-core Graviton. Good luck."
You: spend a day guessing flags, keeping results in a scratch notebook,
     unable to prove your final config is better than the default.
```

The configuration search space is small but real: 3 quantizations x
4 thread counts x 2 concurrency levels = 24 runs, each needing the
same workload, same warmup, same output limits, and a quality check —
otherwise you are comparing noise.

ArmTune automates exactly that loop and records everything.

## Who this helps

| User | What they get |
|---|---|
| Developer deploying an LLM API on Arm cloud | measured config + launch command, no flag guessing |
| Platform/SRE team | reproducible CI benchmarks to catch regressions and right-size instances |
| Developer evaluating "move from x86 to Graviton/Axion" | before/after evidence on identical workload |
| ML engineer quantizing a model | speed/quality Pareto across Q4_0, Q4_K_M, Q8_0 |
| Hackathon judge / reviewer | one artifact: report + charts + hardware counters |

## The core claim (and how to defend it)

> **Claim:** On a fixed Arm64 server, hardware-aware measurement identifies
> an inference configuration that improves latency, throughput, or memory
> while preserving quality.

**Defense 1 — The CPU is never idle, even with a GPU.**
Tokenization, prefill scheduling, request orchestration, KV-cache management,
memory bandwidth, and CPU-offloaded layers all run on the CPU. On Arm servers
— chosen precisely because they are cost-efficient per core — a misconfigured
CPU side wastes the money you saved by choosing Arm.

**Defense 2 — Arm-specific kernels change the answer.**
A llama.cpp built with KleidiAI + `-mcpu=native` uses NEON/DotProd/I8MM/SVE
instructions that a generic build does not. The best thread count and the best
quantization differ between the two builds. You can only know by measuring —
which is exactly what the generic-vs-optimized benchmark does.

**Defense 3 — One size does not fit all Arm servers.**
A 4-core Neoverse-N2 VM (free CI runner), a Graviton3 with SVE-256, and an
Axion V2 differ in ISA features, memory bandwidth, and NUMA. ArmTune detects
the capability fingerprint and searches accordingly, instead of assuming
"Graviton" or "Axion" means one thing.

**Defense 4 — Speed without quality is cheating.**
Every recommended config passes a quality gate (structured output validated
against expected labels). The recommendation is a speed/quality Pareto pick,
so a fast-but-broken config can never win.

**Defense 5 — The output is deployable, not a PDF.**
The final artifact is a copy-paste `llama-server` command plus JSON/CSV for
your own tooling. The benchmark harness is reusable for any GGUF model.

## Concrete before/after scenario (to fill with real CI numbers)

```text
Hardware:  ARM64 runner, Neoverse-N2, 4 cores, 15 GB RAM
Workload:  10 support-ticket classification requests, 256-token outputs

Baseline:
  generic llama.cpp build, Q8_0, default 4 threads, concurrency 1
  TTFT = A s | decode = B tok/s | P95 = C s | RSS = D MB | quality = E

Optimized (ArmTune recommended):
  KleidiAI native build, Q4_K_M, T threads, concurrency N
  TTFT = A' s | decode = B' tok/s | P95 = C' s | RSS = D' MB | quality = E'

Result: decode +X%, TTFT -Y%, RAM -Z%, quality within threshold.
Evidence: results.json + report.md + charts + Arm Performix counters.
```

Fill in A/B/C/D with the CI artifact and this table becomes the Devpost
"Functionality / Output" section.

## Mapping to the challenge criteria

| Criterion | ArmTune's answer |
|---|---|
| Model size | quant sweep measures on-disk + peak RSS reduction |
| Model quality | quality gate + expected-label scorer |
| Model speed | TTFT + decode tok/s per config |
| Inference server speed | P50/P95/P99 + queue delay + concurrency sweep |
| Developer experience | one CLI, Gradio dashboard, HF pull, launch command export |
| Arm-specific optimization | Arm Performix hardware counters + KleidiAI native build evidence |

## What to say to a skeptic

> "Quantization and thread count are not portable folklore — they are
> hardware facts. ArmTune turns your Arm server's ISA features and
> performance counters into a measured configuration, the same way a
> compiler autotuner picks instruction scheduling. You get a deployable
> command and the evidence for why it wins."
