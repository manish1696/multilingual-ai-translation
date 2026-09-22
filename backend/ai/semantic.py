"""Lazy multilingual semantic similarity for reference-based evaluation."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from . import config


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(config.SEMANTIC_MODEL_NAME)


def semantic_similarity(prediction: str, reference: str) -> Optional[float]:
    """Return cosine similarity in [0, 1], or None when scoring is disabled."""
    if not config.SEMANTIC_SCORING_ENABLED:
        return None
    try:
        embeddings = _model().encode(
            [prediction, reference], normalize_embeddings=True, convert_to_numpy=True
        )
    except (ImportError, OSError, RuntimeError):
        # The API remains usable when the optional local model is unavailable.
        return None
    similarity = float(embeddings[0] @ embeddings[1])
    return round(max(0.0, min(1.0, similarity)), 4)
