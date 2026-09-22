import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { ArrowRight, ArrowRightLeft, Copy, Loader2, Play, Route } from "lucide-react";
import { evaluateTranslation, fetchLanguages, translateText } from "../services/api";
import type { LanguagePreset, TranslationResponse } from "../types";
import EvaluationCard from "../components/EvaluationCard";
import { addResult } from "../store/resultsStore";

const FALLBACK: LanguagePreset[] = [
  ["English", "en"], ["French", "fr"], ["German", "de"],
  ["Spanish (Europe)", "es"], ["Portuguese (Europe)", "pt"],
  ["Hungarian", "hu"], ["Hindi", "hi"], ["Chinese", "zh"],
  ["Egyptian Arabic", "arz"], ["Japanese", "ja"], ["Korean", "ko"],
].map(([name, code]) => ({ label: name, name, code }));

type Mode = "translate" | "evaluate";

export default function Home() {
  const [languages, setLanguages] = useState(FALLBACK);
  const [sourceCode, setSourceCode] = useState("ja");
  const [targetCode, setTargetCode] = useState("ko");
  const [sourceText, setSourceText] = useState("");
  const [referenceText, setReferenceText] = useState("");
  const [mode, setMode] = useState<Mode>("translate");
  const [result, setResult] = useState<TranslationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchLanguages().then((r) => r.presets?.length && setLanguages(r.presets)).catch(() => undefined);
  }, []);

  const source = useMemo(
    () => languages.find((l) => l.code === sourceCode) || languages[0],
    [languages, sourceCode],
  );
  const target = useMemo(
    () => languages.find((l) => l.code === targetCode) || languages[1],
    [languages, targetCode],
  );
  const plannedRoute = sourceCode === targetCode
    ? [sourceCode]
    : sourceCode === "en" || targetCode === "en"
      ? [sourceCode, targetCode] : [sourceCode, "en", targetCode];

  const swap = () => {
    setSourceCode(targetCode);
    setTargetCode(sourceCode);
    if (result?.llm_translation) setSourceText(result.llm_translation);
    setResult(null);
  };

  const submit = async () => {
    if (!sourceText.trim()) return toast.error("Enter text to translate.");
    if (mode === "evaluate" && !referenceText.trim()) {
      return toast.error("A reference translation is required for evaluation.");
    }
    setIsLoading(true);
    setResult(null);
    const base = {
      source_text: sourceText.trim(),
      source_language: source.name,
      source_language_code: source.code,
      target_language: target.name,
      target_language_code: target.code,
    };
    try {
      const data = mode === "evaluate"
        ? await evaluateTranslation({ ...base, reference_text: referenceText.trim() })
        : await translateText(base);
      setResult(data);
      addResult(data);
      toast.success(mode === "evaluate" ? "Translation evaluated" : "Translation complete");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(detail || (err instanceof Error ? err.message : "Request failed"));
    } finally { setIsLoading(false); }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <section className="rounded-2xl bg-gradient-to-r from-[#5b0428] to-[#8c174c] text-white p-6 md:p-8 shadow-lg">
        <div className="text-xs uppercase tracking-[0.22em] text-rose-200 font-semibold">Quality-aware multilingual AI</div>
        <h2 className="text-3xl font-bold mt-2">Translate across 110 language directions</h2>
        <p className="text-rose-100 mt-2 max-w-3xl">Direct English routes use one model call. Other language pairs use an inspectable English pivot with per-stage latency and token tracking.</p>
      </section>

      <div className="inline-flex bg-white border rounded-lg p-1 shadow-sm">
        {(["translate", "evaluate"] as Mode[]).map((item) => (
          <button key={item} onClick={() => setMode(item)} className={`px-5 py-2 rounded-md text-sm font-semibold capitalize ${mode === item ? "bg-[#5b0428] text-white" : "text-gray-600 hover:bg-gray-50"}`}>{item}</button>
        ))}
      </div>

      <section className="bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div className="grid grid-cols-[1fr_auto_1fr] items-end gap-3 p-5 border-b bg-gray-50">
          <LanguageSelect label="From" value={sourceCode} onChange={setSourceCode} languages={languages} />
          <button onClick={swap} title="Swap languages" className="mb-1 p-2.5 rounded-full border bg-white text-[#5b0428] hover:bg-rose-50"><ArrowRightLeft className="w-5 h-5" /></button>
          <LanguageSelect label="To" value={targetCode} onChange={setTargetCode} languages={languages} />
        </div>

        <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x">
          <div className="p-5">
            <textarea rows={10} maxLength={20000} value={sourceText} onChange={(e) => setSourceText(e.target.value)} placeholder={`Enter ${source.name} text`} className="w-full resize-none text-lg outline-none" />
            <div className="text-right text-xs text-gray-400">{sourceText.length}/20,000</div>
          </div>
          <div className="p-5 bg-gray-50/60 relative">
            <textarea readOnly rows={10} value={result?.llm_translation || ""} placeholder={isLoading ? "Translating…" : `${target.name} translation`} className="w-full resize-none bg-transparent text-lg outline-none" />
            {result?.llm_translation && <button onClick={() => navigator.clipboard.writeText(result.llm_translation)} className="absolute right-5 bottom-5 p-2 text-gray-500 hover:text-[#5b0428]" title="Copy translation"><Copy className="w-4 h-4" /></button>}
          </div>
        </div>

        {mode === "evaluate" && <div className="p-5 border-t bg-blue-50/50"><label className="block text-sm font-semibold text-gray-700 mb-2">Reference translation in {target.name}</label><textarea rows={4} value={referenceText} onChange={(e) => setReferenceText(e.target.value)} placeholder="Paste a human/reference translation for semantic and lexical evaluation" className="w-full rounded-lg border px-3 py-2 text-sm" /></div>}

        <div className="flex flex-wrap items-center justify-between gap-4 p-5 border-t">
          <div className="flex items-center gap-2 text-sm text-gray-600"><Route className="w-4 h-4 text-[#5b0428]" />{plannedRoute.map((code, i) => <span key={`${code}-${i}`} className="flex items-center gap-2"><strong className="uppercase">{code}</strong>{i < plannedRoute.length - 1 && <ArrowRight className="w-3 h-3" />}</span>)}<span className="text-xs bg-gray-100 px-2 py-1 rounded-full">{Math.max(0, plannedRoute.length - 1)} call(s)</span></div>
          <button onClick={submit} disabled={isLoading} className="flex items-center gap-2 bg-[#5b0428] text-white px-6 py-2.5 rounded-lg hover:bg-[#7b0538] disabled:opacity-60 font-semibold">{isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}{isLoading ? "Working…" : mode === "evaluate" ? "Translate & evaluate" : "Translate"}</button>
        </div>
      </section>

      {result && <RouteDetails result={result} />}
      {mode === "evaluate" && <EvaluationCard result={result} isLoading={isLoading} />}
    </div>
  );
}

function LanguageSelect({ label, value, onChange, languages }: { label: string; value: string; onChange: (v: string) => void; languages: LanguagePreset[] }) {
  return <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">{label}<select value={value} onChange={(e) => onChange(e.target.value)} className="block w-full mt-1 bg-white border rounded-lg px-3 py-2.5 text-sm text-gray-900 normal-case"><option value="" disabled>Select language</option>{languages.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}</select></label>;
}

function RouteDetails({ result }: { result: TranslationResponse }) {
  return <section className="bg-white rounded-xl border p-5"><div className="flex flex-wrap justify-between gap-3"><div><h3 className="font-semibold text-[#5b0428]">Translation route</h3><p className="text-sm text-gray-600 mt-1">{result.route.map((x) => x.toUpperCase()).join(" → ")} · {result.strategy.replace("_", " ")} · {result.stages.length} call(s)</p></div><div className="text-sm text-gray-600 text-right"><div>{result.latency_seconds}s total latency</div><div>{result.total_tokens.toLocaleString()} tokens</div></div></div>{result.pivot_translation && <details className="mt-4"><summary className="cursor-pointer text-sm font-semibold text-gray-700">Inspect English pivot</summary><div className="mt-2 p-3 rounded-lg bg-gray-50 border text-sm whitespace-pre-wrap">{result.pivot_translation}</div></details>}</section>;
}
