import { useMemo, useState } from "react";
import toast from "react-hot-toast";
import { Eye, Search, Trash2 } from "lucide-react";
import {
  clearResults,
  deleteResult,
  useResults,
  type StoredResult,
} from "../store/resultsStore";
import ResultViewModal from "../components/ResultViewModal";
import { confidenceScore } from "../utils/format";

type StatusFilter = "all" | "success" | "failed";

export default function Results() {
  const results = useResults();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [selected, setSelected] = useState<StoredResult | null>(null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return results.filter((r) => {
      if (statusFilter === "success" && r.translation_status !== "success")
        return false;
      if (statusFilter === "failed" && r.translation_status === "success")
        return false;
      if (!q) return true;
      return (
        r.source_text.toLowerCase().includes(q) ||
        r.reference_text.toLowerCase().includes(q) ||
        r.llm_translation.toLowerCase().includes(q) ||
        r.source_language.toLowerCase().includes(q) ||
        r.source_language_code.toLowerCase().includes(q)
      );
    });
  }, [results, search, statusFilter]);

  const handleClearAll = () => {
    if (!results.length) return;
    if (!window.confirm("Delete all stored results? This cannot be undone."))
      return;
    clearResults();
    toast.success("Cleared all results");
  };

  const handleDelete = (id: string) => {
    deleteResult(id);
    toast.success("Result deleted");
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-[#5b0428]">Results</h2>
          <p className="text-sm text-gray-600 mt-1">
            All translations evaluated in this browser session.
            {results.length > 0 && (
              <>
                {" "}
                Showing <strong>{filtered.length}</strong> of{" "}
                <strong>{results.length}</strong>.
              </>
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={handleClearAll}
          disabled={!results.length}
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-200 rounded-md hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Trash2 className="w-4 h-4" />
          Clear all
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border p-4 flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search source, translation, language…"
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#5b0428] focus:border-[#5b0428]"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
          className="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#5b0428] focus:border-[#5b0428]"
        >
          <option value="all">All statuses</option>
          <option value="success">Success only</option>
          <option value="failed">Failed only</option>
        </select>
      </div>

      {results.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border p-10 text-center">
          <p className="text-gray-600 text-sm">
            No results yet. Run a translation from the{" "}
            <strong>Translate</strong> page, or use{" "}
            <strong>Upload</strong> in the header to process a CSV/XLSX in
            bulk.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wide">
                <tr>
                  <th className="text-left px-4 py-3">When</th>
                  <th className="text-left px-4 py-3">Language</th>
                  <th className="text-left px-4 py-3">Source</th>
                  <th className="text-left px-4 py-3">LLM translation</th>
                  <th className="text-left px-4 py-3">Status</th>
                  <th className="text-left px-4 py-3">Quality score</th>
                  <th className="text-right px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr>
                    <td
                      colSpan={8}
                      className="px-4 py-8 text-center text-gray-500"
                    >
                      No results match the current filter.
                    </td>
                  </tr>
                )}
                {filtered.map((r) => {
                  const isSuccess = r.translation_status === "success";
                  return (
                    <tr
                      key={r.id}
                      className="border-t border-gray-100 hover:bg-gray-50"
                    >
                      <td className="px-4 py-3 text-gray-600 text-xs whitespace-nowrap align-top">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-gray-700 whitespace-nowrap align-top">
                        <span className="font-medium">
                          {r.source_language}
                        </span>{" "}
                        <span className="text-xs text-gray-500">
                          ({r.source_language_code})
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-800 align-top max-w-xs">
                        <div className="line-clamp-2">{r.source_text}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-800 align-top max-w-xs">
                        <div className="line-clamp-2">
                          {r.llm_translation || "—"}
                        </div>
                      </td>
                      <td className="px-4 py-3 align-top">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                            isSuccess
                              ? "bg-success-50 text-success-500"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {isSuccess ? "SUCCESS" : "FAILED"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-800 font-semibold align-top whitespace-nowrap">
                        {confidenceScore(r.metrics)}
                      </td>
                      {/* <td className="px-4 py-3 text-gray-600 font-mono text-xs align-top whitespace-nowrap">
                        {formatValue(r.metrics.sentence_chrf)}
                      </td> */}
                      <td className="px-4 py-3 text-right align-top whitespace-nowrap">
                        <div className="inline-flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => setSelected(r)}
                            title="View"
                            className="p-1.5 text-[#5b0428] hover:bg-[#5b0428]/10 rounded transition-colors"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(r.id)}
                            title="Delete"
                            className="p-1.5 text-red-600 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <ResultViewModal result={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
