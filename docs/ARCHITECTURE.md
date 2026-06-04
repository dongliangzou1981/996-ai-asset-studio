# Architecture

## Directory Boundaries

- `frontend/`: Next.js 15 app for the local studio UI.
- `backend/`: FastAPI service for API, validation, persistence, and migration-backed data.
- `docs/`: product, architecture, API, database, and test documentation.
- `prompts/`: future prompt templates.
- `assets/`: local asset placeholder directory.
- `exports/`: local export placeholder directory.
- `scripts/`: utility scripts.
- `tests/`: shared test placeholder directory.

## Current Stack

- Frontend: Next.js 15, React, TypeScript, Tailwind CSS, Jest, Testing Library
- Backend: FastAPI, Uvicorn, Pydantic, pytest
- Database: SQLite for local development, Alembic migrations

## Data Flow

1. Frontend pages call `studioApi`.
2. `studioApi` uses `NEXT_PUBLIC_API_BASE_URL` or defaults to `http://127.0.0.1:8000`.
3. FastAPI validates JSON with Pydantic schemas and exposes OpenAPI.
4. `StudioDatabase` uses Python `sqlite3` for local persistence.
5. Alembic manages versioned schema changes.

## Sprint 3 Scope

- `/panels` manages Base Panel CRUD and copy.
- `/job-center` lists generation jobs.
- `panel_type` is constrained by Pydantic to the supported seven panel types.
- AI generation is intentionally not connected in Sprint 3.

## Sprint 4 Scope

- `/assets` manages uploaded and manually registered asset records.
- `POST /assets/upload` stores local image files under `assets/uploads`.
- Asset records support project-scoped and loose records with `project_id = null`.
- `/job-center` can create mock jobs, show details, display logs, and retry failed jobs.
- Generation jobs now track input, output, error, retry count, logs, status, and progress.
- AI generation is intentionally not connected in Sprint 4.

## Sprint 5 Scope

- `/generation_jobs/mock-ui` creates a local `mock_ui_generation` job.
- `/generation_jobs/{id}/run-mock` invokes `backend/app/mock_worker.py`.
- The mock worker uses Pillow to render local placeholder PNG files.
- Mock outputs create `ui_preview`, `annotated_preview`, and `sliced_component` asset records.
- Job result assets are linked through `assets.generation_job_id` and exposed by `/generation_jobs/{id}/results`.
- `/assets` can preview image files through `GET /assets/{id}/file`.
- `ai_providers` is a placeholder table for Sprint 6 provider integration and stores no secrets.
- AI generation is intentionally not connected in Sprint 5.

## Sprint 6 Scope

- `BaseJobRunner` defines the shared execution flow for provider-backed jobs.
- `MockJobRunner`, `OpenAIJobRunner`, and `CustomJobRunner` run through `JobRunnerService`.
- Jobs move through `pending -> running -> completed`, or `pending -> running -> failed`.
- The OpenAI runner calls the official Images API only when provider config supplies credentials.
- Generated preview images are post-processed into annotated previews, sliced components, thumbnails, and a 996-ready manifest.
- Frontend `/providers` manages provider config and health checks.
- Frontend `/job-center` can create and run provider-backed jobs.
- Frontend `/assets` supports thumbnail preview, download, path copy, and project/job/type/device filtering.

## 2026-06-04 Acceptance Architecture

The verified local acceptance path is:

`Project -> Job -> Mock Runner -> Asset`

Verified modules:

- Project CRUD creates and lists project records.
- Job Center creates and displays generation jobs.
- Mock UI Job Creation creates local mock generation jobs.
- Mock Job Runner moves jobs through the local execution flow.
- Mock Pipeline Complete Flow creates preview outputs without a real AI provider.
- Asset Record Creation persists generated asset records.
- Asset Binding To Generation Job links generated assets through `generation_job_id`.

Current sprint status:

- Sprint 5: accepted
- Sprint 6: accepted
- Sprint 7A: complete
- Sprint 7B: complete

Next architecture priorities:

- P0: Real AI UI generation loop, `Prompt -> Provider -> Image -> Asset -> Preview`.
- P1: 996 package export, slicing, and manifest generation.
- P2: Provider security hardening, audit trail, concurrency control, and batch jobs.

## Sprint 7C Phase 1 Scope

Sprint 7C Phase 1 adds the real generation pipeline skeleton without connecting real model providers.

The new skeleton flow is:

`Prompt -> Provider -> RealJobRunner -> Asset -> Preview`

Key boundaries:

- `real_ui_generation` identifies future real UI generation jobs.
- Job Center creates `real_ui_generation` jobs from prompt, provider, project, device, width, and height fields.
- `RealJobRunner` currently renders one local placeholder PNG.
- The placeholder output creates one `ui_preview` asset.
- Placeholder assets use `source = real_pipeline_placeholder`.
- Generated placeholder assets are linked through `assets.generation_job_id`.
- Job logs and `output_json` record the placeholder execution result.

Out of scope for Phase 1:

- Real OpenAI calls
- OpenRouter calls
- ComfyUI calls
- ZIP export
- Production slicing
- Mock Pipeline changes

## Sprint 7C Phase 1.5 Scope

Sprint 7C Phase 1.5 validates the real UI generation workflow without connecting a real model.

The workflow is:

`Project -> Style Profile -> Base Panel -> Reference Image -> Prompt -> Real UI Job -> RealJobRunner -> Asset -> Preview`

Job Center now acts as the Generation Wizard:

- Step 1: choose project
- Step 2: choose style profile
- Step 3: choose base panel
- Step 4: choose optional reference image
- Step 5: enter prompt
- Step 6: create `real_ui_generation` job

The generated job stores the full workflow context in `generation_jobs.input_json`: `project_id`, `style_profile_id`, `base_panel_id`, `reference_image_id`, `prompt`, `device_type`, `width`, and `height`.

Traceability surfaces:

- Job Detail displays project, style, base panel, reference image, and prompt.
- Real placeholder assets store the same source context in `assets.metadata_json`.
- Assets displays Project, Style, Panel, and Prompt source information.

After Phase 1.5, the application has a complete UI generation workflow. The only missing piece is replacing the placeholder runner output with a real model provider.
