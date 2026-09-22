"""Configuration constants for the AI translation engine.

All values are sourced from environment variables (with sane defaults) so the
engine can be reused by the FastAPI backend, the legacy Streamlit UI, and the
batch CLI without code changes.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# Repository root = parent of `backend/`
_AI_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _AI_DIR.parent
_REPO_ROOT = _BACKEND_DIR.parent

# Load .env files (repo root first, then backend/.env can override).
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env", override=False)


# ============================================================
# Azure OpenAI
# ============================================================

AZURE_OPENAI_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://your-resource.openai.azure.com/",
)
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-mini")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")


def normalize_azure_endpoint(endpoint: str) -> str:
    """Return the Azure OpenAI resource base URL (no path or query string)."""
    cleaned = endpoint.strip().rstrip("/")
    if "?" in cleaned:
        cleaned = cleaned.split("?", 1)[0]
    for suffix in ("/openai/responses", "/openai/v1", "/openai"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned.rstrip("/")


# ============================================================
# Prompt files
# ============================================================

DEFAULT_PROMPTS_DIR = _BACKEND_DIR / "prompts"

# Mutable module-level value so callers (e.g. the backend service) can point
# the engine at a different prompt folder at runtime.
PROMPT_DIR: str = os.getenv("PROMPT_DIR", str(DEFAULT_PROMPTS_DIR))
DEFAULT_PROMPT_FILE = "default_translation_prompt.md"

# When True, look up `<code>_translation_prompt.md` / `<name>_translation_prompt.md`
# before falling back to the default prompt.
USE_LANGUAGE_SPECIFIC_PROMPT = True


# ============================================================
# Output columns (used by the batch CSV pipeline)
# ============================================================

OUTPUT_TRANSLATION_COL = "llm_translation"
OUTPUT_STATUS_COL = "translation_status"
OUTPUT_ERROR_COL = "translation_error"
OUTPUT_LATENCY_COL = "translation_latency_seconds"
OUTPUT_INPUT_TOKENS_COL = "input_tokens"
OUTPUT_OUTPUT_TOKENS_COL = "output_tokens"
OUTPUT_TOTAL_TOKENS_COL = "total_tokens"
OUTPUT_GOOD_TRANSLATION_COL = "good_translation"
OUTPUT_ADEQUACY_SCORE_COL = "adequacy_score"
OUTPUT_TOKEN_F1_COL = "token_f1"
OUTPUT_LENGTH_RATIO_COL = "length_ratio"


# ============================================================
# Scoring weights & thresholds
# ============================================================

# Adequacy-based accuracy (better for literary translation than strict BLEU/chrF).
# Combines chrF, content token overlap (F1), and length similarity.
ADEQUACY_CHRF_WEIGHT = 0.35
ADEQUACY_TOKEN_F1_WEIGHT = 0.45
ADEQUACY_LENGTH_RATIO_WEIGHT = 0.20
GOOD_TRANSLATION_ADEQUACY_MIN = 0.50
GOOD_TRANSLATION_CHRF_FLOOR = 20.0
GOOD_TRANSLATION_TOKEN_F1_FLOOR = 0.20


# ============================================================
# Translation defaults (per call)
# ============================================================

DEFAULT_MAX_COMPLETION_TOKENS = 2048
DEFAULT_RETRY_COUNT = 5
DEFAULT_RETRY_SLEEP = 5.0


# ============================================================
# Language presets (used by the demo UI and the API)
# ============================================================

LANGUAGE_PRESETS: dict[str, dict[str, str]] = {
    "English": {"code": "en", "name": "English"},
    "French": {"code": "fr", "name": "French"},
    "German": {"code": "de", "name": "German"},
    "Spanish (Europe)": {"code": "es", "name": "Spanish (Europe)"},
    "Portuguese (Europe)": {"code": "pt", "name": "Portuguese (Europe)"},
    "Hungarian": {"code": "hu", "name": "Hungarian"},
    "Hindi": {"code": "hi", "name": "Hindi"},
    "Chinese": {"code": "zh", "name": "Chinese"},
    "Egyptian Arabic": {"code": "arz", "name": "Egyptian Arabic"},
    "Japanese": {"code": "ja", "name": "Japanese"},
    "Korean": {"code": "ko", "name": "Korean"},
}

SUPPORTED_LANGUAGE_CODES = frozenset(
    item["code"] for item in LANGUAGE_PRESETS.values()
)

# Semantic evaluation (loaded lazily on the first evaluated request).
SEMANTIC_MODEL_NAME = os.getenv(
    "SEMANTIC_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
SEMANTIC_SCORING_ENABLED = os.getenv("SEMANTIC_SCORING_ENABLED", "true").lower() in {
    "1", "true", "yes", "on"
}

# Quality Score V2. These are heuristic defaults and should be calibrated
# against human-reviewed examples before being described as accuracy.
QUALITY_SEMANTIC_WEIGHT = 0.40
QUALITY_CHRF_WEIGHT = 0.25
QUALITY_TOKEN_F1_WEIGHT = 0.15
QUALITY_LENGTH_WEIGHT = 0.10
QUALITY_ENTITY_WEIGHT = 0.10
QUALITY_PASS_MIN = 0.70
QUALITY_SEMANTIC_FLOOR = 0.70


# ============================================================
# English stop words (used by content-token F1 scoring)
# ============================================================

ENGLISH_STOP_WORDS = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "shall",
        "should", "may", "might", "must", "can", "could", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "and", "or", "but",
        "not", "no", "it", "its", "he", "she", "they", "we", "you", "i", "me",
        "my", "his", "her", "their", "our", "your", "that", "this", "there",
        "then", "than", "so", "if", "when", "up", "out", "into", "over", "after",
        "before", "about", "all", "one", "two",
    }
)
