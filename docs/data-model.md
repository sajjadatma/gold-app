# Data Model

All ids are UUIDs unless noted. All timestamps are UTC. Tenant-owned rows include `brand_id`.

## Template

- `User` (extended): email, hashed_password, is_active, is_superuser, full_name, created_at.
- `Item`: template demo entity; retained for baseline tests, unrelated to MVP flows.

## Tenancy

- `Brand`: id, name, slug (unique), status (`active|archived`), created_at, updated_at.
- `Membership`: id, user_id, brand_id, role (`owner|content_manager`), unique(user_id, brand_id).

## Import and assets

- `BrandImport`: id, brand_id, status (`pending|processing|needs_review|completed|failed`), uploaded_file_count, processed_file_count, error_count, created_by, created_at, updated_at.
- `BrandAsset`: id, brand_id, import_id, asset_type, original_filename, storage_key (unique), content_type, size_bytes, checksum, width, height, page_count, metadata_json, processing_status, is_active, created_at, updated_at.
- `BrandProfile`: id, brand_id, version, status (`draft|needs_review|active|archived`), profile_json, created_from_import_id, created_at, updated_at, activated_at. Partial unique index enforces one `active` profile per brand.

## Models

- `BrandModel`: id, brand_id, type (`virtual|real`), name, status (`draft|generating|ready|archived|failed`), is_default, config_json, created_at, updated_at.
- `BrandModelReference`: id, brand_model_id, storage_key, content_type, is_canonical, created_at.
- `ConsentRecord`: id, brand_model_id, confirmed_by_user_id, confirmation_text_version, permission_scope, confirmed_at.

## Products

- `Product`: id, brand_id, name, sku, category (`ring|necklace|bracelet|earrings|set|pendant|other`), metal_type, metal_color, stone_type, description, integrity_notes, status (`active|archived`), created_at, updated_at.
- `ProductImage`: id, product_id, storage_key, content_type, width, height, is_primary, quality_status (`ok|warning|blocked`), quality_findings_json, created_at.

## Generation

- `GenerationRequest`: id, brand_id, product_id, brand_profile_id, brand_model_id, mode (`studio|on_model|campaign`), aspect_ratio, status (`queued|processing|completed|failed`), provider, model, prompt_version, parameters_json, error_message, created_at, updated_at.
- `GeneratedAsset`: id, generation_request_id, storage_key, content_type, width, height, integrity_status (`pending|passed|needs_review|failed`), integrity_findings_json, created_at.

## Content and publishing

- `ContentDraft`: id, brand_id, product_id, generated_asset_id, caption, alternative_captions_json, hashtags, cta, status (`draft|needs_approval|approved|rejected|published|publish_failed`), created_by, approved_by, approved_at, created_at, updated_at.
- `SocialConnection`: id, brand_id (unique), provider (`instagram`), external_account_id, account_name, access_token, token_expires_at, status (`connected|disconnected|error`), created_at, updated_at. Tokens are never serialized.
- `PublishJob`: id, brand_id, draft_id, provider, status (`queued|processing|published|failed`), remote_post_id, remote_post_url, error_message, attempt_count, created_at, updated_at. Unique successful job per draft enforced in service.
