# Testing

## Backend (Pytest)

Focused behavior tests, not third-party coverage:

- Tenant isolation and role permissions (owner/content manager, unrelated brand).
- Upload validation: extension/MIME mismatch, magic bytes, size limits, ZIP traversal, ZIP limits, SVG sanitization.
- Brand profile validation and one-active-profile rule; activation restricted to Owner.
- Real-model consent gate; virtual model readiness with fake provider.
- Product image requirement; quality checks advisory.
- Generation modes with fake AI; active-profile requirement; job states.
- Integrity gates: failed cannot be approved; needs-review comparison data present.
- Caption generation and preservation of manual edits.
- Approval audit fields; content manager publish denial.
- Publishing: approved-only, fake adapter success, retry-safe failure, no token exposure.

Run:

```bash
cd backend && uv run pytest
cd backend && uv run ruff check app tests
```

## Frontend

- `bun run build` and `bun run lint`.
- Playwright critical path against a clean test database with fake providers: login → brand → import fixture → analyze → activate profile → virtual model → product + image → studio generation → integrity → caption → submit → approve → fake publish → published state.
- Small real-model path verifies consent enforcement.

CI must not depend on paid AI, real Instagram, or real S3. Fake providers are the default.


## Delivery verification (MVP1)

- Backend: 162 tests passed; Ruff clean; mypy clean.
- Frontend: Biome clean; production build passes.
- Fresh database migrated through all ten revisions to `f1eb7aefef7a`.
- OpenAPI client regenerated with no pending diff.
- Playwright: complete fake-provider workflow and real-model consent path passed.

## Brand-book regression coverage

- A text-based PDF fixture is uploaded through the API and analyzed end-to-end.
- Assertions cover identity, positioning, audience, tone, photography, colors, typography, model style, social rules, dos/don'ts, and extra PDF sections (packaging, sustainability).

## OCR coverage

- Responses API request shape is unit-tested (model, PDF data, session header).
- A blank/scanned PDF is analyzed with a mocked OCR response; the profile is populated, OCR text is cached, and a second analysis does not call OCR again.
