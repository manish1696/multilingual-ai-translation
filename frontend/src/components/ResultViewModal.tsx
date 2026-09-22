import type { StoredResult } from "../store/resultsStore";
import { X } from "lucide-react";
import { confidenceScore, formatValue } from "../utils/format";

interface Props {
  result: StoredResult | null;
  onClose: () => void;
}

export default function ResultViewModal({ result, onClose }: Props) {
  if (!result) return null;

  const metrics = result.metrics;
  const isSuccess = result.translation_status === "success";

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-xl font-semibold text-[#5b0428]">
              Translation result
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              {new Date(result.created_at).toLocaleString()} ·{" "}
              <span className="font-mono">{result.id}</span>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          <div className="flex items-center gap-3 text-sm">
            <span
              className={`text-xs font-semibold px-2 py-1 rounded-full ${
                isSuccess
                  ? "bg-success-50 text-success-500"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {isSuccess ? "SUCCESS" : "FAILED"}
            </span>
            <span className="text-gray-600">
              {result.source_language} ({result.source_language_code}) →{" "}
              {result.target_language}
            </span>
          </div>

          {!isSuccess && result.translation_error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-md p-3">
              {result.translation_error}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TextBlock label="Source text" value={result.source_text} />
            <TextBlock
              label={`Reference (${result.target_language})`}
              value={result.reference_text || "Not supplied"}
            />
            <TextBlock
              label="LLM translation"
              value={result.llm_translation || "—"}
              accent
            />
          </div>

          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-2">
              Metrics
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Metric
                label="Quality Score"
                value={confidenceScore(metrics)}
                highlight
              />
              <Metric label="chrF" value={formatValue(metrics.sentence_chrf)} />
              <Metric label="Semantic" value={metrics.semantic_similarity === null ? "—" : `${(metrics.semantic_similarity * 100).toFixed(1)}%`} />
              <Metric
                label="Token F1"
                value={formatValue(metrics.token_f1)}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <DetailTable
              title="Evaluation details"
              rows={[
                ["Passes quality threshold", metrics.passes_quality_threshold],
                ["Semantic similarity", metrics.semantic_similarity],
                ["Entity preservation", metrics.entity_preservation],
                ["Exact match", metrics.exact_match],
                ["Composite score", metrics.composite_score],
                ["Length ratio", metrics.length_ratio],
                ["Adequacy score", metrics.adequacy_score],
                ["BLEU", metrics.sentence_bleu],
                ["Validation method", metrics.validation_method],
              ]}
            />
            <DetailTable
              title="Run metadata"
              rows={[
                ["Model", result.model],
                ["Prompt path", result.prompt_path],
                ["Latency (s)", result.latency_seconds],
                ["Input tokens", result.input_tokens],
                ["Output tokens", result.output_tokens],
                ["Total tokens", result.total_tokens],
                ["Status", result.translation_status],
                ["Strategy", result.strategy],
                ["Route", result.route?.join(" → ")],
              ]}
            />
          </div>
        </div>

        <div className="flex items-center justify-end p-6 border-t bg-gray-50">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function TextBlock({
  label,
  value,
  accent = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1">
        {label}
      </div>
      <div
        className={`text-sm border rounded-md p-3 whitespace-pre-wrap ${
          accent
            ? "border-[#5b0428]/30 bg-[#5b0428]/5 text-gray-900"
            : "border-gray-200 bg-gray-50 text-gray-800"
        }`}
      >
        {value}
      </div>
    </div>
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

function DetailTable({
  title,
  rows,
}: {
  title: string;
  rows: Array<[string, unknown]>;
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-2">{title}</h4>
      <div className="overflow-hidden rounded-md border border-gray-200">
        <table className="w-full text-sm">
          <tbody>
            {rows.map(([label, value]) => (
              <tr
                key={label}
                className="border-b last:border-b-0 border-gray-100 odd:bg-white even:bg-gray-50"
              >
                <td className="py-2 px-3 text-gray-500 w-2/5 align-top">
                  {label}
                </td>
                <td className="py-2 px-3 text-gray-800 font-mono text-xs break-all">
                  {formatValue(value)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
