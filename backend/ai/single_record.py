from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import sacrebleu

from . import config
from .client import build_client
from .prompts import resolve_translation_prompt_path
from .scoring import (
    composite_translation_score,
    compute_adequacy_score,
    get_validation_method,
    is_good_translation,
    length_ratio_score,
    token_f1_score,
    entity_preservation_score,
    passes_quality_threshold,
    quality_score_v2,
)
from .semantic import semantic_similarity
from .text_utils import clean_text, normalize_for_exact_match
from .translator import translate_one


@dataclass
class SingleRecordMetrics:
    sentence_bleu: Optional[float]
    sentence_chrf: Optional[float]
    token_f1: Optional[float]
    length_ratio: Optional[float]
    adequacy_score: Optional[float]
    composite_score: Optional[float]
    exact_match: bool
    good_translation: bool
    accuracy: str
    accuracy_rate: float
    validation_method: str
    semantic_similarity: Optional[float]
    entity_preservation: Optional[float]
    quality_score: Optional[float]
    passes_quality_threshold: bool


@dataclass
class SingleRecordResult:
    source_text: str
    reference_text: str
    source_language: str
    source_language_code: str
    target_language: str
    llm_translation: str
    translation_status: str
    translation_error: str
    prompt_path: str
    model: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    metrics: SingleRecordMetrics

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["metrics"] = asdict(self.metrics)
        return payload


def _empty_metrics() -> SingleRecordMetrics:
    return SingleRecordMetrics(
        sentence_bleu=None,
        sentence_chrf=None,
        token_f1=None,
        length_ratio=None,
        adequacy_score=None,
        composite_score=None,
        exact_match=False,
        good_translation=False,
        accuracy="0/1",
        accuracy_rate=0.0,
        validation_method=get_validation_method(),
        semantic_similarity=None,
        entity_preservation=None,
        quality_score=None,
        passes_quality_threshold=False,
    )


def score_single_translation(
    prediction: str, reference: str, source_text: str = ""
) -> SingleRecordMetrics:
    prediction = clean_text(prediction)
    reference = clean_text(reference)

    if not prediction or not reference:
        return _empty_metrics()

    sentence_bleu = round(sacrebleu.sentence_bleu(prediction, [reference]).score, 4)
    sentence_chrf = round(sacrebleu.sentence_chrf(prediction, [reference]).score, 4)
    exact_match = normalize_for_exact_match(prediction) == normalize_for_exact_match(reference)
    token_f1 = token_f1_score(prediction, reference)
    length_ratio = length_ratio_score(prediction, reference)
    adequacy_score = compute_adequacy_score(sentence_chrf, token_f1, length_ratio)
    composite_score = composite_translation_score(sentence_bleu, sentence_chrf)
    good_translation = is_good_translation(
        exact_match=exact_match,
        sentence_chrf=sentence_chrf,
        token_f1=token_f1,
        length_ratio=length_ratio,
        adequacy_score=adequacy_score,
    )
    semantic_score = semantic_similarity(prediction, reference)
    entity_score = entity_preservation_score(source_text or reference, prediction)
    quality_score = quality_score_v2(
        semantic_score, sentence_chrf, token_f1, length_ratio, entity_score
    )
    quality_pass = passes_quality_threshold(quality_score, semantic_score)

    return SingleRecordMetrics(
        sentence_bleu=sentence_bleu,
        sentence_chrf=sentence_chrf,
        token_f1=token_f1,
        length_ratio=length_ratio,
        adequacy_score=adequacy_score,
        composite_score=composite_score,
        exact_match=exact_match,
        good_translation=good_translation,
        accuracy="1/1" if good_translation else "0/1",
        accuracy_rate=1.0 if good_translation else 0.0,
        validation_method=get_validation_method(),
        semantic_similarity=semantic_score,
        entity_preservation=entity_score,
        quality_score=quality_score,
        passes_quality_threshold=quality_pass,
    )


def translate_and_evaluate_single(
    source_text: str,
    reference_text: str,
    source_language: str,
    source_language_code: str,
    target_language: str = "English",
    max_completion_tokens: int = config.DEFAULT_MAX_COMPLETION_TOKENS,
    retry_count: int = config.DEFAULT_RETRY_COUNT,
    retry_sleep: float = config.DEFAULT_RETRY_SLEEP,
    client: Optional[Any] = None,
) -> SingleRecordResult:
    source_text = clean_text(source_text)
    reference_text = clean_text(reference_text)
    source_language = clean_text(source_language)
    source_language_code = clean_text(source_language_code).lower()
    target_language = clean_text(target_language) or "English"

    if not source_text:
        raise ValueError("source_text is required")
    if not reference_text:
        raise ValueError("reference_text (ground truth translation) is required")
    if not source_language:
        raise ValueError("source_language is required")
    if not source_language_code:
        raise ValueError("source_language_code is required")

    prompt_path = resolve_translation_prompt_path(
        source_language_code=source_language_code,
        source_language=source_language,
    )

    azure_client = client or build_client()
    translation_result = translate_one(
        client=azure_client,
        source_text=source_text,
        source_language=source_language,
        source_language_code=source_language_code,
        max_completion_tokens=max_completion_tokens,
        retry_count=retry_count,
        retry_sleep=retry_sleep,
        target_language=target_language,
    )

    llm_translation = translation_result["translation"]
    if translation_result["status"] == "success" and llm_translation:
        metrics = score_single_translation(llm_translation, reference_text, source_text)
    else:
        metrics = _empty_metrics()

    return SingleRecordResult(
        source_text=source_text,
        reference_text=reference_text,
        source_language=source_language,
        source_language_code=source_language_code,
        target_language=target_language,
        llm_translation=llm_translation,
        translation_status=translation_result["status"],
        translation_error=translation_result["error"],
        prompt_path=str(prompt_path.resolve()),
        model=config.AZURE_OPENAI_DEPLOYMENT,
        latency_seconds=translation_result["latency"],
        input_tokens=translation_result["input_tokens"],
        output_tokens=translation_result["output_tokens"],
        total_tokens=translation_result["total_tokens"],
        metrics=metrics,
    )


# ============================================================
# CLI
# ============================================================

def print_result(result: SingleRecordResult) -> None:
    print("\n==================== SINGLE RECORD RESULT ====================")
    print(f"Source language: {result.source_language} ({result.source_language_code})")
    print(f"Target language: {result.target_language}")
    print(f"Model: {result.model}")
    print(f"Prompt: {result.prompt_path}")
    print(f"Status: {result.translation_status}")
    if result.translation_error:
        print(f"Error: {result.translation_error}")
    print("\nSource text:")
    print(result.source_text)
    print("\nGround truth:")
    print(result.reference_text)
    print("\nLLM translation:")
    print(result.llm_translation or "(empty)")
    print("\nMetrics:")
    for key, value in asdict(result.metrics).items():
        print(f"  {key}: {value}")
    print(f"\nLatency: {result.latency_seconds}s")
    print(
        f"Tokens: in={result.input_tokens}, out={result.output_tokens}, "
        f"total={result.total_tokens}"
    )
    print("==============================================================")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate and evaluate a single literary text record."
    )
    parser.add_argument("--source-text", required=True, help="Original text to translate")
    parser.add_argument(
        "--reference-text",
        required=True,
        help="Ground truth English translation used for evaluation",
    )
    parser.add_argument(
        "--source-language", required=True, help="Source language name, e.g. French"
    )
    parser.add_argument(
        "--source-language-code", required=True, help="Source language code, e.g. fr"
    )
    parser.add_argument(
        "--target-language",
        default="English",
        help="Target language name (default: English)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument("--output", help="Optional path to save JSON result")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        result = translate_and_evaluate_single(
            source_text=args.source_text,
            reference_text=args.reference_text,
            source_language=args.source_language,
            source_language_code=args.source_language_code,
            target_language=args.target_language,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Saved result to {output_path.resolve()}")

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_result(result)

    return 0 if result.translation_status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
