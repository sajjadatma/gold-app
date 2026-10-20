# API Contracts

Base: `/api/v1`. Auth: bearer JWT from template. Errors use FastAPI `detail`. All brand routes require membership; non-members receive `404`.

## Template (unchanged)

`POST /login/access-token`, `POST /login/test-token`, `POST /password-recovery/{email}`, `POST /reset-password/`, `GET/PATCH /users/me`, `PATCH /users/me/password`, `GET /users/` (superuser), health check.

## Brands and team

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET | `/brands` | any user | Brands the caller belongs to |
| POST | `/brands` | any user | Create brand; caller becomes owner |
| GET | `/brands/{brand_id}` | member | Brand detail |
| GET | `/brands/{brand_id}/members` | member | List members |
| POST | `/brands/{brand_id}/members` | owner | Add existing user by email + role |
| PATCH | `/brands/{brand_id}/members/{membership_id}` | owner | Change role |
| DELETE | `/brands/{brand_id}/members/{membership_id}` | owner | Remove member (not last owner) |

## Import and profile

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| POST | `/brands/{brand_id}/imports` | member | Multipart multi-file upload; returns import |
| GET | `/brands/{brand_id}/imports` | member | List imports |
| GET | `/brands/{brand_id}/imports/{import_id}` | member | Import detail with assets |
| POST | `/brands/{brand_id}/imports/{import_id}/analyze` | member | Enqueue/execute brand intelligence |
| GET | `/brands/{brand_id}/assets` | member | Asset library, optional type filter |
| GET | `/brands/{brand_id}/assets/{asset_id}/download` | member | Authenticated original download |
| DELETE | `/brands/{brand_id}/assets/{asset_id}` | owner | Remove asset from active use |
| GET | `/brands/{brand_id}/profile` | member | Latest profile version |
| PATCH | `/brands/{brand_id}/profile/{profile_id}` | owner | Correct `profile_json` |
| POST | `/brands/{brand_id}/profile/{profile_id}/activate` | owner | Activate; archives previous |

## Models

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET | `/brands/{brand_id}/models` | member | List models |
| POST | `/brands/{brand_id}/models` | member | Create virtual or real model |
| GET/PATCH | `/brands/{brand_id}/models/{model_id}` | member | Detail/update |
| POST | `/brands/{brand_id}/models/{model_id}/references` | member | Upload reference image |
| GET | `/brands/{brand_id}/models/{model_id}/references/{ref_id}/download` | member | Private reference |
| POST | `/brands/{brand_id}/models/{model_id}/generate-previews` | member | Virtual previews job |
| POST | `/brands/{brand_id}/models/{model_id}/canonical` | member | Mark canonical reference |
| POST | `/brands/{brand_id}/models/{model_id}/consent` | member | Record consent (real model) |
| POST | `/brands/{brand_id}/models/{model_id}/default` | member | Set default ready model |

## Products

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET/POST | `/brands/{brand_id}/products` | member | List/create |
| GET/PATCH | `/brands/{brand_id}/products/{product_id}` | member | Detail/update |
| POST | `/brands/{brand_id}/products/{product_id}/archive` | member | Archive |
| POST | `/brands/{brand_id}/products/{product_id}/images` | member | Upload image + quality check |
| GET | `/brands/{brand_id}/products/{product_id}/images/{image_id}/download` | member | Private image |
| POST | `/brands/{brand_id}/products/{product_id}/images/{image_id}/primary` | member | Set primary |

## Generation and integrity

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| POST | `/brands/{brand_id}/generations` | member | Create request; validates active profile, product image, model |
| GET | `/brands/{brand_id}/generations` | member | List requests |
| GET | `/brands/{brand_id}/generations/{gen_id}` | member | Detail with assets |
| POST | `/brands/{brand_id}/generations/{gen_id}/retry` | member | Retry failed generation |
| GET | `/brands/{brand_id}/generated-assets/{asset_id}/download` | member | Private generated image |

## Content and approval

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| POST | `/brands/{brand_id}/drafts` | member | Draft from generated asset |
| GET | `/brands/{brand_id}/drafts` | member | List |
| GET/PATCH | `/brands/{brand_id}/drafts/{draft_id}` | member | Detail/manual edit |
| POST | `/brands/{brand_id}/drafts/{draft_id}/generate-caption` | member | Primary + alternatives + CTA + hashtags |
| POST | `/brands/{brand_id}/drafts/{draft_id}/submit` | member | `draft → needs_approval` |
| POST | `/brands/{brand_id}/drafts/{draft_id}/approve` | owner | Requires integrity not failed/pending; audits approver |
| POST | `/brands/{brand_id}/drafts/{draft_id}/reject` | owner | `→ rejected` |

## Social and publishing

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET | `/brands/{brand_id}/social` | member | Connection status (never token) |
| PUT | `/brands/{brand_id}/social` | owner | Configure connection; fake by default |
| DELETE | `/brands/{brand_id}/social` | owner | Disconnect |
| POST | `/brands/{brand_id}/drafts/{draft_id}/publish` | owner | Queue publish; draft must be approved |
| GET | `/brands/{brand_id}/drafts/{draft_id}/publish-jobs` | member | Publish history/state |
| POST | `/brands/{brand_id}/publish-jobs/{job_id}/retry` | owner | Safe retry after failure |
