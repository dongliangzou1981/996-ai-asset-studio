# Changelog

## 0.7B.0 - 2026-06-04

- Hardened the real OpenAI Job Runner path to read keys only from `config_json.api_key_env`.
- Added safe OpenAI run failure handling for missing config, missing environment variables, API errors, empty image responses, and image save failures.
- Added `ai_generated` asset output handling with thumbnails and job result linkage.
- Added mocked OpenAI runner tests without external network access.
- Expanded provider setup and real generation acceptance guidance in `PROVIDERS.md`.

## 0.7A.0 - 2026-06-03

- Hardened provider `config_json` so only `api_key_env` is accepted.
- Added safe provider health checks with `healthy` and `unhealthy` statuses.
- Added provider security guidance in `PROVIDERS.md`.
- Enhanced `/providers` safety copy and health display.

## 0.6.0 - 2026-06-03

- Added unified Job Runner with mock, OpenAI, and custom provider paths.
- Added provider-backed `POST /generation_jobs/{id}/run`.
- Added OpenAI Images API execution path using provider `config_json`.
- Added provider update and health check APIs.
- Added generated thumbnails, output preview paths, and 996-ready package manifests.
- Enhanced `/job-center`, `/assets`, and added `/providers`.
- Added Alembic 0005 migration and Sprint 6 tests.

## 0.5.0 - 2026-06-03

- Added local Mock AI pipeline for `mock_ui_generation` jobs.
- Added mock worker that creates placeholder `ui_preview`, `annotated_preview`, and `sliced_component` PNG assets.
- Added job result endpoints and asset linkage through `generation_job_id`.
- Added asset source tracking with `uploaded` and `mock_generated`.
- Enhanced `/job-center` with mock job creation, run action, log timeline, and result assets.
- Enhanced `/assets` with image previews, detail view, source display, and job filter.
- Added `ai_providers` placeholder table and API without secret storage.
- Added Alembic 0004 migration and Sprint 5 tests.

## 0.4.0 - 2026-06-03

- Added asset CRUD API and local image upload endpoint.
- Added `/assets` page with upload, filters, list, and delete actions.
- Expanded `generation_jobs` API with create, detail, patch, and retry.
- Enhanced `/job-center` with mock job creation, details, logs, and failed-job retry.
- Added Alembic 0003 migration for assets, reference images, and generation job state fields.
- Added backend tests for asset upload, asset CRUD, job state updates, retry, and OpenAPI contract.
- Added frontend tests for asset management and job center workflows.

## 0.3.0 - 2026-06-03

- Added Base Panel CRUD and copy API.
- Added `/panels` Base Panel management page.
- Added `/job-center` page.
- Added `generation_jobs` table.
- Added Alembic 0002 migration.
- Added Base Panel and Job Center tests.

## 0.2.0 - 2026-06-03

- Added project CRUD API and frontend project management.
- Added style profile CRUD API and frontend style management.
- Initialized Alembic.
- Added FastAPI CRUD tests and frontend component tests.

## 0.1.0 - 2026-06-03

- Initialized Sprint 1 project scaffold.
- Added Next.js frontend.
- Added FastAPI backend.
- Added database schema.
- Added docs structure.
