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
