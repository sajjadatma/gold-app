# Delivery and Configuration

## Repositories

| Remote | URL | Purpose |
| --- | --- | --- |
| `origin` | https://github.com/sajjadatma/gold-app.git | Delivery repository |
| `upstream` | https://github.com/fastapi/full-stack-fastapi-template.git | Base template |

Branch: `main`.

## Local services

| Service | Address |
| --- | --- |
| Frontend (dev) | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| PostgreSQL | `localhost:5433` (isolated from a local 5432 server) |
| Mailpit | http://localhost:8025 |
| Redis | `localhost:6379` (`docker compose up -d redis`) |

Host port 5432 is intentionally avoided because a pre-existing local PostgreSQL may own it.

## Environment

Copy `.env.example` to `.env`. It contains:

- `SECRET_KEY`, `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`
- `DATABASE_URL` (`postgresql://postgres:...@localhost:5433/app`)
- storage selection and S3 settings
- AI provider settings
- Instagram provider settings
- job execution (`TASKS_EAGER`, `REDIS_URL`)

`.env` is ignored by Git. Never commit real credentials.

## Storage

`STORAGE_BACKEND=local` (default) writes private objects under `backend/storage`, keyed as
`brands/{brand_id}/{namespace}/{uuid}{ext}`. Every download is authenticated and tenant-checked.

For production, set:

```text
STORAGE_BACKEND=s3
S3_BUCKET=...
S3_ENDPOINT_URL=https://...   # optional for AWS
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...
S3_REGION=...
```

The S3 adapter uses presigned GET URLs only for Instagram Graph publishing.

## AI

Defaults use deterministic fakes, so the full product works without paid credentials.

```text
AI_PROVIDER=fake            # or openai
AI_API_BASE=https://api.openai.com/v1
AI_API_KEY=...
AI_TEXT_MODEL=gpt-4.1-mini
AI_VISION_MODEL=gpt-4.1-mini
AI_IMAGE_MODEL=gpt-image-1
```

The OpenAI-compatible adapter calls chat completions for brand analysis/captions/integrity and images for generation. All structured output is validated by Pydantic before persistence. Missing credentials fall back to fake providers.

## OCR (optional)

Scanned/image-only PDFs can be transcribed by GPT-6 Luna through the OpenAI Responses API. The model accepts PDF input directly.

```text
OCR_ENABLED=false
OCR_API_BASE=https://opencode.ai/inference/go/openai/v1
OCR_API_KEY=...
OCR_MODEL=gpt-6-luna
OCR_MIN_TEXT_CHARS=200
OCR_MAX_PDF_BYTES=20971520
```

- Go endpoint: `https://opencode.ai/inference/go/openai/v1` (OpenCode Go subscription key).
- Console endpoint: `https://opencode.ai/inference/openai/v1` (pay-as-you-go; recommended for OCR/document workloads).
- Only PDFs whose extracted text is shorter than the threshold are sent. OCR text is cached in asset metadata.
- Enabling OCR sends brand documents to an external provider and incurs token costs.

## Instagram

```text
INSTAGRAM_PROVIDER=fake     # or graph
INSTAGRAM_GRAPH_BASE=https://graph.facebook.com/v21.0
```

Connect a professional account under **Social** with its Instagram user id and access token. Real publishing requires a public/presigned image URL (S3 storage). Fake publishing is used in development and tests.

## Background jobs

One worker only:

```bash
cd backend && uv run arq app.workers.tasks.WorkerSettings
```

`TASKS_EAGER=true` executes generation/publish inline (tests and local demo). `TASKS_EAGER=false` enqueues to Redis for the worker. Docker Compose starts both Redis and the worker automatically.

## Database

```bash
cd backend
uv run alembic upgrade head          # migrations
uv run python -m app.initial_data    # initial superuser
```

A fresh database migrates to head (verified in delivery).

## Verification

```bash
cd backend
uv run pytest
uv run ruff check app tests
uv run mypy app

cd ../frontend
bun run lint
bun run build
bunx playwright test tests/mvp-workflow.spec.ts --workers=1
```
