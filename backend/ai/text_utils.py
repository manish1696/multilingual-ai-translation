from __future__ import annotations

import re
from typing import Any

from .config import ENGLISH_STOP_WORDS


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_for_exact_match(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\u201c\u201d]", '"', text)
    text = re.sub(r"[\u2018\u2019]", "'", text)
    return text.strip()


def normalize_content_tokens(value: Any) -> list[str]:
    text = normalize_for_exact_match(value)
    text = re.sub(r"[^a-z0-9']+", " ", text)
    return [token for token in text.split() if token and token not in ENGLISH_STOP_WORDS]
