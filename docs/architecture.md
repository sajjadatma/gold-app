# Architecture

## Shape

Modular monolith: FastAPI + SQLModel + PostgreSQL, one arq worker backed by Redis, private object storage, React SPA generated from OpenAPI.

```text
frontend (React 19 / TanStack Router / Query / Tailwind / shadcn)
        │ generated OpenAPI client
backend/app
  api/            template auth, users, deps, aggregate router
  core/           config, db, security
  models.py       template User (extended with display language only)
  modules/
    brands/       Brand, Membership, tenant dependencies, team API
    brand_import/ BrandImport, BrandAsset, upload validation, ZIP/SVG handling
    brand_models/ BrandModel, references, consent, previews
    products/     Product, ProductImage, quality checks
    generations/  GenerationRequest, GeneratedAsset, studio jobs, integrity evaluation
    content/      ContentDraft, caption generation, approval
    publishing/   SocialConnection, PublishJob, Instagram adapters
  providers/      storage, ai (text/image/vision), instagram — fake + real
  workers/        arq settings and single worker entrypoint
```

Modules expose routers and services; no repository/controller layers. Cross-module reads use SQLModel sessions directly, constrained by brand id.

## Tenancy

- Every tenant-owned row carries `brand_id` (directly or by parent).
- `GET /brands` lists only the caller's memberships; superusers do not bypass tenant scope.
- Brand-scoped endpoints live under `/api/v1/brands/{brand_id}/...`; a dependency resolves the membership and role, returning 404 for unknown/unrelated brands.
- Uploaded objects use server-generated keys prefixed by brand id; downloads always pass tenant authorization.

## Background jobs

`arq` is the only worker. Tasks: import analysis, model previews, image generation, integrity evaluation, publishing. They update persisted status. When `TASKS_EAGER=true` (tests/local default) tasks execute inline so the contract is verifiable without Redis; production runs the same functions through arq.

## Providers

Thin adapters selected by settings, with deterministic fakes as defaults:

- Storage: local private directory (default) or S3-compatible (`boto3`).
- AI: fake (Pillow-generated images, deterministic text/vision) or OpenAI-compatible HTTP endpoints.
- Instagram: fake (default) or Graph API.

No provider registry or marketplace. Missing credentials never block development.

## Key decisions

- Single image feed posts only; publishing requires approved draft and non-failed integrity.
- Virtual model previews are reference-based; no fine-tuning.
- BrandProfile JSON is validated by Pydantic before persistence.
- Uploaded originals are immutable; deleting an asset removes it from active use.
- Generated images are composite placeholders in fake mode and clearly labeled as such.
- Polling drives async UI; no WebSockets.
