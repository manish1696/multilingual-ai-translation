"""AI translation engine.

Split into focused modules:

- `config`         constants & env-driven settings (Azure, prompts, scoring, presets)
- `client`         Azure OpenAI client factory
- `text_utils`     text normalisation helpers
- `prompts`        prompt-file resolution & message building
- `translator`     single-call translation with retry
- `scoring`        BLEU/chrF/token-F1/length/adequacy scoring primitives
- `metrics`        DataFrame-level scoring (`add_row_level_scores`, `calculate_metrics`)
- `single_record`  `translate_and_evaluate_single` for the API and demo UIs
- `batch_pipeline` CSV-in/CSV-out CLI pipeline
"""

from . import config
from .client import build_client
from .prompts import (
    load_translation_prompt,
    make_messages,
    resolve_translation_prompt_path,
)
from .scoring import (
    composite_translation_score,
    compute_adequacy_score,
    get_validation_method,
    is_good_translation,
    length_ratio_score,
    token_f1_score,
)
from .single_record import (
    SingleRecordMetrics,
    SingleRecordResult,
    score_single_translation,
    translate_and_evaluate_single,
)
from .text_utils import clean_text, normalize_content_tokens, normalize_for_exact_match
from .translator import translate_one

__all__ = [
    "config",
    "build_client",
    "load_translation_prompt",
    "make_messages",
    "resolve_translation_prompt_path",
    "composite_translation_score",
    "compute_adequacy_score",
    "get_validation_method",
    "is_good_translation",
    "length_ratio_score",
    "token_f1_score",
    "SingleRecordMetrics",
    "SingleRecordResult",
    "score_single_translation",
    "translate_and_evaluate_single",
    "clean_text",
    "normalize_content_tokens",
    "normalize_for_exact_match",
    "translate_one",
]
