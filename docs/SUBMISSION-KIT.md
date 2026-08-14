# ArmTune Serve — Submission Kit

Everything for the Devpost form, copy-paste ready. Track: **Cloud AI**.

---

## 1. Demo video — full narration script (2:45)

> Read this aloud while recording. Screen actions are in brackets.
> Upload to YouTube (unlisted → verify → public), paste the link in the form.

### The one-liner (for the video description + Devpost)

"ArmTune Serve is the autotuner for LLM serving on Arm: it measures your exact
CPU, sweeps the configurations, and hands you the launch command — with
hardware-counter evidence."

### Beat 1 — The problem (0:00-0:25)

**[Screen: terminal with a long llama.cpp flag list, then the product site hero]**

> "Every developer who deploys an LLM on an Arm server faces the same wall.
> Which quantization? How many threads? What concurrency? The answer is a
> hardware fact — but today it's folklore. You guess, you benchmark by hand,
> you can't prove your config is better than the default."

**[Screen: 24-combination matrix text]** 

> "On this four-core Neoverse machine, just three quantizations, four thread
> counts and two concurrency levels is twenty-four combinations — each needing
> the same prompts, the same warmup, the same seeds, and a quality check.
> Nobody does that by hand. So we built the thing that does."

### Beat 2 — What it is (0:25-0:50)

**[Screen: website pipeline section — four steps]**

> "ArmTune Serve is an autotuner for LLM serving on Arm. One command: it pulls
> a GGUF model from Hugging Face, fingerprints the CPU — NEON, I8MM, SVE2,
> cores, NUMA — then runs a controlled sweep on a real llama-server process."

**[Screen: `armtune detect` output on the ARM64 host]**

> "And because it measures, not assumes, every result carries evidence: TTFT,
> decode speed, P95, memory — and Arm Performix hardware counters captured
> while inference runs. Any configuration that breaks output quality is
> rejected, no matter how fast it is."

### Beat 3 — The console demo (0:50-1:30)

**[Screen: dashboard Console tab]**

> "But you never have to touch a flag. The console is a guided pipeline: search
> Hugging Face right here, inspect the model card, tick the quantizations —
> file sizes included — and press run. The terminal streams every step."

**[Screen: console streaming log — llama-server spawning, benchmark progress]**

> "Each configuration launches a real llama-server built with Arm KleidiAI
> kernels. Look at the thread sweep: one thread, eight tokens per second. Two
> threads, fifteen. Four threads, twenty-eight. That's a three-and-a-half-x
> difference found by measurement, not by reading a blog post."

### Beat 4 — The evidence (1:30-2:10)

**[Screen: website evidence section — measured bars +26% / -27% / -24%]**

> "Here's the headline from our public CI run on GitHub's ARM64 runners: moving
> from Q4_K_M to Q4_0 — a different quantization, same model — gives
> twenty-six percent more throughput, twenty-seven percent lower time to first
> token, twenty-four percent better P95 latency, and five percent less memory.
> Output quality held at one hundred percent."

**[Screen: GitHub Actions run page + docs/evidence/]**

> "And this is the part we're proudest of: every number was produced by a
> public workflow anyone can re-run with one click. No private GPUs, no
> hand-run experiments. The JSON, CSV, charts and report are committed to the
> repository."

### Beat 5 — The output + close (2:10-2:45)

**[Screen: recommendation tab with launch command]**

> "The output isn't a PDF. It's a ranked table, the reasoning, and the exact
> command to deploy — `llama-server`, four threads, Q4_0, one slot."

**[Screen: end card — repo URL + site URL]**

> "ArmTune Serve: tune every token to the architecture it runs on. The source
> is MIT-licensed at the link on screen. Thanks for watching."

### Recording rules (from the challenge)

- Under 3 minutes — this script is 2:45 with pauses.
- Must show the project running on Arm64 — the Actions log or an SSH session.
- No copyrighted music or trademarks. Silence or a simple original synth bed.
- Public on YouTube/Vimeo/Youku before pasting the link.

---

## 2. Devpost — "About the project" (Markdown + LaTeX)

> Paste into the text description. Replace nothing — all values are real.

## Inspiration

Every developer deploying an LLM on an Arm cloud server hits the same wall:
the fastest configuration is a hardware fact, not folklore. Q4 versus Q8,
two threads versus four — the answer changes between a four-core Neoverse
and a sixty-four-core Graviton, and nobody hand-tests twenty-four
combinations with identical prompts, warmup, seeds, and a quality gate.
So we built the tool we wanted to exist: an autotuner for LLM serving on Arm.

## What it does

ArmTune Serve measures how an LLM actually behaves on your exact Arm64
machine, then hands you the deployment command. It pulls a GGUF model from
Hugging Face, fingerprints the CPU (NEON, I8MM, SVE2, cores, NUMA), runs a
controlled sweep on a real `llama-server` process built with Arm KleidiAI
kernels, captures Arm Performix hardware counters during inference, rejects
configurations below the quality threshold, and prints a copy-paste launch
command.

The recommendation problem we solve, formally: over the candidate
configuration space $C$ (quantization × threads × concurrency), we select

$$
c^* = \arg\max_{c \in C} \; s_{\text{obj}}(c)
\quad \text{subject to} \quad
q(c) \geq q_{\min} = 0.5
$$

where $s_{\text{obj}}$ is the objective score (latency, throughput, memory,
or balanced) and $q(c)$ is the structured-output quality of configuration
$c$. Without the constraint, a fast-but-broken config always wins.

## How we built it

The runtime is abstracted behind an adapter interface; the primary adapter
drives `llama-server` through its OpenAI-compatible API so we benchmark the
exact binary compiled with `GGML_CPU_KLEIDIAI=ON` and `-mcpu=native`, and
capture its startup evidence in every result. The CI pipeline builds generic
and KleidiAI variants, then runs the identical workload matrix on both. The
dashboard console provides a guided pipeline — live Hugging Face search,
model cards, streaming terminal — so no one copy-pastes repo IDs.

## Measured results (Neoverse-N2, 4 cores, 15.6 GB, GitHub ARM64 runner)

| Metric | Q4_K_M · 4 threads | Q4_0 · 4 threads | Change |
|---|---:|---:|---:|
| Decode tokens/sec | 26.1 | 33.0 | +26% |
| Time to first token | 0.45 s | 0.33 s | -27% |
| P95 latency | 2.52 s | 1.91 s | -24% |
| Peak process RSS | 1701 MB | 1616 MB | -5% |
| Quality score | 1.00 | 1.00 | gate held |

Thread sweep: 1 thread 8.1 tok/s → 2 threads 15.1 tok/s → 4 threads
28.1 tok/s (3.5×). Full artifacts are committed under `docs/evidence/`.

## Challenges we ran into

- The Arm Performix CLI subcommands vary by version — we built a transparent
  probe that records exactly what ran, so failures are never silent.
- Quality must be measurable or autotuning is meaningless: raw completions
  ramble, so prompts route through the instruct chat template and outputs are
  scored as strict JSON against expected labels.
- A silent fallback bug let CI produce mock numbers once; we caught it,
  added a regression test, and made the CLI refuse to be quiet about it.

## Accomplishments we're proud of

The whole pipeline runs on free, public, native-ARM64 infrastructure and any
claim in this write-up is regenerable with one click. And the honest finding
is the best part: on this hardware the winning move was quantization plus
thread count — not the kernel flag — because decode is memory-bound. The data
proved it. That is exactly what measurement tools are for.

## What we learned

On Arm, quantization choice is a kernel-fit question, not a size question.
Prefill and decode want different thread counts. Oversubscription shows up in
P95 before it shows up in the mean. And hardware counters turn "it's faster"
into "it's faster because IPC rose and LLC misses fell" — the difference
between a benchmark and an explanation.

## What's next

Pin exact Performix CLI flags, NUMA and affinity sweeps on larger instances,
LM-Eval-Harness scoring, a vLLM adapter, and the top-down layer this enables:
fleet scheduling on measured per-replica capacity curves instead of
CPU-utilization guesswork.

---

## 3. "Built with" tags (25 max — use exactly these)

1. python
2. llama.cpp
3. arm64
4. hugging-face
5. gguf
6. arm-performix
7. gradio
8. nextjs
9. react
10. vercel
11. github-actions
12. typer
13. pydantic
14. httpx
15. psutil
16. matplotlib
17. pandas
18. quantized-llm
19. inference-optimization
20. neoverse
21. aws-graviton
22. azure-cobalt
23. google-axion
24. open-source
25. mit-license

## 4. "Try it out" links

| Label | URL |
|---|---|
| Source code (GitHub) | https://github.com/luxmikant/Arm-Tune |
| Product site | https://arm-tune.vercel.app |
| Documentation | https://arm-tune.vercel.app/docs |
| Model card (Hugging Face) | https://huggingface.co/lshar/ARM-TUNE-CPU-INFERENCE-OPT |
| Benchmark workflow (one-click repro) | https://github.com/luxmikant/Arm-Tune/actions/workflows/benchmark-arm64.yml |
| Evidence artifacts | https://github.com/luxmikant/Arm-Tune/tree/main/docs/evidence |
