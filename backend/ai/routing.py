"""English-hub route planning and execution for many-to-many translation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from . import config
from .client import build_client
from .prompts import resolve_translation_prompt_path
from .text_utils import clean_text
from .translator import translate_one


@dataclass
class TranslationStage:
    source_language: str
    source_language_code: str
    target_language: str
    target_language_code: str
    translation: str
    status: str
    error: str
    prompt_path: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class RoutedTranslation:
    source_text: str
    translated_text: str
    source_language: str
    source_language_code: str
    target_language: str
    target_language_code: str
    strategy: str
    route: list[str]
    pivot_translation: Optional[str]
    status: str
    error: str
    model: str
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    stages: list[TranslationStage]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["stages"] = [asdict(stage) for stage in self.stages]
        return payload


def plan_route(source_code: str, target_code: str) -> tuple[str, list[str]]:
    source_code = clean_text(source_code).lower()
    target_code = clean_text(target_code).lower()
    if source_code not in config.SUPPORTED_LANGUAGE_CODES:
        raise ValueError(f"Unsupported source language code: {source_code}")
    if target_code not in config.SUPPORTED_LANGUAGE_CODES:
        raise ValueError(f"Unsupported target language code: {target_code}")
    if source_code == target_code:
        return "identity", [source_code]
    if "en" in (source_code, target_code):
        return "direct", [source_code, target_code]
    return "english_pivot", [source_code, "en", target_code]


def _execute_stage(
    *, client: Any, text: str, source_language: str, source_code: str,
    target_language: str, target_code: str, max_completion_tokens: int,
    retry_count: int, retry_sleep: float,
) -> TranslationStage:
    prompt_path: Path = resolve_translation_prompt_path(source_code, source_language)
    result = translate_one(
        client=client,
        source_text=text,
        source_language=source_language,
        source_language_code=source_code,
        target_language=target_language,
        max_completion_tokens=max_completion_tokens,
        retry_count=retry_count,
        retry_sleep=retry_sleep,
    )
    return TranslationStage(
        source_language=source_language,
        source_language_code=source_code,
        target_language=target_language,
        target_language_code=target_code,
        translation=result["translation"],
        status=result["status"],
        error=result["error"],
        prompt_path=str(prompt_path.resolve()),
        latency_seconds=result["latency"],
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        total_tokens=result["total_tokens"],
    )


def translate_routed(
    *, source_text: str, source_language: str, source_language_code: str,
    target_language: str, target_language_code: str,
    max_completion_tokens: int = config.DEFAULT_MAX_COMPLETION_TOKENS,
    retry_count: int = config.DEFAULT_RETRY_COUNT,
    retry_sleep: float = config.DEFAULT_RETRY_SLEEP,
    client: Optional[Any] = None,
) -> RoutedTranslation:
    source_text = clean_text(source_text)
    source_language = clean_text(source_language)
    target_language = clean_text(target_language)
    source_code = clean_text(source_language_code).lower()
    target_code = clean_text(target_language_code).lower()
    if not source_text:
        raise ValueError("source_text is required")
    if not source_language or not target_language:
        raise ValueError("source_language and target_language are required")

    strategy, route = plan_route(source_code, target_code)
    if strategy == "identity":
        return RoutedTranslation(
            source_text, source_text, source_language, source_code,
            target_language, target_code, strategy, route, None, "success", "",
            config.AZURE_OPENAI_DEPLOYMENT, 0.0, 0, 0, 0, [],
        )

    azure_client = client or build_client()
    stages: list[TranslationStage] = []
    if strategy == "direct":
        stages.append(_execute_stage(
            client=azure_client, text=source_text,
            source_language=source_language, source_code=source_code,
            target_language=target_language, target_code=target_code,
            max_completion_tokens=max_completion_tokens,
            retry_count=retry_count, retry_sleep=retry_sleep,
        ))
    else:
        first = _execute_stage(
            client=azure_client, text=source_text,
            source_language=source_language, source_code=source_code,
            target_language="English", target_code="en",
            max_completion_tokens=max_completion_tokens,
            retry_count=retry_count, retry_sleep=retry_sleep,
        )
        stages.append(first)
        if first.status == "success" and first.translation:
            stages.append(_execute_stage(
                client=azure_client, text=first.translation,
                source_language="English", source_code="en",
                target_language=target_language, target_code=target_code,
                max_completion_tokens=max_completion_tokens,
                retry_count=retry_count, retry_sleep=retry_sleep,
            ))

    final = stages[-1]
    success = len(stages) == len(route) - 1 and all(s.status == "success" for s in stages)
    errors = "; ".join(s.error for s in stages if s.error)
    return RoutedTranslation(
        source_text=source_text,
        translated_text=final.translation if success else "",
        source_language=source_language,
        source_language_code=source_code,
        target_language=target_language,
        target_language_code=target_code,
        strategy=strategy,
        route=route,
        pivot_translation=stages[0].translation if strategy == "english_pivot" else None,
        status="success" if success else "failed",
        error=errors or ("Translation route did not complete" if not success else ""),
        model=config.AZURE_OPENAI_DEPLOYMENT,
        latency_seconds=round(sum(s.latency_seconds for s in stages), 3),
        input_tokens=sum(s.input_tokens for s in stages),
        output_tokens=sum(s.output_tokens for s in stages),
        total_tokens=sum(s.total_tokens for s in stages),
        stages=stages,
    )
