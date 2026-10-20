# Jewelry Brand Studio — MVP1

A multi-tenant SaaS for jewelry brands that already have an identity. Import the brand's own material — including full brand-book PDFs — validate the extracted profile, photograph products with AI, verify jewelry fidelity, draft social copy, approve as Owner, and publish a single-image Instagram post.

PDF brand books are read in full from their embedded text (up to configurable limits). Real AI analysis is chunked across the whole document, and any extra sections such as packaging, values, materials, or sustainability are preserved in the profile.

For scanned or image-only PDFs, optional OCR uses GPT-6 Luna's native PDF input. Set `OCR_ENABLED=true` and `OCR_API_KEY`; the extracted text is cached on the asset so it is never billed twice.

Built on the [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template).

- **Backend:** FastAPI, SQLModel, PostgreSQL, Alembic, Pydantic, PyJWT, pytest
- **Worker:** Redis + one `arq` worker (jobs can run inline with `TASKS_EAGER=true`)
- **Frontend:** React 19, TypeScript, Vite, TanStack Router/Query, Tailwind, shadcn/ui
- **Tests:** pytest and Playwright; deterministic fake providers are the default
- **Storage:** private local directory in development, S3-compatible in production

## Quick start (local)

Requirements: Python 3.14 (managed by `uv`), Bun, Docker.

```bash
cp .env.example .env
# Replace changethis secrets in .env.

docker compose up -d --wait db mailpit
uv sync
cd backend && uv run bash scripts/prestart.sh && cd ..

# API (terminal 1)
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Frontend (terminal 2)
cd frontend && bun install && bun run dev
```

Open http://localhost:5173 and log in with `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` from `.env`.

The project PostgreSQL is exposed on host port **5433** so it never collides with a local PostgreSQL on 5432. Mailpit is at http://localhost:8025.

### Docker Compose

```bash
docker compose up --build -d
```

This starts PostgreSQL, Redis, the API, the arq worker, Mailpit, and Traefik. The worker consumes import/generation/publish jobs; set `TASKS_EAGER=false` only when the worker is running (the Compose services already do).

## Tests

```bash
cd backend && uv run pytest && uv run ruff check app tests && uv run mypy app
cd frontend && bun run lint && bun run build
```

Critical end-to-end flow (requires the API and Vite dev server running, plus initial data):

```bash
cd backend && uv run python -m app.initial_data
cd frontend && bunx playwright test tests/mvp-workflow.spec.ts --workers=1
```

CI and local tests never call paid AI, real Instagram, or real S3.

## OCR (optional)

```text
OCR_ENABLED=true
OCR_API_BASE=https://opencode.ai/inference/go/openai/v1   # Go
OCR_API_KEY=...
OCR_MODEL=gpt-6-luna
```

`gpt-6-luna` accepts `text`, `image`, and `pdf` input, so no rasterization is needed. Only PDFs with little or no embedded text are sent for OCR, and the result is stored per asset.

OpenCode Go is intended for coding-agent traffic and is monitored for abuse. For document/OCR workloads, the OpenCode **Console pay-as-you-go** endpoint (`https://opencode.ai/inference/openai/v1`) uses the same model and is the safer choice. OpenAI's GPT-6 Luna requests are retained for up to 30 days for abuse monitoring.

## Request states

- A slim global progress bar appears for initial data loads and active mutations.
- Mutating actions disable their controls while pending and show success or failure toasts.
- List and detail screens have loading, empty, and error-with-retry states.
- Long-running jobs (generation, publishing) expose persisted `queued`, `processing`, `completed`, and `failed` states and poll while active.

## Languages

The UI ships with **English** and **Farsi**. Use the language control in the sidebar (or the auth pages) to switch; the choice is saved in localStorage.

- Farsi switches the document to RTL (`dir="rtl"`) and uses Persian date formatting.
- Navigation, forms, buttons, validation messages, statuses, empty states, dialogs, and accessibility labels are translated.
- Brand names, user-entered content, AI-generated copy, and backend error details remain in their source language by design.

Translation resources live in `frontend/src/i18n/fa.ts`; the i18n provider and hooks are in `frontend/src/i18n/index.tsx`.

Farsi uses **Vazirmatn**, bundled locally as a variable font in `frontend/public/fonts/` (SIL OFL 1.1, license included). This avoids Google Fonts/CDN dependency. To use Yekanbakh instead, add your licensed font files and replace the `@font-face` rule in `frontend/src/index.css`.

## Providers

| Area | Default | Production configuration |
| --- | --- | --- |
| Storage | Private local directory (`backend/storage`) | `STORAGE_BACKEND=s3`, `S3_BUCKET`, optional endpoint/keys |
| AI | Deterministic fake text/image/vision | `AI_PROVIDER=openai`, `AI_API_BASE`, `AI_API_KEY`, model names |
| Instagram | Fake publisher | `INSTAGRAM_PROVIDER=graph` + connected professional account |

See `.env.example` and [`docs/delivery.md`](docs/delivery.md).

### Instagram real publishing

Real Graph publishing needs an image URL accessible to Meta. Configure S3-compatible storage: the adapter generates a short-lived presigned URL. Local storage returns no public URL and rejects real publishing with an actionable error.

Tokens are stored server-side and never returned by the API. Restrict database access and use encryption at rest in production.

## Documentation

- [Product spec](docs/product-spec.md)
- [Architecture](docs/architecture.md)
- [Data model](docs/data-model.md)
- [API contracts](docs/api-contracts.md)
- [Security](docs/security.md)
- [Testing](docs/testing.md)
- [Delivery and configuration](docs/delivery.md)
- [Progress](docs/progress.md)
- [Final report](docs/final-report.md)

## Scope

MVP1 only. No Reels, stories, carousels, scheduling, analytics, billing, multi-social posting, video, or brand-book design tooling. See [post-MVP backlog](docs/post-mvp-backlog.md).
