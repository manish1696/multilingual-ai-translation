"""Batch CSV pipeline: translate every row of a CSV and compute corpus metrics.

This module preserves the CLI behaviour of the original
`azure_translate_and_score.py`, including the "direct run" config block at the
bottom that lets you launch a batch job with `python -m backend.ai.batch_pipeline`.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from tqdm import tqdm

from . import config
from .client import build_client
from .metrics import (
    add_row_level_scores,
    calculate_metrics,
    ensure_output_columns,
    is_already_done,
)
from .prompts import resolve_translation_prompt_path
from .text_utils import clean_text
from .translator import translate_one


# ============================================================
# Row-level helpers
# ============================================================

def get_language_name(row: pd.Series, args: argparse.Namespace) -> str:
    if args.source_language:
        return args.source_language

    if args.source_lang_col in row and clean_text(row.get(args.source_lang_col)):
        return clean_text(row.get(args.source_lang_col))

    if args.source_lang_code_col in row and clean_text(row.get(args.source_lang_code_col)):
        return clean_text(row.get(args.source_lang_code_col))

    return "the source language"


def get_language_code(row: pd.Series, args: argparse.Namespace) -> str:
    if args.source_lang_code_col in row and clean_text(row.get(args.source_lang_code_col)):
        return clean_text(row.get(args.source_lang_code_col)).lower()

    return ""


# ============================================================
# Output writers
# ============================================================

def save_results(
    df: pd.DataFrame,
    output_path: Path,
    args: argparse.Namespace,
    metrics: Dict[str, Any],
) -> None:
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    if args.excel:
        excel_path = output_path.with_suffix(".xlsx")
        df.to_excel(excel_path, index=False)
        print(f"Excel output saved: {excel_path}")

    metrics_path = output_path.with_name(output_path.stem + "_metrics.json")
    metrics_path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    metrics_csv_path = output_path.with_name(output_path.stem + "_metrics.csv")
    pd.DataFrame([metrics]).to_csv(metrics_csv_path, index=False, encoding="utf-8-sig")

    print("\n==================== METRICS ====================")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print("=================================================")

    print(f"\nOutput CSV saved: {output_path}")
    print(f"Metrics JSON saved: {metrics_path}")
    print(f"Metrics CSV saved: {metrics_csv_path}")


def rescore_existing_output(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    if not output_path.exists():
        raise FileNotFoundError(
            f"Output CSV not found for score-only mode: {output_path}\n"
            "Run a full translation first, or set SCORE_ONLY = False."
        )

    print(f"Score-only mode: recalculating metrics from {output_path}")
    df = pd.read_csv(output_path)

    if args.target_col not in df.columns:
        raise ValueError(
            f"Target column '{args.target_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    if config.OUTPUT_TRANSLATION_COL not in df.columns:
        raise ValueError(
            f"Translation column '{config.OUTPUT_TRANSLATION_COL}' not found. "
            "This file does not contain existing translations to score."
        )

    df = ensure_output_columns(df)

    if args.max_rows:
        df = df.head(args.max_rows).copy()

    print(f"Total rows: {len(df)}")

    df = add_row_level_scores(
        df=df,
        target_col=args.target_col,
        prediction_col=config.OUTPUT_TRANSLATION_COL,
    )

    metrics = calculate_metrics(
        df=df,
        target_col=args.target_col,
        prediction_col=config.OUTPUT_TRANSLATION_COL,
    )

    save_results(df, output_path, args, metrics)


# ============================================================
# Main pipeline
# ============================================================

def run_pipeline(args: argparse.Namespace) -> None:
    if args.score_only:
        rescore_existing_output(args)
        return

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    if output_path.exists() and not args.force:
        print(f"Resuming from existing output file: {output_path}")
        df = pd.read_csv(output_path)
    else:
        print(f"Reading input file: {input_path}")
        df = pd.read_csv(input_path)

    if args.source_col not in df.columns:
        raise ValueError(
            f"Source column '{args.source_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    if args.target_col not in df.columns:
        raise ValueError(
            f"Target column '{args.target_col}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    df = ensure_output_columns(df)

    if args.max_rows:
        df = df.head(args.max_rows).copy()

    client = build_client()

    print(f"Total rows: {len(df)}")
    print(f"Azure endpoint: {config.AZURE_OPENAI_ENDPOINT}")
    print(f"Azure deployment: {config.AZURE_OPENAI_DEPLOYMENT}")
    print(f"API version: {config.AZURE_OPENAI_API_VERSION}")
    print(f"Prompt folder: {Path(config.PROMPT_DIR).resolve()}")
    print(f"Output file: {output_path}")

    if len(df) > 0:
        sample_row = df.iloc[0]
        sample_language = get_language_name(sample_row, args)
        sample_language_code = get_language_code(sample_row, args)
        prompt_path = resolve_translation_prompt_path(
            source_language_code=sample_language_code,
            source_language=sample_language,
        )
        print(
            f"Translation prompt for this data "
            f"({sample_language_code or sample_language}): {prompt_path.resolve()}"
        )

    processed_since_save = 0

    for idx in tqdm(range(len(df)), desc="Translating rows"):
        row = df.iloc[idx]

        if not args.retranslate_success and is_already_done(row):
            continue

        source_text = clean_text(row.get(args.source_col))
        if not source_text:
            df.at[idx, config.OUTPUT_STATUS_COL] = "skipped"
            df.at[idx, config.OUTPUT_ERROR_COL] = "empty source_text"
            continue

        source_language = get_language_name(row, args)
        source_language_code = get_language_code(row, args)

        result = translate_one(
            client=client,
            source_text=source_text,
            source_language=source_language,
            source_language_code=source_language_code,
            max_completion_tokens=args.max_completion_tokens,
            retry_count=args.retry_count,
            retry_sleep=args.retry_sleep,
        )

        df.at[idx, config.OUTPUT_TRANSLATION_COL] = result["translation"]
        df.at[idx, config.OUTPUT_STATUS_COL] = result["status"]
        df.at[idx, config.OUTPUT_ERROR_COL] = result["error"]
        df.at[idx, config.OUTPUT_LATENCY_COL] = result["latency"]
        df.at[idx, config.OUTPUT_INPUT_TOKENS_COL] = result["input_tokens"]
        df.at[idx, config.OUTPUT_OUTPUT_TOKENS_COL] = result["output_tokens"]
        df.at[idx, config.OUTPUT_TOTAL_TOKENS_COL] = result["total_tokens"]

        processed_since_save += 1

        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

        if processed_since_save >= args.save_every:
            df.to_csv(output_path, index=False, encoding="utf-8-sig")
            processed_since_save = 0

    df = add_row_level_scores(
        df=df,
        target_col=args.target_col,
        prediction_col=config.OUTPUT_TRANSLATION_COL,
    )

    metrics = calculate_metrics(
        df=df,
        target_col=args.target_col,
        prediction_col=config.OUTPUT_TRANSLATION_COL,
    )

    save_results(df, output_path, args, metrics)


# ============================================================
# Direct run configuration
# ============================================================

INPUT_CSV_PATH = "data/output_opus_books_10_languages/el_to_en_opus_books_1000.csv"
OUTPUT_CSV_PATH = "data/results/el_to_en_gpt54mini_output.csv"

SOURCE_COL = "source_text"
TARGET_COL = "target_text"
SOURCE_LANG_COL = "source_language"
SOURCE_LANG_CODE_COL = "source_language_code"

# Keep None if source_language column is already present in CSV.
# Example: "French", "Hindi", "Egyptian Arabic"
SOURCE_LANGUAGE = None

# Use None for full file, or use 10/50/100 for testing.
MAX_ROWS = None

MAX_COMPLETION_TOKENS = 2048
SAVE_EVERY = 10
SLEEP_SECONDS = 0.0

RETRY_COUNT = 5
RETRY_SLEEP = 5.0

FORCE = True

# If True, retranslates rows already marked success.
RETRANSLATE_SUCCESS = True

# If True, also creates XLSX output.
SAVE_EXCEL = True

# If True, skip translation and only recalculate scores/metrics on existing output CSV.
SCORE_ONLY = False


def get_default_config() -> argparse.Namespace:
    return argparse.Namespace(
        input=INPUT_CSV_PATH,
        output=OUTPUT_CSV_PATH,
        source_col=SOURCE_COL,
        target_col=TARGET_COL,
        source_lang_col=SOURCE_LANG_COL,
        source_lang_code_col=SOURCE_LANG_CODE_COL,
        source_language=SOURCE_LANGUAGE,
        max_rows=MAX_ROWS,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        save_every=SAVE_EVERY,
        sleep_seconds=SLEEP_SECONDS,
        retry_count=RETRY_COUNT,
        retry_sleep=RETRY_SLEEP,
        force=FORCE,
        retranslate_success=RETRANSLATE_SUCCESS,
        excel=SAVE_EXCEL,
        score_only=SCORE_ONLY,
    )


if __name__ == "__main__":
    run_pipeline(get_default_config())
