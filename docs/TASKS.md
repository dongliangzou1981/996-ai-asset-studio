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

## Sprint 7B

- [x] Read OpenAI API keys only through `config_json.api_key_env`
- [x] Keep real keys out of database records and job responses
- [x] Mark failed OpenAI runs as `failed` with concise `error_message`
- [x] Append OpenAI run success and failure logs
- [x] Save successful OpenAI images as `ai_generated` assets
- [x] Generate thumbnails and link assets to `generation_job_id`
- [x] Write result paths and asset ids to `output_json`
- [x] Cover missing config, missing env var, API failure, empty response, image save failure, and success with mocked tests
- [x] Preserve mock provider runner behavior
- [x] Update provider acceptance documentation
- [ ] Manual real OpenAI smoke test with a local `OPENAI_API_KEY`

## 2026-06-04 Acceptance

Verified:

- [x] Project CRUD
- [x] Job Center
- [x] Mock UI Job Creation
- [x] Mock Job Runner
- [x] Mock Pipeline Complete Flow
- [x] Asset Record Creation
- [x] Asset Binding To Generation Job

Accepted flow:

`Project -> Job -> Mock Runner -> Asset`

Status:

- Sprint 5: accepted
- Sprint 6: accepted
- Sprint 7A: complete
- Sprint 7B: complete

Development priorities:

- P0: Real AI UI generation loop, `Prompt -> Provider -> Image -> Asset -> Preview`
- P1: 996 package export, slicing, manifest
- P2: Provider security hardening, audit, concurrency control, batch jobs

## Sprint 7C Phase 1

- [x] Add `real_ui_generation` job type usage
- [x] Add Job Center real generation entry form
- [x] Capture prompt, provider, device type, width, height, and project id
- [x] Add `RealJobRunner` skeleton
- [x] Run `Prompt -> Provider -> RealJobRunner -> Asset -> Preview`
- [x] Generate placeholder PNG output only
- [x] Write real pipeline logs to `generation_jobs.logs`
- [x] Write placeholder result metadata to `generation_jobs.output_json`
- [x] Create `ui_preview` asset with `source = real_pipeline_placeholder`
- [x] Link placeholder asset to `generation_job_id`
- [x] Keep Mock Pipeline unchanged
- [ ] Connect real OpenAI provider
- [ ] Connect OpenRouter
- [ ] Connect ComfyUI
- [ ] 996 ZIP export
- [ ] Production slicing

Sprint 7C Phase 1 only establishes the real generation pipeline skeleton. It does not connect any real model.

## Sprint 7C Phase 1.5

- [x] Add Generation Wizard in Job Center
- [x] Step 1 selects project
- [x] Step 2 selects style profile
- [x] Step 3 selects base panel
- [x] Step 4 selects optional reference image
- [x] Step 5 captures prompt
- [x] Step 6 creates `real_ui_generation` job
- [x] Save `project_id`, `style_profile_id`, `base_panel_id`, `reference_image_id`, `prompt`, `device_type`, `width`, and `height` in `input_json`
- [x] Show project, style, base panel, reference image, and prompt in Job Detail
- [x] Show Project, Style, Panel, and Prompt source information in Assets
- [x] Keep real model providers disconnected

After Phase 1.5, the UI generation workflow is complete from user selections to job and asset traceability. The remaining gap is real model integration.
