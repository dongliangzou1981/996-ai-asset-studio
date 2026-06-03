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

## Relationships

- `style_profiles.project_id` references `projects.id`.
- `base_panels.project_id` references `projects.id`.
- `base_panels.style_profile_id` references `style_profiles.id`.
- `generation_jobs.project_id` references `projects.id`.

## Migrations

- `0001_create_projects_style_profiles.py`: creates `projects` and `style_profiles`.
- `0002_base_panels_generation_jobs.py`: creates the Sprint 3 `base_panels` shape and `generation_jobs`.

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
- `job_type`
- `status`
- `progress`
- `created_at`
- `updated_at`

