# Changelog

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
