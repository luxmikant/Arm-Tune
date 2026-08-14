import type { Metadata } from "next";
import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/Chrome";

export const metadata: Metadata = {
  title: "Docs | ArmTune Serve",
  description:
    "ArmTune Serve documentation: install, benchmark, understand the recommendation, and publish evidence.",
};

export default function DocsPage() {
  return (
    <>
      <div className="noise" aria-hidden="true" />
      <SiteHeader />
      <main className="docs-layout shell">
        <aside className="docs-sidebar">
          <p className="eyebrow">Documentation</p>
          <h1>Run the loop.</h1>
          <p>From an empty Arm64 machine to a measured deployment command.</p>
          <nav className="docs-nav">
            <a href="#quick-start">Quick start</a>
            <a href="#benchmark">Benchmark</a>
            <a href="#cpu">CPU tuning</a>
            <a href="#performix">Performix</a>
            <a href="#quality">Quality gate</a>
            <a href="#results">Results</a>
            <a href="#release">Release</a>
          </nav>
          <a
            className="side-source"
            href="https://github.com/luxmikant/Arm-Tune/blob/main/docs/USAGE.md"
            target="_blank"
            rel="noreferrer"
          >
            Read source docs <span>↗</span>
          </a>
        </aside>
        <article className="docs-content">
          <div className="docs-hero">
            <p className="eyebrow">
              <span className="pulse-dot" /> ArmTune Serve / v0.1
            </p>
            <h2>A measured answer to a hardware-specific question.</h2>
            <p>
              Use these commands on native Arm64 Linux. Windows and x86 machines
              can run tests and the dashboard, but real inference evidence must
              come from the Arm target.
            </p>
          </div>

          <section id="quick-start" className="doc-section">
            <span className="doc-kicker">01 / QUICK START</span>
            <h2>Install and detect.</h2>
            <p>
              Start with the Python control plane, then install the
              platform-specific runtime and profiler.
            </p>
            <pre>{`git clone https://github.com/luxmikant/Arm-Tune.git
cd Arm-Tune
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
bash scripts/install-performix.sh
bash scripts/build-llama-cpp.sh
armtune detect`}</pre>
            <div className="callout">
              <strong>What to look for</strong>
              <span>
                The output should identify <code>aarch64</code>, the CPU model,
                physical cores, memory, and features such as NEON, I8MM, SVE or
                SVE2.
              </span>
            </div>
          </section>

          <section id="benchmark" className="doc-section">
            <span className="doc-kicker">02 / BENCHMARK</span>
            <h2>Pull a model, sweep the real choices.</h2>
            <p>
              The model connector lists GGUF variants and caches selected files
              locally. The benchmark keeps prompts, warmup, seed and output
              limits constant.
            </p>
            <pre>{`armtune models list unsloth/Llama-3.2-1B-Instruct-GGUF

export ARMTUNE_LLAMA_SERVER=llama.cpp/build-arm-opt/bin/llama-server
armtune benchmark \\
  --profile configs/balanced.yaml \\
  --repo unsloth/Llama-3.2-1B-Instruct-GGUF \\
  --quant Q4_K_M,Q4_0,Q8_0 \\
  --threads 1,2,4 \\
  --concurrency 1,2`}</pre>
            <div className="inline-grid">
              <div>
                <strong>Model</strong>
                <span>GGUF quantization and size</span>
              </div>
              <div>
                <strong>Runtime</strong>
                <span>threads, batch threads, context</span>
              </div>
              <div>
                <strong>Server</strong>
                <span>slots, queue, P95/P99</span>
              </div>
            </div>
          </section>

          <section id="cpu" className="doc-section">
            <span className="doc-kicker">03 / CPU TUNING</span>
            <h2>Why Arm-specific settings matter.</h2>
            <p>
              Prefill and decode are different workloads. Prefill is
              matrix-heavy and responds to batch settings; decode repeatedly
              touches weights and KV state and is sensitive to memory bandwidth,
              cache behavior and thread oversubscription.
            </p>
            <div className="doc-table">
              <div className="table-row table-head">
                <span>Setting</span>
                <span>What it changes</span>
                <span>What to measure</span>
              </div>
              <div className="table-row">
                <span>
                  <code>-t</code> threads
                </span>
                <span>decode parallelism</span>
                <span>decode tok/s, P95</span>
              </div>
              <div className="table-row">
                <span>
                  <code>-tb</code> batch threads
                </span>
                <span>prefill parallelism</span>
                <span>prompt tok/s, TTFT</span>
              </div>
              <div className="table-row">
                <span>quantization</span>
                <span>weight size and kernel path</span>
                <span>RSS, quality, tok/s</span>
              </div>
              <div className="table-row">
                <span>concurrency</span>
                <span>server slots and queueing</span>
                <span>aggregate tok/s, P95</span>
              </div>
              <div className="table-row">
                <span>context / KV cache</span>
                <span>memory per request</span>
                <span>RSS, feasibility</span>
              </div>
            </div>
            <p className="doc-linkline">
              ArmTune builds a generic baseline and a KleidiAI/native Arm
              variant. The point is not to claim that every lower-bit model
              wins. The point is to measure which one wins here.
            </p>
          </section>

          <section id="performix" className="doc-section">
            <span className="doc-kicker">04 / ARM PERFORMIX</span>
            <h2>Explain the win.</h2>
            <p>
              Arm Performix profiles the inference process while the workload is
              running. The report can connect application metrics to hardware
              signals.
            </p>
            <div className="counter-grid">
              <div>
                <strong>IPC</strong>
                <span>instructions per cycle</span>
              </div>
              <div>
                <strong>LLC</strong>
                <span>last-level cache misses</span>
              </div>
              <div>
                <strong>BR</strong>
                <span>branch misprediction</span>
              </div>
              <div>
                <strong>BW</strong>
                <span>memory read/write</span>
              </div>
            </div>
            <p>
              If a profiler command differs between Performix releases, ArmTune
              records the attempted command, version, stderr and status instead
              of presenting empty counters as success.
            </p>
          </section>

          <section id="quality" className="doc-section">
            <span className="doc-kicker">05 / QUALITY GATE</span>
            <h2>Speed without quality is cheating.</h2>
            <p>
              The reference workload asks for strict JSON. ArmTune scores
              structure, valid enums and agreement with expected labels. Any
              configuration below the quality threshold is excluded from
              recommendations — no matter how fast it is.
            </p>
            <div className="callout">
              <strong>Scored fields</strong>
              <span>
                <code>summary</code>, <code>category</code>,{" "}
                <code>priority</code>, <code>recommended_action</code> — plus an
                expected-category correctness bonus.
              </span>
            </div>
          </section>

          <section id="results" className="doc-section">
            <span className="doc-kicker">06 / RESULTS</span>
            <h2>Read the recommendation.</h2>
            <p>
              Each run creates a timestamped directory under <code>results/</code>.
            </p>
            <pre>{`results/20260813_134346/
├── results.json       # complete machine-readable record
├── results.csv        # spreadsheet-friendly comparison
├── report.md          # shareable written report
├── charts.png         # core metric comparison
├── sweeps.png         # thread/concurrency curves
├── performix.png      # Arm counter comparison
└── improvements.png   # relative change vs baseline`}</pre>
          </section>

          <section id="release" className="doc-section">
            <span className="doc-kicker">07 / RELEASE</span>
            <h2>Use it as a package or a workflow.</h2>
            <p>
              The Python control plane is packaged as{" "}
              <code>armtune-serve</code>. A trusted-publishing workflow is
              included for PyPI. The runtime binary and model weights remain
              separate, platform-specific artifacts.
            </p>
            <pre>{`python -m pip install armtune-serve
armtune --version
armtune dashboard`}</pre>
            <div className="callout">
              <strong>Publishing responsibly</strong>
              <span>
                Publish only after replacing placeholder benchmark values with
                real artifacts. Never upload gated model weights or credentials.
              </span>
            </div>
          </section>

          <div className="docs-footer">
            <a
              className="button button-primary"
              href="https://github.com/luxmikant/Arm-Tune"
              target="_blank"
              rel="noreferrer"
            >
              Open repository <span>↗</span>
            </a>
            <Link className="button button-quiet" href="/">
              Back to product <span>→</span>
            </Link>
          </div>
        </article>
      </main>
      <SiteFooter />
    </>
  );
}
