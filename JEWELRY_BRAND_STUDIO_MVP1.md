# Jewelry Brand Studio — MVP1 Autonomous Build Specification

**Document status:** Final MVP1 execution contract  
**Target:** OpenCode  
**Execution mode:** Autonomous, single-agent, strict-scope  
**Base template:** https://github.com/fastapi/full-stack-fastapi-template  
**Delivery repository:** https://github.com/sajjadatma/gold-app.git  
**Target branch:** `main`  
**Architecture:** Modular monolith + one background worker  
**Primary rule:** Build exactly the MVP below. Do not overengineer.

---

# 0. OpenCode Mission

You are the autonomous principal engineer responsible for delivering **Jewelry Brand Studio MVP1** from an empty delivery repository to a tested, runnable, documented application.

You must:

1. Bootstrap the project from the official Full Stack FastAPI Template.
2. Implement the MVP exactly as specified here.
3. Make normal engineering decisions yourself.
4. Do not ask routine questions.
5. Use your strongest reasonable recommendation when requirements are ambiguous.
6. Record only meaningful architecture decisions.
7. Test every completed stage.
8. Commit and push to the target GitHub repository after every completed stage.
9. Ask for human approval only before dangerous, destructive, costly, secret-bearing, production, or irreversible external actions.
10. Continue automatically until the MVP Definition of Done is satisfied.

The user should not need to approve ordinary implementation details.

---

# 1. Product Definition

Jewelry Brand Studio is a SaaS application for jewelry businesses that already have an established brand identity.

The MVP must support this complete flow:

```text
Import existing brand assets
        ↓
AI analyzes brand identity
        ↓
User validates extracted brand profile
        ↓
Create/select a real or virtual human brand model
        ↓
Add jewelry product and source photos
        ↓
Generate professional branded images
        ↓
Check product integrity
        ↓
Generate caption / CTA / hashtags
        ↓
Owner reviews and approves
        ↓
Publish approved image post to Instagram
```

The application does **not** create a brand book from scratch.

---

# 2. Non-Negotiable Product Principles

## 2.1 Existing brand identity is the source of truth

The user already has years of existing brand material.

The application must import and understand it instead of redesigning it.

## 2.2 Jewelry fidelity matters more than creativity

AI-generated imagery must try to preserve:

- jewelry shape
- major geometry
- stone count where visible
- stone placement
- metal color
- structural details
- pendant / ring / chain form
- major decorative elements

The system must warn when output may differ materially from the original product.

## 2.3 Human approval before publishing

No generated social-media content may be published without explicit in-application Owner approval.

## 2.4 Brand consistency

Image generation and caption generation must use the active BrandProfile.

## 2.5 Multi-tenant isolation

One jewelry brand must never access another brand's private data or assets.

---

# 3. HARD RULE — NO OVERENGINEERING

This project must be implemented with the **simplest architecture that correctly satisfies MVP1**.

Use YAGNI aggressively.

Before adding any abstraction, service, table, package, pattern, infrastructure component, or framework, ask internally:

> Is this required by a current MVP1 acceptance criterion?

If the answer is no, do not build it.

## 3.1 Explicitly prohibited unless required by an existing MVP acceptance criterion

Do not introduce:

- microservices
- Kubernetes
- Terraform
- service mesh
- event sourcing
- CQRS
- GraphQL
- custom dependency-injection framework
- generic repository pattern everywhere
- domain-driven-design framework
- internal event bus
- Kafka / RabbitMQ
- multiple worker systems
- speculative caching layers
- Redis caching unrelated to job execution
- custom design system
- custom component library replacing shadcn/ui
- feature-flag platform
- observability platform beyond existing/simple logging and Sentry support
- plugin architecture
- generic workflow engine
- generic AI-provider marketplace
- complex state machine library
- WebSockets unless a concrete implemented screen cannot work adequately with polling
- extra infrastructure for hypothetical future scaling
- premature performance optimization
- broad refactors unrelated to the active task

## 3.2 Simplicity rules

- Prefer template conventions.
- Prefer direct code over framework-building.
- Add a helper only when it simplifies real repeated behavior.
- Do not create interfaces for internal code that has only one implementation.
- External vendors may have a thin adapter because mocks are required.
- Avoid a new dependency if the existing stack can reasonably solve the task.
- Do not add database columns “for future use”.
- Do not create generic metadata systems when explicit fields are clearer.
- Refactor duplication only when it is meaningful, not cosmetic.
- Do not spend time polishing non-MVP areas.
- Do not rewrite working template infrastructure.
- Do not optimize code without evidence of an actual problem.

When two solutions both work, choose the smaller one.

---

# 4. Autonomous Decision Policy

For ordinary ambiguity:

**Do not ask the user.**

Instead:

1. inspect this specification;
2. inspect repository conventions;
3. choose the smallest robust option;
4. implement it;
5. document the decision only if it meaningfully affects future development.

Examples that do **not** require a question:

- names
- route naming
- component organization
- module organization
- UI spacing
- error text
- loading skeleton vs spinner
- empty-state design
- test file organization
- minor schema choices
- small library choice
- internal function boundaries
- pagination implementation
- form UX details

Use recommended defaults and continue.

---

# 5. Human Approval Gates

Human approval is required immediately before:

- using a real production secret;
- reading or exposing a secret from `.env`, credential store, keychain, shell history, or cloud config;
- changing production infrastructure;
- deploying to production;
- modifying production databases;
- destructive database operations;
- database downgrade against non-disposable data;
- deleting remote branches;
- force-pushing;
- rewriting published Git history;
- deleting large amounts of user data;
- sending real email/messages;
- posting real content to social media during development/testing;
- making paid external API calls unless the user has explicitly authorized that spend;
- creating/changing paid cloud resources;
- `sudo`;
- writing outside the project directory when not required;
- any irreversible external side effect.

A request for approval must contain:

- exact action;
- why it is needed;
- expected side effect;
- safest alternative if approval is denied.

All unrelated development must continue before stopping at that gate.

---

# 6. GitHub Delivery Contract

## 6.1 Repositories

Base template:

```text
https://github.com/fastapi/full-stack-fastapi-template
```

Delivery repository:

```text
https://github.com/sajjadatma/gold-app.git
```

Target branch:

```text
main
```

The delivery repository is initially empty.

## 6.2 Bootstrap Git setup

At T00:

1. Start from `fastapi/full-stack-fastapi-template`.
2. Preserve the template remote as:

```text
upstream
```

3. Configure:

```text
origin = https://github.com/sajjadatma/gold-app.git
```

4. Use:

```text
main
```

as the delivery branch.

Do not force-push.

Do not rewrite upstream history.

## 6.3 Mandatory stage push

At the end of **every successfully completed stage**:

1. run the stage verification commands;
2. confirm no unexpected secrets are staged;
3. inspect `git diff`;
4. commit with a concise stage-oriented commit message;
5. verify `origin` exactly matches the delivery repository;
6. push normally to `origin/main`;
7. verify the pushed commit SHA;
8. record the stage status in `docs/progress.md`.

Example:

```text
feat(T04): complete brand asset import
```

or:

```text
test(T11): complete integrity evaluation workflow
```

Normal push to:

```text
origin/main
```

is explicitly authorized by the user.

The following are **not** authorized automatically:

- `git push --force`
- `git push --force-with-lease`
- remote branch deletion
- history rewrite
- deleting tags
- changing repository settings

If a normal push is blocked by remote policy, do not bypass the policy. Report the exact blocker.

---

# 7. Technology Stack

Use the Full Stack FastAPI Template as-is wherever practical.

## Backend

- Python
- FastAPI
- SQLModel
- PostgreSQL
- Alembic
- Pydantic
- PyJWT/authentication from template
- Pytest

## Frontend

- React
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Tailwind CSS
- shadcn/ui
- generated OpenAPI TypeScript client
- Playwright

## Infrastructure

- Docker Compose
- existing template CI conventions
- Redis for async jobs
- `arq` for the single background worker

## Storage

Development:

- private local file storage

Production adapter:

- S3-compatible object storage

## AI

Use only thin external adapters required by current features:

- text generation
- image generation/editing
- vision/evaluation

Implement:

- one fake/mock provider used by tests and local deterministic demo flow;
- one configurable production implementation where credentials are available.

Do not build a generic provider marketplace.

## Social

- Instagram publishing adapter
- fake provider for tests
- real provider implementation/configuration for Instagram professional accounts

---

# 8. Application Architecture

Use:

```text
Modular Monolith
+
One Background Worker
+
PostgreSQL
+
Private Object Storage
```

Do not create microservices.

Suggested domain grouping:

```text
backend/app/
  api/
  core/
  models.py
  modules/
    brands/
    brand_import/
    brand_models/
    products/
    generations/
    content/
    publishing/
  providers/
    storage/
    ai/
    instagram/
  workers/
```

Keep this structure practical.

If fewer files are clearer, use fewer files.

Do not split each module into unnecessary controller/service/repository/domain layers.

---

# 9. Roles and Authorization

MVP roles:

## Owner

Can:

- manage brand
- manage members
- import brand assets
- validate/activate BrandProfile
- manage human models
- manage products
- generate content
- approve/reject content
- connect Instagram
- publish approved content

## Content Manager

Can:

- view active brand profile
- manage permitted brand assets
- manage human models
- manage products
- generate images
- generate/edit captions
- prepare drafts
- send drafts for approval

Cannot:

- activate a BrandProfile
- manage brand membership
- connect/disconnect social account
- perform final publish
- bypass failed integrity result

## Internal Platform Admin

Reuse/extend the template's superuser capability minimally.

Needed only for platform support and system-level debugging.

Do not build a large admin product.

---

# 10. Core Data Model

Implement only fields required by current workflows.

## Brand

- `id`
- `name`
- `slug`
- `status`
- timestamps

## Membership

- `id`
- `user_id`
- `brand_id`
- `role`
- timestamps

Unique membership per user/brand.

## BrandImport

- `id`
- `brand_id`
- `status`
- `uploaded_file_count`
- `processed_file_count`
- `error_count`
- `created_by`
- timestamps

Statuses:

- `pending`
- `processing`
- `needs_review`
- `completed`
- `failed`

## BrandAsset

- `id`
- `brand_id`
- `import_id`
- `asset_type`
- `original_filename`
- `storage_key`
- `content_type`
- `size_bytes`
- `checksum`
- optional `width`
- optional `height`
- optional `page_count`
- minimal JSON metadata where necessary
- `processing_status`
- timestamps

Asset types:

- `brand_book`
- `logo`
- `font`
- `image`
- `campaign_reference`
- `pattern`
- `graphic_element`
- `design_source`
- `other`

## BrandProfile

- `id`
- `brand_id`
- `version`
- `status`
- `profile_json`
- `created_from_import_id`
- timestamps
- `activated_at`

Statuses:

- `draft`
- `needs_review`
- `active`
- `archived`

Exactly one active profile per brand.

## BrandModel

- `id`
- `brand_id`
- `type`
- `name`
- `status`
- `is_default`
- minimal configuration JSON
- timestamps

Types:

- `virtual`
- `real`

Statuses:

- `draft`
- `generating`
- `ready`
- `archived`
- `failed`

## BrandModelReference

- `id`
- `brand_model_id`
- `storage_key`
- `content_type`
- `is_canonical`
- timestamps

## ConsentRecord

For real models:

- `id`
- `brand_model_id`
- `confirmed_by_user_id`
- `confirmation_text_version`
- `permission_scope`
- `confirmed_at`

A real model cannot become ready/default without consent.

## Product

- `id`
- `brand_id`
- `name`
- optional `sku`
- `category`
- optional `metal_type`
- optional `metal_color`
- optional `stone_type`
- optional `description`
- optional `integrity_notes`
- `status`
- timestamps

Categories:

- ring
- necklace
- bracelet
- earrings
- set
- pendant
- other

## ProductImage

- `id`
- `product_id`
- `storage_key`
- `content_type`
- optional dimensions
- `is_primary`
- `quality_status`
- optional quality findings JSON
- timestamps

## GenerationRequest

- `id`
- `brand_id`
- `product_id`
- `brand_profile_id`
- optional `brand_model_id`
- `mode`
- `aspect_ratio`
- `status`
- provider/model metadata
- prompt version
- minimal request parameters JSON
- error information
- timestamps

Modes:

- `studio`
- `on_model`
- `campaign`

## GeneratedAsset

- `id`
- `generation_request_id`
- `storage_key`
- content metadata
- `integrity_status`
- optional integrity findings JSON
- timestamps

Integrity:

- `pending`
- `passed`
- `needs_review`
- `failed`

## ContentDraft

- `id`
- `brand_id`
- `product_id`
- `generated_asset_id`
- `caption`
- `hashtags`
- optional `cta`
- `status`
- `created_by`
- optional `approved_by`
- timestamps

Statuses:

- `draft`
- `needs_approval`
- `approved`
- `rejected`
- `published`
- `publish_failed`

## SocialConnection

Store only required connection metadata.

Never expose tokens through API responses.

## PublishJob

- draft reference
- provider
- status
- remote post id/url when available
- error info
- timestamps

---

# 11. Brand Import — MVP Scope

The brand already exists.

The application must import as much of the existing identity as is practical.

Supported upload types:

## Process directly

- PDF
- PNG
- JPEG
- WebP
- SVG
- TTF
- OTF
- WOFF
- WOFF2
- ZIP

## Accept and preserve as source assets

- AI
- EPS
- PSD

Full structural editing/parsing of AI/EPS/PSD is **not** required.

If safe preview extraction is simple and reliable, implement it.

Otherwise store the original and classify it.

Do not delay MVP to build a professional Adobe-file parser.

---

# 12. Upload Security

All uploads are untrusted.

Required:

- server-generated storage keys
- private-by-default storage
- tenant authorization
- MIME validation
- extension validation
- file signature checks for common processed formats
- configurable size limits
- filename sanitization
- checksums
- image decode safety limits
- SVG sanitization before browser rendering
- ZIP path traversal prevention
- archive expanded-size limit
- archive file-count limit
- reject symlinks inside archives
- reject unsupported nested archive behavior
- PDF processing limits

Recommended configurable defaults:

```text
PDF: 50 MB
Image: 25 MB
Font: 20 MB
Design source: 150 MB
ZIP: 250 MB
Max extracted files: 500
Max expanded archive size: 500 MB
```

Do not create an enterprise-grade malware platform.

Implement the practical protections needed for the MVP.

---

# 13. Brand Intelligence

Pipeline:

```text
Upload
  ↓
Validate
  ↓
Private storage
  ↓
Classify asset
  ↓
Extract available text/metadata
  ↓
Analyze PDF pages and visual references
  ↓
Produce structured BrandProfile candidate
  ↓
Detect conflicts/uncertainty
  ↓
Owner review
  ↓
Activate profile
```

For PDFs:

- use embedded text when available;
- render/analyze visual pages when needed;
- do not require a separate heavy OCR infrastructure for MVP1.

All AI structured output must be validated through Pydantic before persistence.

Do not trust arbitrary model JSON.

Do not invent missing brand rules.

Unknown values remain unknown.

---

# 14. BrandProfile Contract

The profile must be useful directly by image and text generation.

Minimum logical shape:

```json
{
  "identity": {
    "brand_name": "",
    "tagline": "",
    "story": "",
    "positioning": "",
    "audience": [],
    "personality": []
  },
  "colors": [],
  "typography": [],
  "logos": [],
  "photography": {
    "lighting": [],
    "backgrounds": [],
    "composition": [],
    "contrast": "",
    "shadow_style": "",
    "retouching": [],
    "prohibited_styles": []
  },
  "human_model_style": {
    "appearance": [],
    "makeup": [],
    "hair": [],
    "wardrobe": [],
    "hands_and_nails": [],
    "posing": []
  },
  "tone_of_voice": {
    "languages": [],
    "tone": [],
    "caption_style": "",
    "emoji_policy": "",
    "cta_style": "",
    "hashtag_style": ""
  },
  "graphic_system": {
    "patterns": [],
    "decorative_elements": [],
    "layout_principles": []
  },
  "social_media": {
    "preferred_ratios": [],
    "visual_rules": [],
    "logo_rules": []
  },
  "dos": [],
  "donts": []
}
```

Where practical, extracted fields should retain lightweight provenance:

- source asset id
- page number
- confidence

Do not build a complex knowledge graph.

---

# 15. Brand Asset Library

Required UI:

- grid/list of imported assets
- type filter
- file name
- preview where supported
- original download for authorized user
- active logo marking where applicable
- archive/remove from active use
- source import relation

The original uploaded file must be preserved unless the user explicitly deletes it.

Do not silently overwrite originals.

---

# 16. Brand Validation

Owner must be able to:

- inspect extracted identity
- correct fields
- select correct logo variants
- correct color values
- correct typography
- correct photography rules
- correct tone of voice
- resolve obvious conflicting extraction results
- activate the profile

This is **validation of imported identity**, not a brand-book creation tool.

Do not add design tooling.

---

# 17. Human Brand Models

Support both:

## 17.1 Virtual model

User can define a minimal visual direction:

- gender presentation
- apparent age range
- skin appearance
- hair
- makeup
- wardrobe
- hand/nail style
- optional notes

The active BrandProfile automatically influences the model.

Generate a small set of previews.

User chooses a canonical reference.

Avoid fine-tuning in MVP1.

Use reference-based generation.

## 17.2 Real model

User uploads reference photos.

Required:

- reference asset storage
- consent confirmation
- permission scope
- canonical reference selection

Do not activate real model without consent record.

Do not implement legal-document workflow beyond the required confirmation record.

---

# 18. Product Catalog

Required:

- product list
- create
- edit
- archive
- category
- optional SKU
- useful jewelry metadata
- source images
- primary image

At least one source image is required before image generation.

Image quality check should detect practical issues such as:

- very low resolution
- obviously blurred input
- severe under/over exposure
- unusable crop

Quality warning should normally be advisory.

Only block when processing cannot reasonably continue.

---

# 19. AI Photography Studio

MVP generation modes:

## Studio

Goal:

High-quality professional product image while preserving jewelry as faithfully as possible.

## On Model

Place/show the jewelry using the selected real or virtual brand model.

Requires a ready model.

## Campaign

Create a creative branded advertising image using the active BrandProfile.

Required configurable options only:

- mode
- aspect ratio
- selected product/source image
- model when applicable
- minimal style controls

Do not build a Photoshop-like editor.

Do not build node-based generation workflows.

---

# 20. Product Integrity Evaluation

After generation, compare source product with generated result.

Check as feasible:

- silhouette
- major geometry
- visible stone count
- stone placement
- ring/band/chain structure
- pendant geometry
- metal color
- missing major elements
- added major elements

Result:

```text
passed
needs_review
failed
```

Rules:

- `failed` cannot be approved.
- `needs_review` must show a source/generated comparison.
- final human approval remains mandatory.

Do not claim automatic verification is perfect.

---

# 21. Caption Generation

Use:

- active BrandProfile
- product metadata
- selected generated asset
- language/tone rules

Generate:

- one primary caption
- two alternatives
- CTA
- suggested hashtags

Allow manual editing.

Never silently overwrite user-edited text.

Do not create a full copywriting suite.

---

# 22. Review & Approval

Content review page must show:

- source jewelry image
- final generated image
- integrity result
- product metadata
- selected brand profile version
- selected human model where applicable
- caption
- hashtags
- CTA
- status

Owner actions:

- approve
- reject
- request regeneration/edit

A Content Manager can prepare drafts but cannot final-publish.

---

# 23. Instagram Publishing

MVP scope:

- Instagram professional account connection
- single image feed post
- publish now
- result state
- retryable technical failure where safe

Not in MVP:

- Reels
- stories
- carousel
- analytics
- content calendar
- recurring auto-posting
- multi-social cross-posting

Development must use fake publishing by default.

A real test post is an external side effect and requires human approval.

---

# 24. Required Frontend Pages

Keep navigation simple.

## Authentication

Reuse template:

- login
- password recovery
- user settings as appropriate

## Main application

```text
/dashboard

/brand/import
/brand/imports/:id
/brand/assets
/brand/profile

/models
/models/new
/models/:id

/products
/products/new
/products/:id

/studio
/studio/generations/:id

/content
/content/:id

/social

/team
/settings
```

Do not create separate pages if a dialog or existing page is simpler.

---

# 25. UI Direction

The product is for jewelry brands.

Use a restrained premium feel:

- clean
- minimal
- image-forward
- high readability
- generous but not excessive spacing
- neutral UI
- brand content should provide the visual personality

Use existing shadcn/ui components.

Do not build a custom design system.

Desktop-first responsive web app.

Mobile must remain usable, but no separate mobile UI architecture is required.

Accessibility basics are required:

- proper labels
- keyboard-accessible controls
- visible focus
- semantic buttons/links
- image alt text where relevant
- reasonable contrast

---

# 26. Background Jobs

Use exactly one practical asynchronous worker setup:

```text
Redis + arq
```

Use background jobs only for long-running work such as:

- brand import analysis
- PDF processing
- AI brand intelligence
- virtual model generation
- image generation
- integrity evaluation
- publish retry when appropriate

Each job needs:

- persisted status
- user-visible failure
- bounded retry when appropriate
- basic idempotency for operations that can duplicate external effects

Do not build a generic distributed workflow engine.

---

# 27. External Adapter Rules

External systems require small boundaries because tests must not depend on real services.

Allowed thin adapters:

```text
Storage
AI text
AI image
AI vision/evaluation
Instagram
```

Rules:

- keep adapters small;
- do not build generic registries;
- domain code should not directly expose vendor-specific objects;
- fake implementations must support deterministic tests;
- production implementation can use environment configuration;
- if credentials are missing, do not block unrelated work.

---

# 28. Missing Credential Policy

Missing credentials must never stop the whole project.

When a credential is unavailable:

1. finish domain logic;
2. finish the real adapter code as far as possible;
3. implement fake adapter;
4. write unit/contract tests;
5. write configuration instructions;
6. mark only the live integration verification as pending;
7. continue all remaining tasks.

Never fabricate a secret.

Never print a secret.

---

# 29. Testing Strategy

Do not over-test third-party libraries.

Test our behavior.

## Backend

Use Pytest for:

- tenant isolation
- authorization
- import validation
- data model constraints
- profile activation rules
- real-model consent rule
- product requirements
- generation workflow
- integrity gates
- approval
- publishing gates

## Frontend E2E

Use Playwright for critical journeys.

Do not attempt exhaustive screenshot testing.

## Mock providers

CI must not depend on:

- paid AI
- real Instagram
- real S3

Complete E2E must work with fake providers.

---

# 30. Security Requirements

Mandatory:

- tenant isolation
- authorization on every tenant-owned resource
- private asset delivery
- no direct secret exposure
- secure token storage strategy
- upload validation
- archive traversal protection
- sanitized SVG handling
- safe error responses
- audit trail for approval and publish actions
- no secrets committed to Git

Before every push:

- inspect staged files for obvious secret files;
- `.env` must not be committed;
- `.env.example` may contain only placeholders.

Do not add heavyweight security infrastructure unrelated to these requirements.

---

# 31. Logging and Errors

Use existing/simple application logging.

User-facing async jobs need useful states:

```text
queued
processing
completed
failed
```

Errors should be actionable but not leak:

- stack traces
- secrets
- internal tokens
- private filesystem paths

Use Sentry support already present if appropriate.

Do not create a custom observability platform.

---

# 32. MVP1 Out of Scope

Do not implement:

- brand identity creation from scratch
- AI logo generation
- full graphic editor
- Figma-like design tools
- video generation
- Reels generation
- Story publishing
- TikTok
- Telegram
- X
- Pinterest
- social analytics
- automated DMs
- campaign analytics
- autonomous posting without approval
- advanced scheduler/calendar
- e-commerce
- checkout
- inventory management
- ERP
- accounting
- jewelry price engine
- per-brand model fine-tuning
- native iOS/Android app
- microservices
- Kubernetes
- advanced organization billing
- subscription billing unless specifically required later

If an idea is useful but outside scope, add one short line to:

```text
docs/post-mvp-backlog.md
```

Do not implement it.

---

# 33. OpenCode Single-Agent Rule

Use one primary LLM/agent for MVP1.

Do not spawn specialist subagents automatically.

Do not create an agent hierarchy.

Do not delegate tasks through internal multi-agent orchestration.

The single agent owns:

- architecture
- backend
- frontend
- tests
- documentation
- integration
- delivery

This avoids cross-agent inconsistency and unnecessary complexity.

---

# 34. Required Documentation

Create only useful project documentation:

```text
AGENTS.md
README.md

docs/
  product-spec.md
  architecture.md
  data-model.md
  api-contracts.md
  security.md
  testing.md
  progress.md
  delivery.md
  post-mvp-backlog.md
  final-report.md
  decisions/
```

Do not create large amounts of duplicate documentation.

`product-spec.md` may reference this specification rather than duplicate it unnecessarily.

ADRs should be created only for meaningful decisions.

---

# 35. OpenCode Behavioral Rules for AGENTS.md

Create a root `AGENTS.md` containing, at minimum:

```md
# Jewelry Brand Studio Engineering Rules

Build MVP1 autonomously.

## Priority

1. Correct MVP behavior
2. Security and tenant isolation
3. Simplicity
4. Tests
5. Maintainability
6. Performance only when needed

## No overengineering

Implement only current MVP acceptance criteria.

Do not build infrastructure, abstractions, frameworks, generic systems, or future-facing features unless required now.

Prefer the smallest working solution.

## Questions

Do not ask routine questions.

Choose the strongest reasonable recommendation and continue.

Ask only before dangerous, destructive, costly, secret-bearing, production, or irreversible external operations.

## Architecture

Preserve Full Stack FastAPI Template conventions.

Use a modular monolith.

One background worker only.

No microservices.

## Agents

Use one primary agent.

Do not spawn subagents.

## AI

Keep external provider adapters thin.

Fake providers must support tests.

Validate structured AI output before persistence.

## Git

Target:
https://github.com/sajjadatma/gold-app.git

Branch:
main

At the end of every completed stage:

- verify tests
- inspect diff
- commit
- push normally to origin/main
- update docs/progress.md

Never force-push or rewrite published history without human approval.

## Testing

Do not weaken/delete tests to make a build green.

When OpenAPI changes, regenerate the frontend client.

## Security

Never read or expose secrets unless explicitly required and approved.

Never commit credentials.

Treat uploads as untrusted.

Protect tenant boundaries.

## Completion

Continue stage by stage until the MVP Definition of Done is satisfied.
```

---

# 36. OpenCode Permission Policy

Configure project-level OpenCode permissions with this intent.

Exact schema may be adapted to the installed OpenCode version.

## Automatically allowed

Inside the project workspace:

- read source files
- search files
- edit/create source files
- run formatter
- run linters
- run type checker
- run tests
- run local development servers
- install necessary project dependencies
- generate Alembic revisions
- run local `alembic upgrade head`
- build frontend
- regenerate OpenAPI client
- run Playwright
- Docker Compose startup/build/log inspection
- normal git status/diff/log
- git add
- git commit
- normal push to verified `origin/main`
- fetch public technical documentation

## Ask before

- any force push
- remote branch deletion
- git reset that discards work
- git clean that deletes files
- destructive restore/checkout
- production deploy
- production database write
- database downgrade against non-disposable data
- Docker volume deletion
- deleting persistent local data if it may matter
- `sudo`
- SSH/SCP to external hosts
- real social-media publication
- live paid AI calls not previously authorized
- cloud-resource creation/modification with cost implications
- reading real secrets
- writing outside project directory where unnecessary

## Deny by default

- expose/copy secrets into logs
- commit `.env`
- force push without explicit approval
- disable security controls to make a test pass
- bypass branch protection
- install software globally when project-local installation works
- multi-agent spawning for this MVP

---

# 37. Build Stages

A stage is complete only when its acceptance gate passes.

Every successful stage ends with:

```text
verify → update docs/progress.md → commit → push origin/main
```

---

## T00 — Bootstrap & Baseline

### Work

- initialize from Full Stack FastAPI Template;
- configure `upstream` to the template repository;
- configure `origin` to `https://github.com/sajjadatma/gold-app.git`;
- normalize delivery branch to `main`;
- inspect existing architecture;
- run baseline tests/build;
- create project docs skeleton;
- create `AGENTS.md`;
- configure OpenCode project rules/permissions;
- record any template baseline issue before modifying related code.

### Gate

- backend installs;
- frontend installs;
- PostgreSQL development workflow is understood/runnable;
- baseline backend tests pass or pre-existing failure is documented with evidence;
- frontend production build passes or pre-existing failure is documented;
- no project feature code yet;
- origin verified;
- normal first push succeeds.

### Push

```text
chore(T00): bootstrap Jewelry Brand Studio
```

---

## T01 — MVP Contracts

### Work

Create concise:

- `docs/product-spec.md`
- `docs/architecture.md`
- `docs/data-model.md`
- `docs/api-contracts.md`
- `docs/security.md`
- `docs/testing.md`
- `docs/progress.md`
- `docs/delivery.md`

Do not turn planning into weeks of documentation.

The contract must be enough to implement.

### Gate

- every MVP module maps to data/API/UI acceptance criteria;
- out-of-scope list is present;
- no unresolved routine design question blocks coding.

### Push

```text
docs(T01): lock MVP1 contracts
```

---

## T02 — Brand + Multi-Tenant Access

### Work

Implement:

- Brand
- Membership
- Owner
- Content Manager
- brand selection/context
- tenant-scoped authorization
- minimal team UI

### Required tests

- user cannot access unrelated brand;
- Content Manager permission limits;
- Owner access;
- superuser behavior remains controlled.

### Gate

Tenant isolation tests pass.

### Push

```text
feat(T02): add brand tenancy and roles
```

---

## T03 — Private Storage

### Work

Implement simplest required storage boundary:

- local private storage for development/tests;
- S3-compatible production adapter;
- authenticated download/access;
- server-generated keys;
- checksum;
- upload limits.

### Gate

- unauthorized asset access fails;
- tenant asset isolation passes;
- local adapter tests pass;
- production adapter configuration documented.

### Push

```text
feat(T03): add private brand asset storage
```

---

## T04 — Brand Import

### Work

Implement:

- BrandImport
- BrandAsset
- multi-file upload
- PDF
- standard images
- SVG
- fonts
- design-source storage
- ZIP extraction
- processing statuses
- import detail UI
- asset library UI

### Required security tests

- extension/MIME mismatch
- archive traversal
- archive excessive expansion/file count
- unsafe SVG handling
- unauthorized access

### Gate

A brand can import a realistic brand asset bundle and review stored assets.

### Push

```text
feat(T04): implement secure brand import
```

---

## T05 — Brand Intelligence

### Work

Implement:

- text/metadata extraction
- PDF page analysis
- visual reference analysis
- structured BrandProfile generation
- Pydantic validation
- source provenance where practical
- uncertainty/conflict reporting
- fake AI provider for deterministic tests
- real provider adapter/configuration

### Gate

Fixture brand materials generate a schema-valid profile candidate.

No arbitrary unvalidated AI JSON is persisted.

### Push

```text
feat(T05): extract structured brand intelligence
```

---

## T06 — Brand Validation & Activation

### Work

Implement:

- profile review page
- corrections
- logo choice
- colors
- fonts
- photography rules
- tone
- version activation
- archival of previous active version

### Gate

- exactly one active profile per brand;
- only Owner can activate;
- generation cannot start without active profile.

### Push

```text
feat(T06): add brand profile validation
```

---

## T07 — Real & Virtual Brand Models

### Work

Implement:

- BrandModel
- references
- virtual-model configuration
- preview generation
- canonical reference
- real model upload
- consent record
- default model

### Gate

- virtual model can reach ready state using fake provider in tests;
- real model cannot become active/default without consent;
- tenant isolation passes.

### Push

```text
feat(T07): add real and virtual brand models
```

---

## T08 — Product Catalog

### Work

Implement:

- product list/create/edit/archive
- product images
- primary image
- required category/name/source image
- basic image quality feedback
- product detail UI

### Gate

A user can create a jewelry product with source imagery and use it as a generation input.

### Push

```text
feat(T08): add jewelry product catalog
```

---

## T09 — AI Generation Foundation

### Work

Implement the minimum external AI boundaries needed by the product:

- text
- image
- vision/evaluation

Include:

- fake deterministic providers
- configured real provider implementation
- request provenance
- safe errors
- environment documentation

Do not build a generic provider system.

### Gate

Application can run all AI workflows under fake providers without paid credentials.

### Push

```text
feat(T09): add AI generation adapters
```

---

## T10 — AI Photography Studio

### Work

Implement:

- Studio generation
- On-Model generation
- Campaign generation
- aspect-ratio selection
- source-image selection
- model selection where required
- active BrandProfile automatically applied
- GeneratedAsset persistence
- studio/generation UI
- async status UI

### Gate

From one product, user can generate all three MVP modes using fake provider.

Real provider path is configurable.

### Push

```text
feat(T10): build AI jewelry photography studio
```

---

## T11 — Product Integrity Evaluation

### Work

Implement:

- source/generated comparison
- vision evaluation
- `passed`
- `needs_review`
- `failed`
- findings display
- approval gate

### Gate

- failed output cannot be approved;
- needs-review output clearly shows comparison/findings;
- fake evaluation enables deterministic tests.

### Push

```text
feat(T11): add product integrity review
```

---

## T12 — Caption & Content Draft

### Work

Implement:

- primary caption
- two alternatives
- CTA
- hashtags
- editing
- ContentDraft
- brand-aware generation
- manual text preservation

### Gate

User can create and edit a complete social draft from an approved/generated image.

### Push

```text
feat(T12): add branded social content drafts
```

---

## T13 — Approval Workflow

### Work

Implement:

- Owner approve
- Owner reject
- regeneration/edit path
- Content Manager submission
- audit data sufficient to know who approved and when

### Gate

- Content Manager cannot perform final publish;
- non-approved draft cannot publish;
- failed-integrity asset cannot be approved.

### Push

```text
feat(T13): add owner content approval
```

---

## T14 — Instagram Connection & Publishing

### Work

Implement:

- Instagram connection configuration
- real adapter
- fake adapter
- single-image feed publishing
- publish result
- error state
- safe retry strategy
- token handling without exposing token to frontend

### Gate

Mock E2E publishing succeeds.

Live publish is tested only after explicit approval and credentials are available.

### Push

```text
feat(T14): add Instagram publishing
```

---

## T15 — Complete End-to-End Workflow

Create a Playwright critical-path test:

```text
login
→ create/select brand
→ import brand PDF/assets fixture
→ process brand intelligence
→ review/activate BrandProfile
→ create virtual model
→ create product
→ upload source image
→ generate Studio image
→ integrity evaluation
→ generate caption
→ submit
→ Owner approve
→ fake Instagram publish
→ verify published state
```

Also add a smaller real-model path validating consent requirements.

### Gate

Core E2E passes against a clean test database with fake providers.

### Push

```text
test(T15): verify complete MVP workflow
```

---

## T16 — Hardening

Strictly fix concrete MVP issues only.

Review:

- tenant isolation
- authorization
- upload security
- asset privacy
- migration integrity
- async failure states
- approval gates
- publishing idempotency
- responsive usability
- accessibility basics
- dependency vulnerabilities relevant to actual use

Do not start new architecture work.

Do not refactor for aesthetics.

### Gate

No known critical/high MVP security or correctness issue remains.

### Push

```text
fix(T16): harden MVP delivery
```

---

## T17 — Delivery

### Work

Prepare:

- final README
- `.env.example`
- local setup
- Docker setup
- provider configuration
- migrations
- seed/demo instructions if useful
- deployment notes
- final test report
- `docs/final-report.md`

Run from clean state where practical.

### Final verification

Backend:

```text
pytest
ruff
mypy / ty as used by template
```

Frontend:

```text
lint
type/build
Playwright critical path
```

Database:

```text
fresh migration to head
```

OpenAPI:

```text
generated frontend client is current
```

Git:

```text
clean working tree
origin verified
main pushed
```

### Push

```text
release(T17): deliver Jewelry Brand Studio MVP1
```

---

# 38. Stage Execution Loop

For every stage:

```text
READ CURRENT STAGE
        ↓
INSPECT RELEVANT EXISTING CODE
        ↓
IMPLEMENT MINIMUM REQUIRED BEHAVIOR
        ↓
ADD/UPDATE FOCUSED TESTS
        ↓
RUN FOCUSED TESTS
        ↓
FIX FAILURES
        ↓
RUN RELEVANT REGRESSION TESTS
        ↓
REGENERATE API CLIENT IF CONTRACT CHANGED
        ↓
UPDATE ONLY RELEVANT DOCS
        ↓
INSPECT DIFF FOR SCOPE CREEP
        ↓
VERIFY NO SECRET IS STAGED
        ↓
UPDATE docs/progress.md
        ↓
COMMIT
        ↓
VERIFY ORIGIN
        ↓
PUSH origin/main
        ↓
VERIFY REMOTE COMMIT
        ↓
START NEXT STAGE
```

Do not ask the user between stages.

---

# 39. Scope-Creep Check Before Every Commit

Before every stage commit, inspect the diff and remove unnecessary complexity.

Ask internally:

- Did I implement anything not required by this stage?
- Did I add an abstraction with no immediate need?
- Did I add a dependency that can be removed?
- Did I create generic infrastructure for a hypothetical future feature?
- Did I refactor unrelated working code?
- Could the same behavior be delivered with less code?

If yes, simplify before committing.

---

# 40. Definition of Done — Individual Stage

A stage is done only when:

- required behavior exists;
- relevant migrations exist;
- relevant API contract works;
- frontend behavior exists if required;
- focused tests exist;
- focused tests pass;
- relevant regression tests pass;
- generated client is updated when API changes;
- no known regression was introduced;
- no secret is committed;
- scope remains within MVP;
- progress documentation is updated;
- stage is committed;
- stage commit is pushed to `origin/main`.

---

# 41. Definition of Done — MVP1

MVP1 is `READY FOR DELIVERY` only when all are true:

## Product

A user can:

1. authenticate;
2. create/select a jewelry brand;
3. import existing brand-book/assets;
4. receive structured brand intelligence;
5. review and activate it;
6. create a real or virtual brand model;
7. add a jewelry product and source photo;
8. generate Studio / On-Model / Campaign imagery;
9. review integrity;
10. generate/edit caption, CTA, and hashtags;
11. submit content;
12. approve as Owner;
13. publish using fake provider in E2E;
14. use the real Instagram adapter when properly configured.

## Engineering

- backend test suite passes;
- frontend build passes;
- lint/type checks pass;
- critical Playwright flow passes;
- clean database migrates to head;
- OpenAPI client is current;
- tenant isolation tests pass;
- upload security tests pass;
- `.env` is not committed;
- README is sufficient for a fresh setup;
- production adapters are documented;
- target repository contains every stage commit;
- final `main` is pushed;
- working tree is clean.

---

# 42. Valid Final Status

OpenCode must create:

```text
docs/final-report.md
```

with:

- final status
- final commit SHA
- repository
- implemented modules
- migrations
- API summary
- frontend routes
- storage configuration
- AI configuration
- Instagram configuration
- tests executed
- test results
- live tests not executed and why
- known MVP limitations
- required external credentials
- deployment instructions

Final status must be exactly one of:

```text
READY FOR DELIVERY
```

or:

```text
BLOCKED BY EXTERNAL REQUIREMENT
```

Do not use vague states such as:

```text
mostly done
probably ready
should work
almost complete
```

If only a live credential-dependent verification remains but the implementation and fake E2E are complete, clearly identify that external requirement rather than pretending it was tested.

---

# 43. Suggested OpenCode `/ship-mvp` Command

Create a project command equivalent to:

```md
---
description: Build Jewelry Brand Studio MVP1 autonomously to delivery
agent: build
---

Read:
@JEWELRY_BRAND_STUDIO_MVP1.md
@AGENTS.md

Execute the first incomplete stage and continue stage-by-stage until MVP1 satisfies the Definition of Done.

Rules:

- Do not ask routine questions.
- Use your strongest reasonable recommendation.
- Do not overengineer.
- Do not expand scope.
- Use one agent only.
- Preserve FastAPI template conventions.
- Test before completing a stage.
- Push every completed stage to origin/main.
- Never force-push.
- Never expose secrets.
- Stop only immediately before an action that requires human approval under the execution contract.
- If an external credential is missing, implement/test with a fake provider and continue all unrelated work.
- Do not declare READY FOR DELIVERY while known MVP failures remain.
```

---

# 44. Final Instruction to OpenCode

This document is the authoritative MVP1 execution contract.

Do not reinterpret it into a larger product.

Do not add “enterprise-ready” architecture for hypothetical future needs.

Do not pause for normal implementation questions.

Do not create extra agents.

Do not skip tests.

Do not bypass security.

Do not skip the mandatory stage pushes.

Build the simplest correct Jewelry Brand Studio MVP1, stage by stage, and continue until it is genuinely ready for delivery or an explicit external requirement makes further completion impossible.
