# Tasks

## Sprint 1

- [x] Create project directory structure
- [x] Initialize docs
- [x] Initialize Next.js 15 + TypeScript + Tailwind
- [x] Initialize FastAPI
- [x] Create database schema
- [ ] AI generation

## Sprint 2

- [x] Backend project CRUD
- [x] Frontend project management
- [x] Backend style profile CRUD
- [x] Frontend style management
- [x] Alembic initialization
- [x] FastAPI OpenAPI / Swagger contract
- [x] Backend CRUD tests
- [x] Frontend component tests
- [ ] AI generation

## Sprint 3

- [x] Backend Base Panel CRUD
- [x] Base Panel copy endpoint
- [x] Support seven panel types
- [x] Frontend `/panels` page
- [x] Frontend `/job-center` page
- [x] Add `generation_jobs` table
- [x] Add Alembic 0002 migration
- [x] Update API, database, architecture, tasks, and changelog docs
- [ ] AI generation

AI generation is not part of Sprint 3.

## Sprint 4

- [x] Backend asset CRUD
- [x] Backend image upload endpoint
- [x] Support loose assets with `project_id = null`
- [x] Support Sprint 4 asset types
- [x] Frontend `/assets` page
- [x] Generation job create/list/detail/update/retry API
- [x] Frontend `/job-center` creation, detail, log, and retry flow
- [x] Alembic 0003 migration
- [x] Backend tests for uploads, asset CRUD, job update, and retry
- [x] Frontend tests for `/assets` and `/job-center`
- [x] Update API, database, architecture, task, changelog, and test docs
- [ ] AI generation

AI generation is not part of Sprint 4.

## Sprint 5

- [x] Support `mock_ui_generation` jobs
- [x] Add pending/running/completed and pending/running/failed mock flows
- [x] Add mock worker service
- [x] Generate local placeholder PNG previews with Pillow
- [x] Create `ui_preview`, `annotated_preview`, and `sliced_component` result assets
- [x] Link generated assets to `generation_job_id`
- [x] Write result asset data to `job.output_json`
- [x] Add `POST /generation_jobs/mock-ui`
- [x] Add `POST /generation_jobs/{id}/run-mock`
- [x] Add `GET /generation_jobs/{id}/results`
- [x] Enhance `/job-center` with mock create, run, logs, and result assets
- [x] Enhance `/assets` with image preview, details, source, and job_id filtering
- [x] Add `ai_providers` placeholder table and API
- [x] Add Alembic 0004 migration
- [x] Add backend and frontend Sprint 5 tests
- [x] Update docs
- [ ] Real AI provider integration

AI generation is not part of Sprint 5.

## Sprint 6

- [x] Add unified `BaseJobRunner`
- [x] Add `MockJobRunner`, `OpenAIJobRunner`, and `CustomJobRunner`
- [x] Add unified `POST /generation_jobs/{id}/run`
- [x] Add `provider_id` and `output_preview_path` to generation jobs
- [x] Add provider config update and health check APIs
- [x] Add `thumbnail_path` to assets
- [x] Generate 996-ready preview, annotated preview, component slice, thumbnails, and manifest
- [x] Enhance `/job-center` with provider-backed job creation and execution
- [x] Enhance `/assets` with thumbnails, device filter, download, and path copy
- [x] Add `/providers` page
- [x] Add Alembic 0005 migration
- [x] Add backend and frontend tests
- [x] Update docs
- [ ] Production-grade external custom model adapter
- [ ] Secure secret vault integration

## Sprint 7A

- [x] Restrict provider `config_json` to `api_key_env`
- [x] Reject direct API key fields
- [x] Return provider health as `healthy` or `unhealthy`
- [x] Check OpenAI `api_key_env` presence
- [x] Check whether the named environment variable exists
- [x] Avoid returning real key values
- [x] Add `/providers` safety guidance
- [x] Add `PROVIDERS.md`
- [x] Add backend and frontend tests
