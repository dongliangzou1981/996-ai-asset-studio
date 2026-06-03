# Database

SQL schema: `backend/app/db/schema.sql`

Alembic config: `backend/alembic.ini`

## Tables

- `projects`: project records.
- `style_profiles`: style templates attached to projects.
- `base_panels`: unified base panel specs.
- `reference_images`: reference image metadata.
- `ui_screens`: UI screen records.
- `assets`: generated or imported asset metadata.
- `exports`: export records.
- `generation_jobs`: generation job status records.
- `ai_providers`: provider config placeholder records without secrets.

## Relationships

- `style_profiles.project_id` references `projects.id`.
- `base_panels.project_id` references `projects.id`.
- `base_panels.style_profile_id` references `style_profiles.id`.
- `assets.project_id` references `projects.id` and can be null for loose assets.
- `assets.generation_job_id` references `generation_jobs.id` and can be null for uploaded assets.
- `reference_images.project_id` references `projects.id` and can be null for loose reference records.
- `generation_jobs.project_id` references `projects.id` and can be null for studio-wide test jobs.
- `generation_jobs.provider_id` references `ai_providers.id` and can be null for default mock execution.

## Migrations

- `0001_create_projects_style_profiles.py`: creates `projects` and `style_profiles`.
- `0002_base_panels_generation_jobs.py`: creates the Sprint 3 `base_panels` shape and `generation_jobs`.
- `0003_assets_jobs_state_flow.py`: updates assets, reference images, and generation job state fields for Sprint 4.
- `0004_mock_pipeline_assets_providers.py`: adds asset source/job linkage fields and `ai_providers`.
- `0005_unified_job_runner.py`: adds provider-backed job fields, output preview paths, and asset thumbnails.

Default local database URL:

```text
sqlite:///backend/data/studio.db
```

`DATABASE_URL` can override the Alembic database URL for PostgreSQL or another SQLAlchemy-supported backend.

## Base Panel Fields

- `project_id`
- `style_profile_id`
- `panel_type`
- `device_type`
- `width`
- `height`
- `texture`
- `border_style`
- `background_style`
- `color_scheme`

## Generation Job Fields

- `id`
- `project_id`
- `provider_id`
- `job_type`
- `status`
- `progress`
- `input_json`
- `output_json`
- `output_preview_path`
- `error_message`
- `retry_count`
- `logs`
- `created_at`
- `updated_at`

Allowed status values: `pending`, `running`, `completed`, `failed`, `cancelled`.

## Asset Fields

- `id`
- `project_id`
- `asset_type`
- `device_type`
- `width`
- `height`
- `file_path`
- `original_filename`
- `metadata_json`
- `source`
- `generation_job_id`
- `thumbnail_path`
- `created_at`
- `updated_at`

Allowed asset types: `reference_image`, `ui_preview`, `annotated_preview`, `sliced_component`, `base_panel`, `icon`.

Allowed asset sources: `uploaded`, `mock_generated`, `ai_generated`.

## AI Provider Fields

- `id`
- `name`
- `type`
- `enabled`
- `config_json`
- `created_at`
- `updated_at`

Provider types: `mock`, `openai`, `custom`. Prefer `api_key_env` inside `config_json`; do not commit real API keys.

## 996-Ready Output

Generated jobs write local output under:

```text
assets/uploads/996-ready/{generation_job_id}/
  previews/
  components/
  thumbnails/
  package/manifest.json
```
