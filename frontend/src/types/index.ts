export interface LanguagePreset { label: string; name: string; code: string }
export interface LanguagesResponse { presets: LanguagePreset[] }

export interface TranslationMetrics {
  sentence_bleu: number | null;
  sentence_chrf: number | null;
  token_f1: number | null;
  length_ratio: number | null;
  adequacy_score: number | null;
  composite_score: number | null;
  exact_match: boolean;
  good_translation: boolean;
  accuracy: string;
  accuracy_rate: number;
  validation_method: string;
  semantic_similarity: number | null;
  entity_preservation: number | null;
  quality_score: number | null;
  passes_quality_threshold: boolean;
}

export interface TranslationStage {
  source_language: string;
  source_language_code: string;
  target_language: string;
  target_language_code: string;
  translation: string;
  status: string;
  error: string;
  prompt_path: string;
  latency_seconds: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface TranslationRequest {
  source_text: string;
  source_language: string;
  source_language_code: string;
  target_language: string;
  target_language_code: string;
}

export interface EvaluationRequest extends TranslationRequest {
  reference_text: string;
}

export interface TranslationResponse extends EvaluationRequest {
  llm_translation: string;
  translation_status: string;
  translation_error: string;
  prompt_path: string;
  model: string;
  latency_seconds: number;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  metrics: TranslationMetrics;
  strategy: "identity" | "direct" | "english_pivot";
  route: string[];
  pivot_translation: string | null;
  stages: TranslationStage[];
}
