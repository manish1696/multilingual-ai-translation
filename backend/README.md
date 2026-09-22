# Translation Evaluation Backend

FastAPI service that wraps the Azure OpenAI literary translation engine
(`backend/ai/`) and exposes it as a REST API consumed by the frontend.

## Project layout

```
backend/
├── ai/                      # Translation + scoring engine
│   ├── batch_pipeline.py    # CSV-in/CSV-out CLI pipeline
│   ├── single_record.py     # Single-record translate + evaluate
│   ├── client.py            # Azure OpenAI client factory
│   ├── config.py            # Engine constants & env-driven settings
│   ├── metrics.py           # DataFrame-level scoring
│   ├── prompts.py           # Prompt-file resolution & message building
│   ├── scoring.py           # BLEU/chrF/token-F1/adequacy primitives
│   ├── text_utils.py        # Text normalisation helpers
│   └── translator.py        # Single-call translation with retry
├── app/
│   ├── api/                 # FastAPI routers (health, translation)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Pipeline integration (wraps ai/)
│   ├── config.py            # API settings loaded from env (.env)
│   └── main.py              # FastAPI application factory
├── prompts/                 # Language-specific prompt files (.md)
├── scripts/                 # Dataset extraction CLIs
├── requirements.txt
├── .env.example
└── README.md
```

The `app` layer is a thin REST wrapper around the `ai` package; no logic is
duplicated.

## Setup

```powershell
# from repo root
python -m venv .venv
.\.venv\Scripts\activate
pip install -r backend/requirements.txt

copy backend\.env.example backend\.env
# edit backend\.env and set AZURE_OPENAI_API_KEY
```

## Run

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: <http://localhost:8000/docs>

## Endpoints

| Method | Path                                | Description                             |
| ------ | ----------------------------------- | --------------------------------------- |
| GET    | `/`                                 | Service metadata                        |
| GET    | `/api/v1/health`                    | Liveness probe                          |
| GET    | `/api/v1/translation/languages`     | Built-in language presets               |
| POST   | `/api/v1/translation/evaluate`      | Translate one record and score it       |

### `POST /api/v1/translation/evaluate`

Request body:

```json
{
  "source_text": "Bonjour le monde.",
  "reference_text": "Hello, world.",
  "source_language": "French",
  "source_language_code": "fr",
  "target_language": "English"
}
```

Response: see `TranslationResponse` in `app/schemas/translation.py`.

## Environment variables

| Variable                     | Required | Default                                                                 |
| ---------------------------- | -------- | ----------------------------------------------------------------------- |
| `AZURE_OPENAI_API_KEY`       | yes      | —                                                                       |
| `AZURE_OPENAI_ENDPOINT`      | no       | `https://user-validation-ai-foundry.cognitiveservices.azure.com/`       |
| `AZURE_OPENAI_DEPLOYMENT`    | no       | `gpt-5.4-mini`                                                          |
| `AZURE_OPENAI_API_VERSION`   | no       | `2024-12-01-preview`                                                    |
| `API_PREFIX`                 | no       | `/api/v1`                                                               |
| `HOST` / `PORT`              | no       | `0.0.0.0` / `8000`                                                      |
| `CORS_ORIGINS`               | no       | `http://localhost:3001,http://localhost:5173,http://localhost:3000,http://127.0.0.1:5500` |
