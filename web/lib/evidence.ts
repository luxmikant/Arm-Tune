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
 * Populated from the ARM64 CI benchmark artifacts (docs/evidence/).
 * Fields stay null until a real run is captured — the site never presents
 * illustrative numbers as measurements.
 */
export const evidence: Evidence | null = null;

export function hasEvidence(e: Evidence | null): e is Evidence {
  return e !== null && e.metrics.length > 0;
}

export function pctChange(baseline: number, tuned: number): number {
  if (!baseline) return 0;
  return ((tuned - baseline) / baseline) * 100;
}
