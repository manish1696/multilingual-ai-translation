import type { TranslationMetrics } from "../types";

export function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  }
  return String(value);
}

export function confidenceScore(metrics: TranslationMetrics | undefined | null): string {
  if (!metrics || metrics.quality_score === null || metrics.quality_score === undefined) {
    return "\u2014";
  }
  return `${(metrics.quality_score * 100).toFixed(1)}%`;
}
