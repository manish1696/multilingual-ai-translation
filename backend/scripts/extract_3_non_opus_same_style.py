"""
Extract/convert these 3 datasets into the same style as extract_opus_books_10_to_english.py:

1. Chinese -> English
   Dataset: cmots/UniST
   Output: zh_to_en_unist_1000.csv

2. Hindi -> English
   Dataset: ai4bharat/samanantar
   Output: hi_to_en_samanantar_1000.csv

3. Egyptian Arabic -> English
   Dataset: IbrahimAmin/arz-en-parallel-corpus
   Output: arz_to_en_parallel_corpus_1000.csv

All outputs use the same columns as OPUS Books extractor:

    row_no
    record_id
    source_language
    source_language_code
    target_language
    target_language_code
    source_text
    target_text
    dataset
    config
    split
    source_url

Install:
    pip install datasets pandas tqdm

Run:
    python extract_3_non_opus_same_style.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from datasets import load_dataset
from tqdm import tqdm


TARGET_ROWS = 1000
OUTPUT_DIR = Path("data/output_3_non_opus_same_style")

STANDARD_COLUMNS = [
    "row_no",
    "record_id",
    "source_language",
    "source_language_code",
    "target_language",
    "target_language_code",
    "source_text",
    "target_text",
    "dataset",
    "config",
    "split",
    "source_url",
]


def clean_text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def finalize(records: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)
    df = df[STANDARD_COLUMNS]
    return df


def extract_unist_zh_to_en() -> pd.DataFrame:
    """
    UniST has these useful fields:
        id
        transcription
        translation
        src_lang
        tgt_lang
        split

    UniST may contain both directions. For a Chinese -> English evaluation file:
        - If src_lang is Chinese and tgt_lang is English:
              source_text = transcription
              target_text = translation
        - If src_lang is English and tgt_lang is Chinese:
              source_text = translation
              target_text = transcription
    """
    dataset_id = "cmots/UniST"
    source_url = "https://huggingface.co/datasets/cmots/UniST"
    chinese_codes = {"cmn", "zho", "zh", "chi"}
    english_codes = {"eng", "en"}

    records: List[Dict] = []
    seen = set()

    for split in ["validation", "test", "train"]:
        ds = load_dataset(dataset_id, "default", split=split, streaming=True)

        for row in tqdm(ds, desc=f"UniST zh->en {split}"):
            src_lang = clean_text(row.get("src_lang")).lower()
            tgt_lang = clean_text(row.get("tgt_lang")).lower()

            source_text: Optional[str] = None
            target_text: Optional[str] = None

            if src_lang in chinese_codes and tgt_lang in english_codes:
                source_text = clean_text(row.get("transcription"))
                target_text = clean_text(row.get("translation"))

            elif src_lang in english_codes and tgt_lang in chinese_codes:
                # Reverse English -> Chinese rows to create Chinese -> English rows.
                source_text = clean_text(row.get("translation"))
                target_text = clean_text(row.get("transcription"))

            else:
                continue

            if not source_text or not target_text:
                continue
            if source_text == target_text:
                continue

            key = (source_text, target_text)
            if key in seen:
                continue
            seen.add(key)

            records.append(
                {
                    "row_no": len(records) + 1,
                    "record_id": row.get("id"),
                    "source_language": "Chinese",
                    "source_language_code": "zh",
                    "target_language": "English",
                    "target_language_code": "en",
                    "source_text": source_text,
                    "target_text": target_text,
                    "dataset": dataset_id,
                    "config": "default",
                    "split": split,
                    "source_url": source_url,
                }
            )

            if len(records) >= TARGET_ROWS:
                return finalize(records)

    raise RuntimeError(f"Only found {len(records)} valid Chinese->English rows. Expected {TARGET_ROWS}.")


def extract_samanantar_hi_to_en() -> pd.DataFrame:
    """
    Samanantar Hindi config:
        src = English
        tgt = Hindi

    For Hindi -> English evaluation:
        source_text = tgt
        target_text = src
    """
    dataset_id = "ai4bharat/samanantar"
    source_url = "https://huggingface.co/datasets/ai4bharat/samanantar"

    records: List[Dict] = []
    seen = set()

    ds = load_dataset(dataset_id, "hi", split="train", streaming=True)

    for row in tqdm(ds, desc="Samanantar hi->en"):
        source_text = clean_text(row.get("tgt"))
        target_text = clean_text(row.get("src"))

        if not source_text or not target_text:
            continue
        if source_text == target_text:
            continue

        key = (source_text, target_text)
        if key in seen:
            continue
        seen.add(key)

        records.append(
            {
                "row_no": len(records) + 1,
                "record_id": row.get("idx"),
                "source_language": "Hindi",
                "source_language_code": "hi",
                "target_language": "English",
                "target_language_code": "en",
                "source_text": source_text,
                "target_text": target_text,
                "dataset": dataset_id,
                "config": "hi",
                "split": "train",
                "source_url": source_url,
            }
        )

        if len(records) >= TARGET_ROWS:
            return finalize(records)

    raise RuntimeError(f"Only found {len(records)} valid Hindi->English rows. Expected {TARGET_ROWS}.")


def extract_arz_to_en() -> pd.DataFrame:
    """
    Egyptian Arabic dataset expected fields:
        arz = Egyptian Arabic
        en = English
    """
    dataset_id = "IbrahimAmin/arz-en-parallel-corpus"
    source_url = "https://huggingface.co/datasets/IbrahimAmin/arz-en-parallel-corpus"

    records: List[Dict] = []
    seen = set()

    ds = load_dataset(dataset_id, split="train", streaming=True)

    for row in tqdm(ds, desc="Egyptian Arabic arz->en"):
        source_text = clean_text(row.get("arz"))
        target_text = clean_text(row.get("en"))

        if not source_text or not target_text:
            continue
        if source_text == target_text:
            continue

        key = (source_text, target_text)
        if key in seen:
            continue
        seen.add(key)

        records.append(
            {
                "row_no": len(records) + 1,
                "record_id": row.get("id") or row.get("idx"),
                "source_language": "Egyptian Arabic",
                "source_language_code": "arz",
                "target_language": "English",
                "target_language_code": "en",
                "source_text": source_text,
                "target_text": target_text,
                "dataset": dataset_id,
                "config": "default",
                "split": "train",
                "source_url": source_url,
            }
        )

        if len(records) >= TARGET_ROWS:
            return finalize(records)

    raise RuntimeError(f"Only found {len(records)} valid Egyptian Arabic->English rows. Expected {TARGET_ROWS}.")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("zh_to_en_unist_1000.csv", extract_unist_zh_to_en),
        ("hi_to_en_samanantar_1000.csv", extract_samanantar_hi_to_en),
        ("arz_to_en_parallel_corpus_1000.csv", extract_arz_to_en),
    ]

    manifest_rows = []
    combined_frames = []

    for filename, fn in jobs:
        df = fn()
        out_path = OUTPUT_DIR / filename
        df.to_csv(out_path, index=False, encoding="utf-8-sig")

        combined_frames.append(df)
        manifest_rows.append(
            {
                "file": filename,
                "dataset": df["dataset"].iloc[0],
                "source_language": df["source_language"].iloc[0],
                "source_language_code": df["source_language_code"].iloc[0],
                "target_language": "English",
                "target_language_code": "en",
                "records": len(df),
                "columns": "|".join(STANDARD_COLUMNS),
            }
        )

        print(f"Created {out_path} with {len(df)} rows")

    combined_df = pd.concat(combined_frames, ignore_index=True)
    combined_df.to_csv(
        OUTPUT_DIR / "combined_zh_hi_arz_to_en_3000.csv",
        index=False,
        encoding="utf-8-sig",
    )

    manifest_df = pd.DataFrame(manifest_rows)
    manifest_df.to_csv(OUTPUT_DIR / "manifest.csv", index=False, encoding="utf-8-sig")

    print(f"\nDone. Output folder: {OUTPUT_DIR.resolve()}")
    print("All files use the exact OPUS Books column style.")


if __name__ == "__main__":
    main()
