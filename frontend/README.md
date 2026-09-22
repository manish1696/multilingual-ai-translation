# Translation Evaluation Frontend

React + TypeScript + Vite + Tailwind CSS frontend for the translation
evaluation API, using a clean neutral product identity:

- Primary brand color: `#5b0428` (header brand text, focus rings, headings)
- Hover state: `#7b0538`
- Accent: `#DB1A1A`
- Product mark: Lucide `Languages` icon
- Font: Inter (Google Fonts)

## Project layout

```
frontend/
├── public/
│   └── robots.txt
├── src/
│   ├── components/
│   │   └── TranslationResult.tsx
│   ├── layout/
│   │   ├── Header.tsx          # Product icon + title + nav
│   │   └── index.tsx           # Page chrome (matches sample-frontend)
│   ├── pages/
│   │   ├── Home.tsx            # Translate & evaluate page
│   │   └── About.tsx
│   ├── services/
│   │   └── api.ts              # axios client → backend FastAPI
│   ├── types/
│   │   └── index.ts            # API DTOs (TS interfaces)
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css
│   └── vite-env.d.ts
├── .env.example
├── .eslintrc.cjs
├── index.html
├── package.json
├── postcss.config.js
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

## Setup

```bash
cd frontend
npm install
copy .env.example .env       # adjust VITE_API_BASE_URL if needed
npm run dev                  # http://localhost:3001
```

## Build / lint

```bash
npm run build
npm run preview
npm run lint
```

## Environment variables

| Variable             | Default                          | Description                  |
| -------------------- | -------------------------------- | ---------------------------- |
| `VITE_API_BASE_URL`  | `http://localhost:8000/api/v1`   | FastAPI backend base URL     |

Make sure the backend (`uvicorn backend.app.main:app --reload`) has
`http://localhost:3001` in its `CORS_ORIGINS` env var.

## Features

- Header with a neutral product icon, title, and primary-color nav links.
- Language preset dropdown (loaded from `GET /translation/languages`,
  falls back to a built-in list if the API is unreachable).
- Source text, reference text, source language, language code, target
  language inputs.
- Calls `POST /translation/evaluate` and renders:
  - LLM translation (read-only textarea)
  - Three metric cards (Accuracy %, chrF, Token F1)
  - Collapsible evaluation details (BLEU, length ratio, etc.)
  - Collapsible run metadata (model, prompt path, latency, token usage)
- Toast notifications for success / error states.
