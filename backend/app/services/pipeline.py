from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ai import config as ai_config
from ai.config import LANGUAGE_PRESETS as _LANGUAGE_PRESETS
from ai.routing import translate_routed
from ai.single_record import _empty_metrics, score_single_translation

from ..config import get_settings

settings = get_settings()
ai_config.PROMPT_DIR = str(settings.prompts_dir)
LANGUAGE_PRESETS: dict[str, dict[str, str]] = dict(_LANGUAGE_PRESETS)


def get_language_presets() -> list[dict[str, str]]:
    return [
        {"label": label, "name": data["name"], "code": data["code"]}
        for label, data in LANGUAGE_PRESETS.items()
    ]


def run_translation(
    *, source_text: str, source_language: str, source_language_code: str,
    target_language: str, target_language_code: str,
) -> dict[str, Any]:
    routed = translate_routed(
        source_text=source_text, source_language=source_language,
        source_language_code=source_language_code, target_language=target_language,
        target_language_code=target_language_code,
    )
    return _response_payload(routed.to_dict(), "", asdict(_empty_metrics()))


def run_translation_and_evaluation(
    *, source_text: str, reference_text: str, source_language: str,
    source_language_code: str, target_language: str = "English",
    target_language_code: str = "en",
) -> dict[str, Any]:
    routed = translate_routed(
        source_text=source_text, source_language=source_language,
        source_language_code=source_language_code, target_language=target_language,
        target_language_code=target_language_code,
    )
    metrics = (
        score_single_translation(routed.translated_text, reference_text, source_text)
        if routed.status == "success" else _empty_metrics()
    )
    return _response_payload(routed.to_dict(), reference_text, asdict(metrics))


def _response_payload(
    routed: dict[str, Any], reference_text: str, metrics: dict[str, Any]
) -> dict[str, Any]:
    stages = routed["stages"]
    return {
        "source_text": routed["source_text"],
        "reference_text": reference_text,
        "source_language": routed["source_language"],
        "source_language_code": routed["source_language_code"],
        "target_language": routed["target_language"],
        "target_language_code": routed["target_language_code"],
        "llm_translation": routed["translated_text"],
        "translation_status": routed["status"],
        "translation_error": routed["error"],
        "prompt_path": stages[-1]["prompt_path"] if stages else "identity",
        "model": routed["model"],
        "latency_seconds": routed["latency_seconds"],
        "input_tokens": routed["input_tokens"],
        "output_tokens": routed["output_tokens"],
        "total_tokens": routed["total_tokens"],
        "metrics": metrics,
        "strategy": routed["strategy"],
        "route": routed["route"],
        "pivot_translation": routed["pivot_translation"],
        "stages": stages,
    }
