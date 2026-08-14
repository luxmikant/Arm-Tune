import Link from "next/link";
import { SiteFooter, SiteHeader } from "@/components/Chrome";

export default function HomePage() {
  return (
    <>
      <div className="noise" aria-hidden="true" />
      <SiteHeader />
      <main>
        <section className="hero shell">
          <div className="hero-copy">
            <p className="eyebrow">
              <span className="pulse-dot" /> Arm64 / CPU-first / Performix-powered
            </p>
            <h1>Tune every token to the architecture it runs on.</h1>
            <p className="hero-lede">
              ArmTune Serve turns an Arm cloud server&apos;s hardware fingerprint
              into a measured LLM deployment configuration. Less guesswork. More
              useful CPU time.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" href="/docs#quick-start">
                Start tuning <span>→</span>
              </Link>
              <a
                className="button button-quiet"
                href="https://github.com/luxmikant/Arm-Tune"
                target="_blank"
                rel="noreferrer"
              >
                View source <span>↗</span>
              </a>
            </div>
            <div className="hero-note">
              <span className="mini-rule" /> Built for Graviton, Cobalt, Axion,
              Ampere and native Arm64 CI.
            </div>
          </div>
          <div className="hero-console" aria-label="Example ArmTune terminal output">
            <div className="console-top">
              <span className="console-light red" />
              <span className="console-light amber" />
              <span className="console-light green" />
              <span className="console-title">armtune / benchmark</span>
              <span className="console-live">LIVE</span>
            </div>
            <div className="console-body">
              <p>
                <span className="prompt">$</span> armtune detect
              </p>
              <p className="muted">architecture</p>
              <p className="value">aarch64 / Neoverse-N2</p>
              <p className="muted">features</p>
              <p className="value">NEON I8MM SVE2 BF16</p>
              <p>
                <span className="prompt">$</span> armtune recommend --latest
              </p>
              <div className="recommend-line">
                <span>recommended</span>
                <strong>Q4_K_M / 4 threads / 1 slot</strong>
              </div>
              <div className="console-metrics">
                <div>
                  <small>TTFT</small>
                  <b>0.31s</b>
                  <i>-28%</i>
                </div>
                <div>
                  <small>DECODE</small>
                  <b>18.4</b>
                  <em>tok/s</em>
                </div>
                <div>
                  <small>QUALITY</small>
                  <b>0.91</b>
                  <i>pass</i>
                </div>
              </div>
              <p className="cursor">
                <span className="prompt">$</span>{" "}
                <span className="typing">llama-server -m model.gguf -t 4 -np 1</span>
                <span className="caret" />
              </p>
            </div>
          </div>
        </section>

        <section className="proof-strip shell" aria-label="Project facts">
          <div>
            <strong>01</strong>
            <span>Detect</span>
            <small>ISA, cores, memory, NUMA</small>
          </div>
          <div>
            <strong>02</strong>
            <span>Measure</span>
            <small>real inference on real hardware</small>
          </div>
          <div>
            <strong>03</strong>
            <span>Explain</span>
            <small>Arm Performix counters</small>
          </div>
          <div>
            <strong>04</strong>
            <span>Deploy</span>
            <small>copy-paste launch command</small>
          </div>
        </section>

        <section id="problem" className="section shell">
          <div className="section-label">
            <span>01</span>
            <span>Why this matters</span>
          </div>
          <div className="split-heading">
            <h2>The same model does not have one best configuration.</h2>
            <p>
              Quantization, thread count, memory pressure and concurrency
              interact with the processor underneath. A setting that wins on a
              4-core Neoverse-N2 can lose on a larger Graviton machine.
            </p>
          </div>
          <div className="card-grid three">
            <article className="feature-card accent-green">
              <span className="card-index">A / MODEL</span>
              <h3>Quality is a constraint.</h3>
              <p>
                Compare Q4, Q8 and other GGUF variants without allowing a fast
                but invalid structured response to win.
              </p>
              <Link href="/docs#quality">
                Quality gate <span>→</span>
              </Link>
            </article>
            <article className="feature-card accent-blue">
              <span className="card-index">B / RUNTIME</span>
              <h3>Threads are not free.</h3>
              <p>
                Separate decode and prefill behavior. Find where extra cores
                stop helping and start competing for bandwidth.
              </p>
              <Link href="/docs#cpu">
                CPU tuning <span>→</span>
              </Link>
            </article>
            <article className="feature-card accent-orange">
              <span className="card-index">C / EVIDENCE</span>
              <h3>Numbers need a reason.</h3>
              <p>
                Arm Performix adds IPC, cache, branch and memory evidence to
                explain why a configuration wins.
              </p>
              <Link href="/docs#performix">
                Performix <span>→</span>
              </Link>
            </article>
          </div>
        </section>

        <section id="how" className="section section-dark">
          <div className="shell">
            <div className="section-label">
              <span>02</span>
              <span>How it works</span>
            </div>
            <div className="split-heading">
              <h2>One workflow from model to production command.</h2>
              <p>
                ArmTune sits around the runtime you already trust. It does not
                replace llama.cpp. It makes the deployment decision observable
                and repeatable.
              </p>
            </div>
            <div className="pipeline">
              <div className="pipeline-step">
                <span className="step-num">01</span>
                <div className="step-icon">⌁</div>
                <h3>Fingerprint</h3>
                <p>Read the CPU&apos;s instruction set, memory, cores and NUMA topology.</p>
              </div>
              <div className="pipeline-connector" />
              <div className="pipeline-step">
                <span className="step-num">02</span>
                <div className="step-icon">↓</div>
                <h3>Source</h3>
                <p>Pull a GGUF model and quantization directly from Hugging Face.</p>
              </div>
              <div className="pipeline-connector" />
              <div className="pipeline-step">
                <span className="step-num">03</span>
                <div className="step-icon">×</div>
                <h3>Sweep</h3>
                <p>Run controlled tests across quantization, threads and concurrency.</p>
              </div>
              <div className="pipeline-connector" />
              <div className="pipeline-step">
                <span className="step-num">04</span>
                <div className="step-icon">◎</div>
                <h3>Recommend</h3>
                <p>Rank the quality-safe configurations and export the command.</p>
              </div>
            </div>
          </div>
        </section>

        <section id="evidence" className="section shell">
          <div className="section-label">
            <span>03</span>
            <span>Evidence, not folklore</span>
          </div>
          <div className="evidence-heading">
            <h2>Make the bottleneck visible.</h2>
            <div className="counter-note">
              <span className="counter-led" />
              <span>Arm Performix counters</span>
              <small>captured with the workload</small>
            </div>
          </div>
          <div className="evidence-panel">
            <div className="panel-head">
              <span>configuration comparison</span>
              <span>Neoverse-N2 / aarch64</span>
            </div>
            <div className="metric-row">
              <div className="metric-label">
                <span>Q8_0 / generic</span>
                <small>baseline</small>
              </div>
              <div className="bar-track">
                <span className="bar bar-gray" style={{ width: "52%" }} />
              </div>
              <strong>
                11.8 <small>tok/s</small>
              </strong>
            </div>
            <div className="metric-row selected">
              <div className="metric-label">
                <span>Q4_K_M / KleidiAI</span>
                <small>recommended</small>
              </div>
              <div className="bar-track">
                <span className="bar bar-green" style={{ width: "91%" }} />
              </div>
              <strong>
                18.4 <small>tok/s</small>
              </strong>
            </div>
            <div className="metric-row">
              <div className="metric-label">
                <span>Q4_0 / KleidiAI</span>
                <small>quality-safe</small>
              </div>
              <div className="bar-track">
                <span className="bar bar-blue" style={{ width: "84%" }} />
              </div>
              <strong>
                17.1 <small>tok/s</small>
              </strong>
            </div>
            <div className="evidence-footer">
              <span>Throughput</span>
              <span>
                Quality threshold: <b>0.50</b>
              </span>
              <span>
                Recommendation: <b>Q4_K_M</b>
              </span>
            </div>
          </div>
          <p className="disclaimer">
            Illustrative dashboard view. Published benchmark values are
            generated from the Arm64 workflow and stored as JSON, CSV, Markdown
            and chart artifacts.
          </p>
        </section>

        <section className="section section-dark" id="use-cases">
          <div className="shell">
            <div className="section-label">
              <span>04</span>
              <span>Built for real workflows</span>
            </div>
            <div className="split-heading">
              <h2>Useful before the first request reaches production.</h2>
              <p>
                ArmTune turns a performance question into an artifact a team can
                review, automate and deploy.
              </p>
            </div>
            <div className="use-case-list">
              <article className="use-case">
                <div className="use-case-mark">01</div>
                <div>
                  <h3>ML engineer</h3>
                  <p>
                    Compare model size, quality and speed on the actual Arm
                    target before selecting a quantization.
                  </p>
                </div>
                <span>→</span>
              </article>
              <article className="use-case">
                <div className="use-case-mark">02</div>
                <div>
                  <h3>Platform team</h3>
                  <p>
                    Run the benchmark in CI and detect a performance regression
                    when a runtime or model changes.
                  </p>
                </div>
                <span>→</span>
              </article>
              <article className="use-case">
                <div className="use-case-mark">03</div>
                <div>
                  <h3>Cloud architect</h3>
                  <p>
                    Compare a CPU-only deployment profile with a future CPU-GPU
                    split using the same workload contract.
                  </p>
                </div>
                <span>→</span>
              </article>
            </div>
          </div>
        </section>

        <section className="section shell platform-section">
          <div className="section-label">
            <span>05</span>
            <span>Arm cloud, without hardcoding a vendor</span>
          </div>
          <div className="platform-intro">
            <h2>Detect the capability. Tune the machine.</h2>
            <p>
              ArmTune works from the CPU fingerprint, so the same workflow
              travels across Arm64 Linux environments.
            </p>
          </div>
          <div className="platform-grid">
            <span>AWS Graviton</span>
            <span>Azure Cobalt</span>
            <span>Google Axion</span>
            <span>Ampere</span>
            <span>Neoverse N1</span>
            <span>Neoverse N2</span>
            <span>Neoverse V2</span>
            <span>Arm64 CI</span>
          </div>
        </section>

        <section className="cta-band">
          <div className="shell cta-inner">
            <div>
              <p className="eyebrow">OPEN SOURCE / ARM64</p>
              <h2>Stop guessing at runtime flags.</h2>
            </div>
            <div className="cta-actions">
              <Link className="button button-primary" href="/docs#quick-start">
                Read the docs <span>→</span>
              </Link>
              <a
                className="button button-outline"
                href="https://github.com/luxmikant/Arm-Tune"
                target="_blank"
                rel="noreferrer"
              >
                Star on GitHub <span>↗</span>
              </a>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
