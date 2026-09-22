from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    source_text: str = Field(..., min_length=1, max_length=20000, description="Original text")
    source_language: str = Field(..., min_length=1, description="Source language name, e.g. French")
    source_language_code: str = Field(..., min_length=1, description="Source language code, e.g. fr")
    target_language: str = Field("English", description="Target language name")
    target_language_code: str = Field("en", min_length=2, description="Target language code")


class EvaluationRequest(TranslationRequest):
    reference_text: str = Field(..., min_length=1, max_length=20000)


class TranslationMetrics(BaseModel):
    sentence_bleu: Optional[float] = None
    sentence_chrf: Optional[float] = None
    token_f1: Optional[float] = None
    length_ratio: Optional[float] = None
    adequacy_score: Optional[float] = None
    composite_score: Optional[float] = None
    exact_match: bool = False
    good_translation: bool = False
    accuracy: str = "0/1"
    accuracy_rate: float = 0.0
    validation_method: str = ""
    semantic_similarity: Optional[float] = None
    entity_preservation: Optional[float] = None
    quality_score: Optional[float] = None
    passes_quality_threshold: bool = False


class TranslationStage(BaseModel):
    source_language: str
    source_language_code: str
    target_language: str
    target_language_code: str
    translation: str
    status: str
    error: str = ""
    prompt_path: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


class TranslationResponse(BaseModel):
    source_text: str
    reference_text: str = ""
    source_language: str
    source_language_code: str
    target_language: str
    target_language_code: str = "en"
    llm_translation: str
    translation_status: str
    translation_error: str
    prompt_path: str
    model: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    metrics: TranslationMetrics
    strategy: str = "direct"
    route: list[str] = Field(default_factory=list)
    pivot_translation: Optional[str] = None
    stages: list[TranslationStage] = Field(default_factory=list)


class LanguagePreset(BaseModel):
    label: str
    name: str
    code: str


class LanguagesResponse(BaseModel):
    presets: list[LanguagePreset]
