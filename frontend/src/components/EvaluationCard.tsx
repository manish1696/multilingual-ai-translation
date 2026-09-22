import type { TranslationMetrics, TranslationResponse } from "../types";
import { confidenceScore, formatValue } from "../utils/format";

interface Props {
  result: TranslationResponse | null;
  isLoading: boolean;
}

export default function EvaluationCard({ result, isLoading }: Props) {
  if (isLoading && !result) {
    return (
      <section className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-base font-semibold text-[#5b0428] mb-3">
          Evaluation
        </h3>
        <div className="text-sm text-gray-600 bg-blue-50 border border-blue-100 rounded-md p-3">
          Translating and scoring…
        </div>
      </section>
    );
  }

  if (!result) {
    return (
      <section className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-base font-semibold text-[#5b0428] mb-3">
          Evaluation
        </h3>
        <div className="text-sm text-blue-900 bg-blue-50 border border-blue-100 rounded-md p-3">
          Add a reference translation to see semantic similarity, chrF, and other
          evaluation details here.
        </div>
      </section>
    );
  }

  const metrics: TranslationMetrics = result.metrics;
  const isSuccess = result.translation_status === "success";

  return (
    <section className="bg-white rounded-lg shadow-sm border p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-[#5b0428]">Evaluation</h3>
        <span
          className={`text-xs font-semibold px-2 py-1 rounded-full ${
            isSuccess
              ? "bg-success-50 text-success-500"
              : "bg-red-50 text-red-700"
          }`}
        >
          {isSuccess ? "SUCCESS" : "FAILED"}
        </span>
      </div>

      {!isSuccess && (
        <div className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-md p-3">
          {result.translation_error || "Translation failed."}
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Metric label="Quality Score" value={confidenceScore(metrics)} highlight />
        <Metric label="Semantic Match" value={metrics.semantic_similarity === null ? "—" : `${(metrics.semantic_similarity * 100).toFixed(1)}%`} />
        <Metric label="chrF" value={formatValue(metrics.sentence_chrf)} />
        <Metric label="Token F1" value={formatValue(metrics.token_f1)} />
      </div>

      <div>
        <h4 className="text-sm font-semibold text-gray-700 mb-2">
          Evaluation details
        </h4>
        <div className="overflow-hidden rounded-md border border-gray-200">
          <table className="w-full text-sm">
            <tbody>
              <Row label="Passes quality threshold" value={metrics.passes_quality_threshold} />
              <Row label="Entity preservation" value={metrics.entity_preservation} />
              <Row label="Legacy good translation" value={metrics.good_translation} />
              <Row label="Exact match" value={metrics.exact_match} />
              <Row label="Composite score" value={metrics.composite_score} />
              <Row label="Length ratio" value={metrics.length_ratio} />
              <Row label="Adequacy score" value={metrics.adequacy_score} />
              <Row label="Sentence BLEU" value={metrics.sentence_bleu} />
              <Row
                label="Validation method"
                value={metrics.validation_method}
              />
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  highlight = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-md p-3">
      <div className="text-[11px] uppercase tracking-wide text-gray-500 font-medium">
        {label}
      </div>
      <div
        className={`text-xl font-bold mt-0.5 ${
          highlight ? "text-[#5b0428]" : "text-gray-900"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: unknown }) {
  return (
    <tr className="border-b last:border-b-0 border-gray-100 odd:bg-white even:bg-gray-50">
      <td className="py-2 px-3 text-gray-500 w-1/3 align-top">{label}</td>
      <td className="py-2 px-3 text-gray-800 font-mono text-xs break-all">
        {formatValue(value)}
      </td>
    </tr>
  );
}
