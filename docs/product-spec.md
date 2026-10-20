# Product Spec — Jewelry Brand Studio MVP1

Authoritative source: [`JEWELRY_BRAND_STUDIO_MVP1.md`](../JEWELRY_BRAND_STUDIO_MVP1.md).

## Outcome

A multi-tenant SaaS where a jewelry brand imports its existing identity, validates it, creates a real or virtual brand model, photographs products with AI, verifies jewelry fidelity, drafts social copy, approves as Owner, and publishes a single Instagram feed post.

## Core flow

```text
import assets → analyze → validate/activate BrandProfile
→ choose/create model → add product + source image
→ generate (studio | on_model | campaign) → integrity review
→ caption/CTA/hashtags → submit → Owner approve
→ publish to Instagram (fake provider in development)
```

## Roles

| Capability | Owner | Content Manager | Superuser |
| --- | --- | --- | --- |
| Manage brand, team, social connection | yes | no | support only |
| Import assets, manage models/products | yes | yes | no |
| Generate imagery/content | yes | yes | no |
| Activate BrandProfile | yes | no | no |
| Approve/reject/publish content | yes | no | no |
| Cross-tenant access | no | no | no |

## MVP acceptance criteria

1. Authentication reuses the template (login, recovery, settings).
2. Users can create/select a brand; membership is tenant-scoped.
3. Brand bundles (PDF, images, SVG, fonts, AI/EPS/PSD, ZIP) import securely and are listed in a library.
4. Import analysis produces a Pydantic-validated BrandProfile candidate with provenance and uncertainty notes.
5. Owner can correct and activate exactly one profile per brand; generation requires an active profile.
6. Virtual models generate deterministic previews with a fake provider; real models require a consent record before ready/default.
7. Products require name, category, and at least one source image before generation; images get advisory quality feedback.
8. Studio, On-Model, and Campaign generation run with the active profile; results are stored as GeneratedAssets.
9. Integrity evaluation returns `passed | needs_review | failed`; failed assets cannot be approved.
10. Caption generation returns one primary + two alternatives, CTA, and hashtags; user edits are never overwritten silently.
11. Owner approval is mandatory and audited (who/when); Content Managers cannot publish.
12. Instagram publishing supports a single image post with fake and real adapters, retry-safe failure states, and no token exposure.

## Out of scope

See [`JEWELRY_BRAND_STUDIO_MVP1.md` §32](../JEWELRY_BRAND_STUDIO_MVP1.md#32-mvp1-out-of-scope) and [`post-mvp-backlog.md`](post-mvp-backlog.md). No billing, video, carousels, analytics, scheduler, or brand-book design tooling.
