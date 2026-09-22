"""
Create 10 separate translation evaluation files from Helsinki-NLP/opus_books.

Each output file contains 1,000 records from one source language to English.

Selected OPUS Books languages:
    hu -> en  Hungarian
    fr -> en  French
    es -> en  Spanish
    de -> en  German
    nl -> en  Dutch
    it -> en  Italian
    ru -> en  Russian
    fi -> en  Finnish
    no -> en  Norwegian
    sv -> en  Swedish

Install:
    pip install datasets pandas openpyxl tqdm

Run:
    python extract_opus_books_10_to_english.py

Outputs:
    data/output_opus_books_10_languages/
        hu_to_en_opus_books_1000.csv
        hu_to_en_opus_books_1000.xlsx
        ...
        sv_to_en_opus_books_1000.csv
        sv_to_en_opus_books_1000.xlsx
        combined_manifest.csv
        combined_all_languages_10000.csv

Notes:
    - The OPUS Books config can be either en-xx or xx-en.
    - This script always writes source_text as the non-English language
      and target_text as English.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm

DATASET_ID = "Helsinki-NLP/opus_books"
HF_URL = f"https://huggingface.co/datasets/{DATASET_ID}"
TARGET_ROWS_PER_LANGUAGE = 1000
OUTPUT_DIR = Path("data/output_opus_books_10_languages")

LANGUAGES: List[Dict[str, object]] = [
    {"language_name": "Hungarian", "source_language_code": "hu", "config": "en-hu"},
    {"language_name": "French (Europe)", "source_language_code": "fr", "config": "en-fr"},
    {"language_name": "Spanish (Europe)", "source_language_code": "es", "config": "en-es"},
    {"language_name": "German (Europe)", "source_language_code": "de", "config": "de-en"},
    {"language_name": "Dutch", "source_language_code": "nl", "config": "en-nl"},
    {"language_name": "Italian", "source_language_code": "it", "config": "en-it"},
    {"language_name": "Russian", "source_language_code": "ru", "config": "en-ru"},
    {"language_name": "Finnish", "source_language_code": "fi", "config": "en-fi"},
    {"language_name": "Norwegian", "source_language_code": "no", "config": "en-no"},
    {"language_name": "Swedish", "source_language_code": "sv", "config": "en-sv"},
    # Additional OPUS Books languages
    {"language_name": "Greek", "source_language_code": "el", "config": "el-en"},
    {"language_name": "Polish", "source_language_code": "pl", "config": "en-pl"},
    {"language_name": "Portuguese (Europe)", "source_language_code": "pt", "config": "en-pt"},
]


def clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def extract_language(language_name: str, source_code: str, config: str) -> pd.DataFrame:
    dataset = load_dataset(DATASET_ID, config, split="train", streaming=True)

    records = []
    seen_pairs = set()

    for row in tqdm(dataset, desc=f"{source_code}->en"):
        translation = row.get("translation") or {}
        source_text = clean_text(translation.get(source_code))
        target_text = clean_text(translation.get("en"))

        if not source_text or not target_text:
            continue
        if source_text == target_text:
            continue

        pair_key = (source_text, target_text)
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        records.append({
            "row_no": len(records) + 1,
            "record_id": row.get("id"),
            "source_language": language_name,
            "source_language_code": source_code,
            "target_language": "English",
            "target_language_code": "en",
            "source_text": source_text,
            "target_text": target_text,
            "dataset": DATASET_ID,
            "config": config,
            "split": "train",
            "source_url": HF_URL,
        })

        if len(records) >= TARGET_ROWS_PER_LANGUAGE:
            break

    if len(records) < TARGET_ROWS_PER_LANGUAGE:
        raise RuntimeError(
            f"Only found {len(records)} rows for {language_name} ({source_code}->en). "
            f"Expected {TARGET_ROWS_PER_LANGUAGE}."
        )

    return pd.DataFrame(records)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    combined_frames = []

    for item in LANGUAGES:
        language_name = str(item["language_name"])
        source_code = str(item["source_language_code"])
        config = str(item["config"])

        df = extract_language(language_name, source_code, config)

        csv_path = OUTPUT_DIR / f"{source_code}_to_en_opus_books_1000.csv"
        xlsx_path = OUTPUT_DIR / f"{source_code}_to_en_opus_books_1000.xlsx"

        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        df.to_excel(xlsx_path, index=False)

        combined_frames.append(df)
        manifest_rows.append({
            "language_name": language_name,
            "source_language_code": source_code,
            "target_language_code": "en",
            "config": config,
            "records": len(df),
            "csv_file": csv_path.name,
            "xlsx_file": xlsx_path.name,
            "source_url": HF_URL,
        })

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_csv(OUTPUT_DIR / "combined_manifest.csv", index=False, encoding="utf-8-sig")
    manifest_df.to_excel(OUTPUT_DIR / "combined_manifest.xlsx", index=False)

    combined_df = pd.concat(combined_frames, ignore_index=True)
    combined_df.to_csv(OUTPUT_DIR / "combined_all_languages_10000.csv", index=False, encoding="utf-8-sig")
    combined_df.to_excel(OUTPUT_DIR / "combined_all_languages_10000.xlsx", index=False)

    print(f"Done. Created {len(combined_df)} total rows in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
