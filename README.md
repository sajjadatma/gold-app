# Jewelry Brand Studio — MVP1

A multi-tenant SaaS for jewelry brands that already have an identity. Import the brand's own material, validate the extracted profile, photograph products with AI, verify jewelry fidelity, draft social copy, approve as Owner, and publish a single-image Instagram post.

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
