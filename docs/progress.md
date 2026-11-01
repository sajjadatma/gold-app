# Progress

MVP1 execution status. Updated at the end of every completed stage.

| Stage | Scope | Status | Commit |
| --- | --- | --- | --- |
| T00 | Bootstrap & baseline | complete | `3ad0d4f` |
| T01 | MVP contracts | complete | `4f3277f` |
| T02 | Brand + multi-tenant access | complete | `089d99f` |
| T03 | Private storage | complete | `a712bd9` |
| T04 | Brand import | complete | `df11d1f` |
| T05 | Brand intelligence | complete | `45fc6e6` |
| T06 | Brand validation & activation | complete | `b4db9de` |
| T07 | Real & virtual brand models | complete | `c76ad5f` |
| T08 | Product catalog | complete | `9eafa7f` |
| T09 | AI generation foundation | complete | same-as-T10 |
| T10 | AI photography studio | complete | `a0cdd53` |
| T11 | Product integrity evaluation | complete | `c083049` |
| T12 | Caption & content draft | complete | `c083049` |
| T13 | Approval workflow | complete | `33c6ed9` |
| T14 | Instagram publishing | complete | `60e777d` |
| T15 | Complete E2E workflow | complete | `ce35f4d` |
| T16 | Hardening | complete | `4973c7e` |
| T17 | Delivery | complete | pending push |

## Baseline notes (T00)

- Repository started from `fastapi/full-stack-fastapi-template`; `upstream` points at the template, `origin` at the delivery repository.
- Host port `5432` is occupied by a pre-existing local PostgreSQL installation. The project database is mapped to host port `5433` (`compose.override.yml`) so the unrelated local database is never touched.
- `DATABASE_URL` in the local `.env` targets `localhost:5433`.
- The template tracks `.env`; it has been untracked and ignored. `.env.example` contains placeholders only.
- `backend/alembic.ini` now sets `prepend_sys_path = .`, and `backend/scripts/prestart.sh` runs `python -m app.initial_data` so the backend package is importable when commands run outside Docker.
- Baseline backend suite: 58 passed.
- Baseline frontend production build: passed.

## Post-delivery changes

- Dashboard logout button.
- Brand-book PDFs are read in full from embedded text; real AI analysis is chunked across the document and unknown sections are stored in `additional_sections`.

- Added English/Farsi localization with RTL, Persian dates, persisted language selection, and a sidebar/auth language switcher.

- Full-app acceptance pass completed with downloaded real assets, rich brand-book PDFs, scanned OCR, admin/items CRUD, and both languages; fixed discovered parser, settings-form, and English enum-label issues.

## Isolated full-app QA — 2026-11-01

- Complete: 166 backend tests, 65 browser tests against Redis and one real arq worker, and 27 additional live API/worker checks passed.
- Fresh PostgreSQL databases and private storage isolated test cleanup from the existing development data. External AI/OCR and Instagram calls were disabled or faked.
- Fixed PDF typographic-apostrophe headings losing `donts`, asynchronous publishing UI failing to follow worker completion, profile field labels, and missing Farsi labels.
- Made the Farsi browser test self-contained, added profile-edit persistence coverage, and excluded generated test artifacts from Biome.
- Ruff, mypy, Biome, TypeScript/production build and diff review passed. OpenAPI unchanged. Ten main Farsi pages checked at a 390×844 mobile viewport without document overflow.
- Detailed evidence, original failures, fixes, screenshots and scope limits: [QA report](qa/2026-11-01.md).
