from __future__ import annotations

from openai import OpenAI

from . import config


def build_client() -> OpenAI:
    if not config.AZURE_OPENAI_API_KEY:
        raise RuntimeError(
            "AZURE_OPENAI_API_KEY is missing. Add it in .env or export it:\n"
            "export AZURE_OPENAI_API_KEY='your-key'"
        )

    endpoint = config.normalize_azure_endpoint(config.AZURE_OPENAI_ENDPOINT)
    return OpenAI(
        api_key=config.AZURE_OPENAI_API_KEY,
        base_url=f"{endpoint}/openai/v1/",
    )
