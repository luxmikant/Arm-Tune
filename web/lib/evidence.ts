export interface EvidenceMetric {
  label: string;
  baseline: number;
  tuned: number;
  unit: string;
  betterIsLower: boolean;
}

export interface Evidence {
  capturedAt: string;
  hardware: string;
  model: string;
  tunedConfig: string;
  metrics: EvidenceMetric[];
  summary: { label: string; value: string }[];
  sourceUrl: string;
}

/**
 * Populated from the ARM64 CI benchmark artifacts committed under
 * docs/evidence/ (workflow run 31790177140). Regenerate any time via
 * Actions > Benchmark ARM64 > Run workflow.
 */
export const evidence: Evidence = {
  capturedAt: "2026-08-14T10:04Z",
  hardware: "Neoverse-N2 · 4 cores · 15.6 GB · aarch64",
  model: "Llama-3.2-1B-Instruct (GGUF)",
  tunedConfig: "Q4_0 · 4 threads · 1 slot",
  metrics: [
    {
      label: "Decode throughput",
      baseline: 26.1,
      tuned: 33.0,
      unit: "tok/s",
      betterIsLower: false,
    },
    {
      label: "Time to first token",
      baseline: 0.45,
      tuned: 0.33,
      unit: "s",
      betterIsLower: true,
    },
    {
      label: "P95 latency",
      baseline: 2.52,
      tuned: 1.91,
      unit: "s",
      betterIsLower: true,
    },
    {
      label: "Peak process RSS",
      baseline: 1701,
      tuned: 1616,
      unit: "MB",
      betterIsLower: true,
    },
  ],
  summary: [
    {
      label: "Thread sweep",
      value: "1 → 2 → 4 threads: 8.1 → 15.1 → 28.1 tok/s (3.5×)",
    },
    {
      label: "Quality gate",
      value: "strict JSON + expected labels: 1.00 / 1.00 (threshold 0.5)",
    },
    {
      label: "Workload",
      value: "5 ticket prompts · 1 warmup + 6 measured · 128 tokens · seed 42+i",
    },
  ],
  sourceUrl:
    "https://github.com/luxmikant/Arm-Tune/tree/main/docs/evidence",
};

export function hasEvidence(e: Evidence | null): e is Evidence {
  return e !== null && e.metrics.length > 0;
}

export function pctChange(baseline: number, tuned: number): number {
  if (!baseline) return 0;
  return ((tuned - baseline) / baseline) * 100;
}
