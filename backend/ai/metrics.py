from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import sacrebleu

from . import config
from .scoring import (
    composite_translation_score,
    compute_adequacy_score,
    get_validation_method,
    is_good_translation,
    length_ratio_score,
    token_f1_score,
)
from .text_utils import clean_text, normalize_for_exact_match


def ensure_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        config.OUTPUT_TRANSLATION_COL: "",
        config.OUTPUT_STATUS_COL: "",
        config.OUTPUT_ERROR_COL: "",
        config.OUTPUT_LATENCY_COL: "",
        config.OUTPUT_INPUT_TOKENS_COL: 0,
        config.OUTPUT_OUTPUT_TOKENS_COL: 0,
        config.OUTPUT_TOTAL_TOKENS_COL: 0,
    }

    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    return df


def is_already_done(row: pd.Series) -> bool:
    status = clean_text(row.get(config.OUTPUT_STATUS_COL)).lower()
    translation = clean_text(row.get(config.OUTPUT_TRANSLATION_COL))
    return status == "success" and bool(translation)


def add_row_level_scores(
    df: pd.DataFrame,
    target_col: str,
    prediction_col: str,
) -> pd.DataFrame:
    sentence_bleu_values = []
    sentence_chrf_values = []
    exact_match_values = []
    composite_score_values = []
    token_f1_values = []
    length_ratio_values = []
    adequacy_score_values = []
    good_translation_values = []

    for _, row in df.iterrows():
        pred = clean_text(row.get(prediction_col))
        ref = clean_text(row.get(target_col))
        status = clean_text(row.get(config.OUTPUT_STATUS_COL)).lower()

        if status != "success" or not pred or not ref:
            sentence_bleu_values.append(None)
            sentence_chrf_values.append(None)
            exact_match_values.append(False)
            composite_score_values.append(None)
            token_f1_values.append(None)
            length_ratio_values.append(None)
            adequacy_score_values.append(None)
            good_translation_values.append(False)
            continue

        sentence_bleu = round(sacrebleu.sentence_bleu(pred, [ref]).score, 4)
        sentence_chrf = round(sacrebleu.sentence_chrf(pred, [ref]).score, 4)
        exact_match = normalize_for_exact_match(pred) == normalize_for_exact_match(ref)
        composite_score = composite_translation_score(sentence_bleu, sentence_chrf)
        token_f1 = token_f1_score(pred, ref)
        length_ratio = length_ratio_score(pred, ref)
        adequacy_score = compute_adequacy_score(sentence_chrf, token_f1, length_ratio)

        sentence_bleu_values.append(sentence_bleu)
        sentence_chrf_values.append(sentence_chrf)
        exact_match_values.append(exact_match)
        composite_score_values.append(composite_score)
        token_f1_values.append(token_f1)
        length_ratio_values.append(length_ratio)
        adequacy_score_values.append(adequacy_score)
        good_translation_values.append(
            is_good_translation(
                exact_match, sentence_chrf, token_f1, length_ratio, adequacy_score
            )
        )

    df["sentence_bleu"] = sentence_bleu_values
    df["sentence_chrf"] = sentence_chrf_values
    df["exact_match"] = exact_match_values
    df["composite_score"] = composite_score_values
    df[config.OUTPUT_TOKEN_F1_COL] = token_f1_values
    df[config.OUTPUT_LENGTH_RATIO_COL] = length_ratio_values
    df[config.OUTPUT_ADEQUACY_SCORE_COL] = adequacy_score_values
    df[config.OUTPUT_GOOD_TRANSLATION_COL] = good_translation_values

    return df


def calculate_metrics(
    df: pd.DataFrame,
    target_col: str,
    prediction_col: str,
) -> Dict[str, Any]:
    scored_df = df[
        (df[config.OUTPUT_STATUS_COL].astype(str).str.lower() == "success")
        & (df[prediction_col].astype(str).str.strip() != "")
        & (df[target_col].astype(str).str.strip() != "")
    ].copy()

    good_translation_count = int(
        df[config.OUTPUT_GOOD_TRANSLATION_COL].fillna(False).astype(bool).sum()
    )
    records_total = int(len(df))
    adequacy_scores = pd.to_numeric(
        df[config.OUTPUT_ADEQUACY_SCORE_COL], errors="coerce"
    ).dropna()
    average_adequacy_score = (
        round(float(adequacy_scores.mean()), 4) if not adequacy_scores.empty else 0.0
    )

    base = {
        "records_total": records_total,
        "records_failed": int(
            (df[config.OUTPUT_STATUS_COL].astype(str).str.lower() == "failed").sum()
        ),
        "average_adequacy_score": average_adequacy_score,
        "good_translation_count": good_translation_count,
        "accuracy": f"{good_translation_count}/{records_total}",
        "validation_method": get_validation_method(),
        "total_input_tokens": int(
            pd.to_numeric(df[config.OUTPUT_INPUT_TOKENS_COL], errors="coerce").fillna(0).sum()
        ),
        "total_output_tokens": int(
            pd.to_numeric(df[config.OUTPUT_OUTPUT_TOKENS_COL], errors="coerce").fillna(0).sum()
        ),
        "total_tokens": int(
            pd.to_numeric(df[config.OUTPUT_TOTAL_TOKENS_COL], errors="coerce").fillna(0).sum()
        ),
    }

    if scored_df.empty:
        return {
            **base,
            "records_scored": 0,
            "exact_match_count": 0,
            "exact_match_rate": 0.0,
            "corpus_bleu": 0.0,
            "corpus_chrf": 0.0,
            "average_sentence_bleu": 0.0,
            "average_sentence_chrf": 0.0,
            "accuracy_rate": 0.0,
        }

    predictions = [clean_text(x) for x in scored_df[prediction_col].tolist()]
    references = [clean_text(x) for x in scored_df[target_col].tolist()]

    exact_matches = [
        normalize_for_exact_match(pred) == normalize_for_exact_match(ref)
        for pred, ref in zip(predictions, references)
    ]

    sentence_bleu_scores = [
        sacrebleu.sentence_bleu(pred, [ref]).score
        for pred, ref in zip(predictions, references)
    ]

    sentence_chrf_scores = [
        sacrebleu.sentence_chrf(pred, [ref]).score
        for pred, ref in zip(predictions, references)
    ]

    return {
        **base,
        "records_scored": int(len(scored_df)),
        "exact_match_count": int(sum(exact_matches)),
        "exact_match_rate": round(float(sum(exact_matches) / len(exact_matches)), 4),
        "corpus_bleu": round(
            float(sacrebleu.corpus_bleu(predictions, [references]).score), 4
        ),
        "corpus_chrf": round(
            float(sacrebleu.corpus_chrf(predictions, [references]).score), 4
        ),
        "average_sentence_bleu": round(
            float(sum(sentence_bleu_scores) / len(sentence_bleu_scores)), 4
        ),
        "average_sentence_chrf": round(
            float(sum(sentence_chrf_scores) / len(sentence_chrf_scores)), 4
        ),
        "accuracy_rate": round(float(good_translation_count / records_total), 4),
    }
