from __future__ import annotations

import re
from typing import Optional

from . import config
from .text_utils import normalize_content_tokens


def token_f1_score(prediction: str, reference: str) -> float:
    prediction_tokens = set(normalize_content_tokens(prediction))
    reference_tokens = set(normalize_content_tokens(reference))

    if not prediction_tokens and not reference_tokens:
        return 1.0
    if not prediction_tokens or not reference_tokens:
        return 0.0

    common_tokens = prediction_tokens & reference_tokens
    precision = len(common_tokens) / len(prediction_tokens)
    recall = len(common_tokens) / len(reference_tokens)
    if precision + recall == 0:
        return 0.0

    return round((2 * precision * recall) / (precision + recall), 4)


def length_ratio_score(prediction: str, reference: str) -> float:
    prediction_length = len(normalize_content_tokens(prediction))
    reference_length = len(normalize_content_tokens(reference))

    if prediction_length == 0 and reference_length == 0:
        return 1.0
    if prediction_length == 0 or reference_length == 0:
        return 0.0

    return round(
        min(prediction_length, reference_length) / max(prediction_length, reference_length),
        4,
    )


def composite_translation_score(
    sentence_bleu: Optional[float],
    sentence_chrf: Optional[float],
) -> Optional[float]:
    """Legacy diagnostic score kept for CSV comparison."""
    if sentence_bleu is None or sentence_chrf is None:
        return None
    return round((0.35 * sentence_bleu) + (0.65 * sentence_chrf), 4)


def compute_adequacy_score(
    sentence_chrf: Optional[float],
    token_f1: Optional[float],
    length_ratio: Optional[float],
) -> Optional[float]:
    if sentence_chrf is None or token_f1 is None or length_ratio is None:
        return None

    return round(
        (config.ADEQUACY_CHRF_WEIGHT * (sentence_chrf / 100.0))
        + (config.ADEQUACY_TOKEN_F1_WEIGHT * token_f1)
        + (config.ADEQUACY_LENGTH_RATIO_WEIGHT * length_ratio),
        4,
    )


def is_good_translation(
    exact_match: bool,
    sentence_chrf: Optional[float],
    token_f1: Optional[float],
    length_ratio: Optional[float],
    adequacy_score: Optional[float],
) -> bool:
    if exact_match:
        return True

    if adequacy_score is None or sentence_chrf is None or token_f1 is None:
        return False

    if adequacy_score < config.GOOD_TRANSLATION_ADEQUACY_MIN:
        return False

    return (
        sentence_chrf >= config.GOOD_TRANSLATION_CHRF_FLOOR
        or token_f1 >= config.GOOD_TRANSLATION_TOKEN_F1_FLOOR
    )


def get_validation_method() -> str:
    return (
        f"adequacy>={config.GOOD_TRANSLATION_ADEQUACY_MIN} "
        f"({config.ADEQUACY_CHRF_WEIGHT}*chrF + "
        f"{config.ADEQUACY_TOKEN_F1_WEIGHT}*token_f1 + "
        f"{config.ADEQUACY_LENGTH_RATIO_WEIGHT}*length_ratio), "
        f"with chrF>={config.GOOD_TRANSLATION_CHRF_FLOOR} or "
        f"token_f1>={config.GOOD_TRANSLATION_TOKEN_F1_FLOOR}"
    )


_ENTITY_PATTERN = re.compile(
    r"(?:\b\d+(?:[.,:/-]\d+)*\b|[$€£₹¥]\s?\d+(?:[.,]\d+)*)"
)


def entity_preservation_score(source: str, prediction: str) -> float:
    """Measure preservation of deterministic numeric/currency entities."""
    source_entities = _ENTITY_PATTERN.findall(source)
    if not source_entities:
        return 1.0
    prediction_entities = _ENTITY_PATTERN.findall(prediction)
    remaining = list(prediction_entities)
    preserved = 0
    for entity in source_entities:
        if entity in remaining:
            preserved += 1
            remaining.remove(entity)
    return round(preserved / len(source_entities), 4)


def quality_score_v2(
    semantic_score: Optional[float],
    sentence_chrf: Optional[float],
    token_f1: Optional[float],
    length_ratio: Optional[float],
    entity_score: Optional[float],
) -> Optional[float]:
    values = (semantic_score, sentence_chrf, token_f1, length_ratio, entity_score)
    if any(value is None for value in values):
        return None
    return round(
        config.QUALITY_SEMANTIC_WEIGHT * semantic_score
        + config.QUALITY_CHRF_WEIGHT * (sentence_chrf / 100.0)
        + config.QUALITY_TOKEN_F1_WEIGHT * token_f1
        + config.QUALITY_LENGTH_WEIGHT * length_ratio
        + config.QUALITY_ENTITY_WEIGHT * entity_score,
        4,
    )


def passes_quality_threshold(
    quality_score: Optional[float], semantic_score: Optional[float]
) -> bool:
    return bool(
        quality_score is not None
        and semantic_score is not None
        and quality_score >= config.QUALITY_PASS_MIN
        and semantic_score >= config.QUALITY_SEMANTIC_FLOOR
    )
