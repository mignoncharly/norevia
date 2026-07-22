export type ScoredValue = { score: number | null; weight: number; qualityCoefficient: number; available: boolean };

export function normalize(value: number, p05: number, p95: number, direction: "HIGHER_IS_BETTER" | "LOWER_IS_BETTER"): number | null {
  if (![value, p05, p95].every(Number.isFinite) || p95 <= p05) return null;
  const capped = Math.min(p95, Math.max(p05, value));
  const ascending = ((capped - p05) / (p95 - p05)) * 100;
  return direction === "HIGHER_IS_BETTER" ? ascending : 100 - ascending;
}

export function aggregate(values: ScoredValue[]) {
  const eligible = values.filter((item) => item.available && item.score !== null && item.weight > 0);
  const requested = values.reduce((sum, item) => sum + Math.max(0, item.weight), 0);
  const covered = eligible.reduce((sum, item) => sum + item.weight, 0);
  const denominator = eligible.reduce((sum, item) => sum + item.weight * item.qualityCoefficient, 0);
  const numerator = eligible.reduce((sum, item) => sum + (item.score ?? 0) * item.weight * item.qualityCoefficient, 0);
  return {
    destinationScore: denominator > 0 ? numerator / denominator : null,
    dataCoverage: requested > 0 ? (covered / requested) * 100 : 0,
    confidenceCoefficient: covered > 0 ? denominator / covered : 0,
  };
}
