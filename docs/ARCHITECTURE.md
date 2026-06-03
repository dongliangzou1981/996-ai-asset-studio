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
