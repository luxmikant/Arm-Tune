# 3-Minute Demo Video Script — ArmTune Serve

> Target: 2:40. Record at 1080p. Terminal + browser only. No music with
> copyright; a quiet synth bed or silence. Show the product on ARM64 —
> use the GitHub Actions log or an SSH session to a real Arm host.

## Beat sheet

| Time | Screen | Narration |
|---|---|---|
| 0:00-0:15 | Product site hero (arm-tune.vercel.app) | "Every LLM deployment on an Arm server hides the same question: which quantization, how many threads, what concurrency? The answer is a hardware fact — and today it's usually guesswork." |
| 0:15-0:30 | Site: pipeline section | "ArmTune Serve is an autotuner for LLM serving on Arm. It measures your exact machine and hands you the launch command — with evidence." |
| 0:30-0:50 | Terminal (ARM64): `armtune detect` | "First, it fingerprints the CPU — Neoverse, NEON, I8MM, SVE2, cores, memory, NUMA. This capability map drives everything downstream, so the same tool works on Graviton, Cobalt, Axion or Ampere." |
| 0:50-1:20 | Dashboard Console tab: search "llama 3.2 1b", pick repo, model card appears, tick Q4_K_M | "No copy-pasting from Hugging Face. Search, inspect the model card, pick quantizations — file sizes included — right here." |
| 1:20-1:50 | Console: set threads 1,2,4 → Run → streaming terminal log (show llama-server spawning, KleidiAI line in evidence) | "Each configuration spawns a real llama-server — the exact binary we compiled with Arm KleidiAI kernels. Prompts run through the instruct chat template, so quality is scored, not assumed. While inference runs, Arm Performix captures hardware counters." |
| 1:50-2:15 | Sweeps tab: charts.png / sweeps.png | "The sweep answers the real questions: where do extra threads stop helping? Which quantization wins *here* — and every recommendation must pass the quality gate." |
| 2:15-2:35 | Recommendation tab: launch command, copy button | "The output isn't a PDF. It's a ranked table, the reasoning, and the exact command to deploy. That's the whole product: measurement to production in one step." |
| 2:35-2:50 | GitHub: Actions run + evidence dir; end card with repo URL | "Everything you saw runs on free GitHub ARM64 runners and is reproducible with one click. ArmTune Serve — tune every token to the architecture it runs on." |

## Recording checklist

- [ ] Dashboard running on the ARM64 host (or record the Actions log side-by-side)
- [ ] Real results loaded in Sweeps/Recommendation tabs (run benchmark first!)
- [ ] Terminal font ≥ 14pt, dark background
- [ ] Say "Arm Performix" and "KleidiAI" out loud at least once (judges listen for it)
- [ ] End card: github.com/luxmikant/Arm-Tune + arm-tune.vercel.app
- [ ] Upload unlisted → verify it plays → set public → paste link in Devpost form
