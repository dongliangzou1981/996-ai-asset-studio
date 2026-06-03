# Test Cases

## Sprint 1

1. Run `npm run build` in `frontend/`.
2. Start the backend with `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`.
3. Check `GET /health` returns `status: ok`.
4. Check `GET /schema/tables` returns the core database table list.

## Sprint 2

1. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
2. Run `npm test -- --runInBand` in `frontend/`.
3. Run `npm run build` in `frontend/`.
4. Check project CRUD endpoints.
5. Check style profile CRUD endpoints.
6. Check `/openapi.json` includes project and style profile schemas.

## Sprint 3

1. Check Base Panel CRUD endpoints.
2. Check `POST /base_panels/{id}/copy`.
3. Check `/panels` can create, list, edit, delete, and copy panels.
4. Check `/job-center` can list generation jobs.
5. Run Alembic `upgrade head` with migration 0002.

## Sprint 4

1. Check asset CRUD supports project assets and loose assets.
2. Check `POST /assets/upload` accepts `png`, `jpg`, `jpeg`, and `webp` extensions.
3. Check upload rejects unsupported extensions.
4. Check `/assets` can filter by project and asset type, upload files, and delete assets.
5. Check `POST /generation_jobs` creates a mock generation job.
6. Check `PATCH /generation_jobs/{id}` updates status, progress, logs, and errors.
7. Check `POST /generation_jobs/{id}/retry` resets failed jobs to `pending`, increments `retry_count`, and appends logs.
8. Check `/job-center` can create mock jobs, view details, display logs, and retry failed jobs.
9. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
10. Run `npm test -- --runInBand` in `frontend/`.
11. Run `npm run build` in `frontend/`.
12. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.
