import { useRef, useState } from "react";
import { AlertCircle, FileText, Upload, X } from "lucide-react";
import * as XLSX from "xlsx";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { evaluateTranslation } from "../services/api";
import { addResults } from "../store/resultsStore";
import type {
  EvaluationRequest,
  TranslationResponse,
} from "../types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

interface ParsedRow {
  rowNumber: number;
  payload: EvaluationRequest;
}

const REQUIRED_COLUMNS = [
  "source_text",
  "reference_text",
  "source_language",
  "source_language_code",
] as const;

function pick(record: Record<string, unknown>, key: string): string {
  const raw = record[key];
  if (raw === null || raw === undefined) return "";
  return String(raw).trim();
}

function parseWorkbook(file: File): Promise<ParsedRow[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read the file."));
    reader.onload = (event) => {
      try {
        const data = event.target?.result;
        if (!data) {
          reject(new Error("Empty file."));
          return;
        }
        const workbook = XLSX.read(data, { type: "array" });
        const firstSheetName = workbook.SheetNames[0];
        if (!firstSheetName) {
          reject(new Error("Workbook has no sheets."));
          return;
        }
        const sheet = workbook.Sheets[firstSheetName];
        const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, {
          defval: "",
          raw: false,
        });

        if (!rows.length) {
          reject(new Error("File has no data rows."));
          return;
        }

        const headers = Object.keys(rows[0]).map((h) => h.toLowerCase().trim());
        const missing = REQUIRED_COLUMNS.filter((c) => !headers.includes(c));
        if (missing.length) {
          reject(
            new Error(
              `Missing required column(s): ${missing.join(", ")}. ` +
                `Headers must be: source_text, reference_text, source_language, ` +
                `source_language_code, [target_language].`,
            ),
          );
          return;
        }

        const normalized: ParsedRow[] = rows.map((row, idx) => {
          const lower: Record<string, unknown> = {};
          for (const [k, v] of Object.entries(row)) {
            lower[k.toLowerCase().trim()] = v;
          }
          return {
            rowNumber: idx + 2,
            payload: {
              source_text: pick(lower, "source_text"),
              reference_text: pick(lower, "reference_text"),
              source_language: pick(lower, "source_language"),
              source_language_code: pick(
                lower,
                "source_language_code",
              ).toLowerCase(),
              target_language: pick(lower, "target_language") || "English",
              target_language_code: pick(lower, "target_language_code") || "en",
            },
          };
        });

        resolve(normalized);
      } catch (err) {
        reject(err instanceof Error ? err : new Error("Failed to parse file."));
      }
    };
    reader.readAsArrayBuffer(file);
  });
}

export default function UploadModal({ isOpen, onClose }: Props) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedRows, setParsedRows] = useState<ParsedRow[] | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const reset = () => {
    setSelectedFile(null);
    setParsedRows(null);
    setError(null);
    setProgress({ done: 0, total: 0 });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleClose = () => {
    if (isUploading) return;
    reset();
    onClose();
  };

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const isCsv = file.name.toLowerCase().endsWith(".csv");
    const isXlsx = file.name.toLowerCase().endsWith(".xlsx");
    if (!isCsv && !isXlsx) {
      setError("Please select a CSV or XLSX file.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB.");
      return;
    }

    setSelectedFile(file);
    setError(null);
    setParsedRows(null);

    try {
      const rows = await parseWorkbook(file);
      setParsedRows(rows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse file.");
    }
  };

  const handleSubmit = async () => {
    if (!parsedRows || !parsedRows.length) {
      setError("No rows to process.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setProgress({ done: 0, total: parsedRows.length });

    const successes: TranslationResponse[] = [];
    let failures = 0;

    for (let i = 0; i < parsedRows.length; i++) {
      const { rowNumber, payload } = parsedRows[i];
      try {
        const result = await evaluateTranslation(payload);
        successes.push(result);
      } catch (err) {
        failures += 1;
        console.warn(`Row ${rowNumber} failed`, err);
      }
      setProgress({ done: i + 1, total: parsedRows.length });
    }

    if (successes.length) {
      addResults(successes);
    }

    setIsUploading(false);

    if (successes.length && !failures) {
      toast.success(`Processed ${successes.length} rows`);
    } else if (successes.length && failures) {
      toast.success(`Processed ${successes.length} rows (${failures} failed)`);
    } else {
      toast.error("All rows failed");
    }

    reset();
    onClose();
    navigate("/results");
  };

  if (!isOpen) return null;

  const progressPct =
    progress.total > 0 ? Math.round((progress.done / progress.total) * 100) : 0;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={handleClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Upload className="w-5 h-5 mr-2 text-[#5b0428]" />
            Upload translation jobs
          </h2>
          <button
            type="button"
            onClick={handleClose}
            disabled={isUploading}
            className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-40"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select file
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                onChange={handleFileChange}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex flex-col items-center space-y-2 text-gray-600 hover:text-gray-800 transition-colors w-full disabled:opacity-50"
              >
                <Upload className="w-8 h-8" />
                <span className="text-sm font-medium text-center">
                  {selectedFile ? selectedFile.name : "Click to select file"}
                </span>
                <span className="text-xs text-gray-500">
                  CSV or XLSX (max 10MB)
                </span>
              </button>
            </div>
          </div>

          {selectedFile && parsedRows && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-md flex items-center space-x-2">
              <FileText className="w-4 h-4 text-blue-500" />
              <span className="text-sm text-blue-700">
                {selectedFile.name} — {parsedRows.length} row(s) ready to
                process
              </span>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-md flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}

          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              File format
            </h3>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• CSV or XLSX (.csv, .xlsx)</li>
              <li>
                • Required columns:{" "}
                <code className="bg-white px-1 rounded">source_text</code>,{" "}
                <code className="bg-white px-1 rounded">reference_text</code>,{" "}
                <code className="bg-white px-1 rounded">source_language</code>,{" "}
                <code className="bg-white px-1 rounded">
                  source_language_code
                </code>
              </li>
              <li>
                • Optional:{" "}
                <code className="bg-white px-1 rounded">target_language</code>{" "}
                (defaults to English)
              </li>
              <li>• Maximum file size: 10MB</li>
            </ul>
          </div>

          {isUploading && (
            <div>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Translating rows…</span>
                <span>
                  {progress.done}/{progress.total} ({progressPct}%)
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#5b0428] transition-all"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end space-x-3 p-6 border-t bg-gray-50">
          <button
            type="button"
            onClick={handleClose}
            disabled={isUploading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!parsedRows?.length || isUploading}
            className="px-4 py-2 text-sm font-medium text-white bg-[#5b0428] border border-transparent rounded-md hover:bg-[#7b0538] disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            {isUploading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            )}
            <span>
              {isUploading
                ? `Processing ${progress.done}/${progress.total}…`
                : "Translate all rows"}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
