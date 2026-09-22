from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
PROMPTS_DIR = BACKEND_DIR / "prompts"

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env", override=False)


class Settings:
    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Translation Evaluation API")
        self.app_version: str = os.getenv("APP_VERSION", "1.0.0")
        self.api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.cors_origins: list[str] = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:3001,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500",
            ).split(",")
            if origin.strip()
        ]
        self.azure_openai_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_deployment: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.azure_openai_api_version: str | None = os.getenv("AZURE_OPENAI_API_VERSION")
        self.prompts_dir: Path = PROMPTS_DIR
        self.project_root: Path = PROJECT_ROOT


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
