# Multilingual AI Translation & Evaluation Platform

A quality-aware Azure OpenAI translation platform supporting **110 directed
language pairs** across English and ten benchmarked languages. English-connected
translations use one call; other pairs are routed through an inspectable English
pivot with per-stage latency and token observability.

## V2 capabilities

- Any-to-any translation across 11 languages
- Deterministic direct/English-pivot route planning
- Separate **Translate** and **Evaluate** experiences
- Multilingual semantic similarity using Sentence Transformers
- BLEU, chrF, token-F1, length ratio, entity preservation, and Quality Score V2
- Per-stage prompt, output, latency, token usage, status, and error metadata
- English-pivot inspection and retry-safe partial-stage results
- CSV/XLSX batch evaluation and resumable offline pipelines
- FastAPI OpenAPI documentation and React/TypeScript production UI
- Unit tests, linting, type checking, Docker, and CI

## Supported languages

English, French, German, Spanish (Europe), Portuguese (Europe), Hungarian,
Hindi, Chinese, Egyptian Arabic, Japanese, and Korean.

With 11 languages the platform supports `11 × 10 = 110` directed pairs:

- `ja → en`: direct, one call
- `en → ko`: direct, one call
- `ja → ko`: `ja → en → ko`, two calls

## Evaluation design

Evaluation is reference-based and intentionally separate from normal translation.
Quality Score V2 combines:

```text
40% semantic similarity
25% normalized chrF
15% token-F1
10% length ratio
10% numeric/currency entity preservation
```

The score is a configurable heuristic quality indicator—not calibrated
probabilistic confidence or human accuracy. Calibrate its weights and threshold
against human-reviewed data before making an accuracy claim.

Semantic scoring lazily loads
`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` on the first
evaluated request. Set `SEMANTIC_SCORING_ENABLED=false` to run without it.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
# Add AZURE_OPENAI_API_KEY and your Azure endpoint/deployment.

cd backend
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

- UI: http://localhost:3001
- API documentation: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## API

### Translate without a reference

`POST /api/v1/translation/translate`

```json
{
  "source_text": "こんにちは",
  "source_language": "Japanese",
  "source_language_code": "ja",
  "target_language": "Korean",
  "target_language_code": "ko"
}
```

### Translate and evaluate

`POST /api/v1/translation/evaluate` uses the same fields plus:

```json
{ "reference_text": "안녕하세요" }
```

The response includes the route, optional English pivot, stage records, final
translation, model metadata, token totals, and evaluation metrics.

## Validation

```bash
PYTHONPATH=backend SEMANTIC_SCORING_ENABLED=false pytest -q backend/tests
cd frontend
npm run build
npm run lint
```

Semantic-scoring correctness should additionally be smoke-tested once the model
is downloaded in the target deployment environment.

## Existing benchmark

The supplied experiment set covers 10,000 records over ten non-English → English
directions. The earlier 88.51% figure is an automated threshold pass rate, not
human-validated accuracy. V2 preserves the legacy metrics for comparison while
adding semantic similarity and a clearly labelled Quality Score.

## Security and publishing

- Never commit `.env`, credentials, input datasets, or generated outputs.
- Restrict CORS and add authentication/rate limiting before public deployment.
- Verify that all prompts, branding, and datasets may legally be published.
- The example Azure endpoint is deliberately non-organization-specific.
