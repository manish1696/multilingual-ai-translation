from __future__ import annotations

import sys
import time
from typing import Any, Dict, Optional

from openai import OpenAI

from . import config
from .prompts import make_messages
from .text_utils import clean_text


def translate_one(
    client: OpenAI,
    source_text: str,
    source_language: str,
    source_language_code: str,
    max_completion_tokens: int = config.DEFAULT_MAX_COMPLETION_TOKENS,
    retry_count: int = config.DEFAULT_RETRY_COUNT,
    retry_sleep: float = config.DEFAULT_RETRY_SLEEP,
    target_language: str = "English",
) -> Dict[str, Any]:
    last_error: Optional[Exception] = None

    for attempt in range(1, retry_count + 1):
        try:
            start = time.time()

            response = client.responses.create(
                model=config.AZURE_OPENAI_DEPLOYMENT,
                input=make_messages(
                    source_text=source_text,
                    source_language=source_language,
                    source_language_code=source_language_code,
                    target_language=target_language,
                ),
                max_output_tokens=max_completion_tokens,
                temperature=0,
                store=False,
            )

            latency = round(time.time() - start, 3)
            content = response.output_text or ""
            translation = clean_text(content)

            usage = getattr(response, "usage", None)
            input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
            output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0

            return {
                "status": "success",
                "translation": translation,
                "error": "",
                "latency": latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

        except Exception as exc:
            last_error = exc
            wait = retry_sleep * attempt
            print(
                f"\nRetry {attempt}/{retry_count} failed: {exc}. Sleeping {wait:.1f}s...",
                file=sys.stderr,
            )
            time.sleep(wait)

    return {
        "status": "failed",
        "translation": "",
        "error": str(last_error),
        "latency": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
