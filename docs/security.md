# Security

## Tenant isolation

- Membership lookup on every brand-scoped request; unrelated ids return 404.
- Child resources are resolved through their brand (never by bare id alone).
- Superusers do not receive cross-tenant data access.
- Storage keys embed the brand id; every download re-checks membership.

## Uploads

- Server-generated storage keys; original filenames sanitized and kept only as metadata.
- Private storage by default; authenticated, non-public download endpoints.
- Extension and MIME allowlists plus magic-signature checks for processed formats.
- Configurable limits: PDF 50 MB, image 25 MB, font 20 MB, design source 150 MB, ZIP 250 MB, 500 extracted files, 500 MB expanded.
- ZIP: reject absolute paths, `..` traversal, symlinks, nested archives; enforce count/size limits while streaming.
- SVG: parse with `defusedxml`, reject DTD/entities, strip scripts, event handlers, `foreignObject`, external references; serve sanitized/original via download with `attachment` and no inline HTML rendering of untrusted SVG.
- Images: Pillow decode with pixel-count guard; reject decompression bombs.
- PDF: page-count and text-length limits; no heavy OCR infra.

## Secrets

- `.env` untracked; `.env.example` contains placeholders only.
- Provider/Instagram tokens never appear in API responses or logs.
- Missing credentials fall back to fake providers; no fabricated secrets.

## Authorization gates

- Only Owners activate profiles, manage members/social, approve/reject, and publish.
- Content Managers prepare drafts and cannot bypass approval.
- Failed-integrity assets cannot be approved; pending/queued assets cannot be approved.
- Publishing requires an approved draft, connected account, and no successful prior job for the draft.
- Approval and publish actions record actor and timestamp.

## Errors and logging

- User-facing errors are actionable without stack traces, tokens, or filesystem paths.
- Sentry support from the template remains optional.
