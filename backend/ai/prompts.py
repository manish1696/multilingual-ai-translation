from __future__ import annotations

from pathlib import Path

from . import config
from .text_utils import clean_text


def resolve_translation_prompt_path(
    source_language_code: str,
    source_language: str,
) -> Path:
    """
    Prompt loading priority:
        1. <PROMPT_DIR>/<source_language_code>_translation_prompt.md
           Example: prompts/hi_translation_prompt.md
        2. <PROMPT_DIR>/<source_language_name>_translation_prompt.md
           Example: prompts/egyptian_arabic_translation_prompt.md
        3. <PROMPT_DIR>/default_translation_prompt.md
    """
    prompt_dir = Path(config.PROMPT_DIR)

    language_code = clean_text(source_language_code).lower()
    language_name = clean_text(source_language).lower().replace(" ", "_")

    prompt_candidates: list[Path] = []

    if config.USE_LANGUAGE_SPECIFIC_PROMPT:
        if language_code:
            prompt_candidates.append(prompt_dir / f"{language_code}_translation_prompt.md")

        if language_name:
            prompt_candidates.append(prompt_dir / f"{language_name}_translation_prompt.md")

    prompt_candidates.append(prompt_dir / config.DEFAULT_PROMPT_FILE)

    for prompt_path in prompt_candidates:
        if prompt_path.exists():
            return prompt_path

    raise FileNotFoundError(
        "No translation prompt file found. Expected one of:\n"
        + "\n".join(str(path) for path in prompt_candidates)
    )


def load_translation_prompt(
    source_language_code: str,
    source_language: str,
) -> str:
    prompt_path = resolve_translation_prompt_path(
        source_language_code=source_language_code,
        source_language=source_language,
    )
    return prompt_path.read_text(encoding="utf-8").strip()


def make_messages(
    source_text: str,
    source_language: str,
    source_language_code: str,
    target_language: str = "English",
) -> list[dict[str, str]]:
    system_prompt = load_translation_prompt(
        source_language_code=source_language_code,
        source_language=source_language,
    )

    user_prompt = (
        f"Source language: {source_language}\n"
        f"Source language code: {source_language_code}\n"
        f"Target language: {target_language}\n\n"
        f"Text:\n{source_text}"
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
