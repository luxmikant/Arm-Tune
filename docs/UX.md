# Developer-Tool UX Principles for ArmTune Serve

Why the product is shaped the way it is, and which patterns from the best
developer tools each part borrows.

## 1. The problem with CLI-only flows

The classic flow requires context switching:

```text
open huggingface.co -> search -> read card -> copy repo id ->
open terminal -> paste -> remember quant names -> run -> read JSON
```

Every step leaks time and invites typos. Great developer tools remove the
copy-paste loop: **one surface, guided steps, live feedback**.

## 2. Patterns borrowed from category leaders

| Tool | Pattern we borrowed |
|---|---|
| Vercel dashboard | deployment console with live streaming logs and a clear final URL |
| Railway | step-by-step provisioning wizard; terminal that streams every command |
| Replicate | model cards with metadata and one-click "run" from the card |
| Hugging Face hub | search-driven model discovery; license/downloads visible before use |
| Supabase | CLI + web console parity — every CLI command has a GUI equivalent |
| Grafana | dark theme, dense but readable metrics tables, color-coded status |
| pnpm/brew/turborepo | fast, monospaced terminal aesthetics; short punchy commands |

## 3. ArmTune's answer: the Console

The dashboard's **Console tab** is a guided pipeline:

```text
1. Search Hugging Face (live, in-UI) -> matching repos with download counts
2. Inspect the model card (license, likes, tags, pipeline) before deciding
3. Pick quantizations from a checkbox list (sizes shown, defaults smart)
4. Configure sweeps (threads, concurrency) with sensible defaults
5. Run -> terminal streams the real CLI output line by line
6. Refresh -> charts and recommendation appear in the other tabs
```

No copy-paste between HF and the CLI. The CLI stays for CI and scripting;
the Console is the human surface. That is the Supabase principle:
**CLI + GUI parity, not replacement.**

## 4. Principles the design follows

1. **Progressive disclosure.** Hardware is detected automatically; the user
   only sees choices that matter.
2. **Live feedback.** The terminal streams output — waiting is visible, not
   silent.
3. **Defaults that work.** Q4_K_M/Q4_0/Q8_0, threads 1,2,4 — opinionated but
   editable.
4. **Decision support, not decision making.** The model card shows license
   and downloads before the user picks; the recommendation explains its
   reasoning and always leaves a deployable command.
5. **Dark, monospaced, calm.** The theme matches what backend developers
   already expect from Grafana and terminal tools.
6. **Artifacts over prose.** Every run leaves JSON/CSV/MD/charts the team can
   diff in CI.

## 5. Future: a hosted console

The natural next step is a hosted web console (Next.js frontend + runner
backend) that drives benchmarks on remote Arm instances. This requires
persistent Arm hardware and safe job isolation — out of scope for the
hackathon, but the Console tab already encodes the interaction model the
hosted version would reuse.
