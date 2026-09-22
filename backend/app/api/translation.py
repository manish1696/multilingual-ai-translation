from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, status

from ..schemas import (
    EvaluationRequest, LanguagePreset, LanguagesResponse,
    TranslationRequest, TranslationResponse,
)
from ..services import get_language_presets, run_translation, run_translation_and_evaluation

router = APIRouter(prefix="/translation", tags=["translation"])


@router.get("/languages", response_model=LanguagesResponse)
def list_languages() -> LanguagesResponse:
    return LanguagesResponse(
        presets=[LanguagePreset(**item) for item in get_language_presets()]
    )


@router.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest) -> TranslationResponse:
    return _execute(lambda: run_translation(
        source_text=payload.source_text,
        source_language=payload.source_language,
        source_language_code=payload.source_language_code,
        target_language=payload.target_language,
        target_language_code=payload.target_language_code,
    ))


@router.post(
    "/evaluate", response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
)
def evaluate_translation(payload: EvaluationRequest) -> TranslationResponse:
    return _execute(lambda: run_translation_and_evaluation(
        source_text=payload.source_text,
        reference_text=payload.reference_text,
        source_language=payload.source_language,
        source_language_code=payload.source_language_code,
        target_language=payload.target_language,
        target_language_code=payload.target_language_code,
    ))


def _execute(operation: Callable[[], dict]) -> TranslationResponse:
    try:
        return TranslationResponse(**operation())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Translation pipeline failed") from exc
