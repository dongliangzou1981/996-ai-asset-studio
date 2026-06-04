# Changelog

## Sprint 8C Local Ofox Acceptance - 2026-06-04

- Added `scripts/setup_ofox_provider.py` to create or update a default Ofox Provider without storing secrets.
- Added `scripts/verify_ofox_e2e.py` to run local real Ofox E2E acceptance.
- Defaulted Ofox local config to `https://api.ofox.ai/v1` and `gpt-image-2`.
- Documented that users only need to provide `OFOX_API_KEY` locally.
- Added `docs/OFOX_E2E.md` with setup, run, output, and failure-check guidance.

## Sprint 8C - 2026-06-04

- Added `ofox` provider type.
- Added Ofox OpenAI Compatible image runner.
- Allowed Ofox config fields `api_key_env`, `base_url`, and `model` without storing real API keys.
- Added Ofox health checks using local environment variables.
- Added Ofox to the frontend provider type selector.
- Connected Ofox generation output to Assets and automatic component processing.
- Added mocked Ofox tests for UI generation, component slicing, Chinese annotation, manifest, and preview output.

## Sprint 8B - 2026-06-04

- Routed `real_ui_generation` jobs with OpenAI providers to the real OpenAI runner.
- Connected successful OpenAI image generation to the Sprint 8A Component Processing Service.
- Saved OpenAI output images as `ai_generated` `ui_preview` assets.
- Generated six `component_processing` sliced component assets after OpenAI image creation.
- Added component processing paths and component asset ids to generation job `output_json`.
- Added mocked OpenAI tests for `Prompt -> OpenAI -> Assets -> component detection -> annotation -> slicing`.

## Sprint 8A.1 - 2026-06-04

- Added Chinese-first wording across the main navigation, Assets, Job Center, and Providers surfaces.
- Added Chinese component names for the six Sprint 8A template regions while preserving English internal IDs.
- Added Chinese-first fields to `annotation.json`, including component name, component type, coordinates, dimensions, font, font size, font color, and notes.
- Added Chinese component names and Chinese descriptions to `manifest.json`.
- Updated `preview.html` to display Chinese component names and annotation notes.
- Documented the Chinese-first principle: pages, exports, and annotations default to Chinese; code internals and API fields may remain English.

## Sprint 8A - 2026-06-04

- Added template-based Component Processing Service for `ui_preview` assets.
- Added `POST /assets/{asset_id}/process-components`.
- Generated six `main_ui` component regions, component PNGs, `manifest.json`, `annotation.json`, and `preview.html`.
- Stored generated slices as `sliced_component` assets with `source = component_processing`.
- Added Assets detail action to trigger component slicing and annotation generation.
- Documented Sprint 8A as template-based component recognition, not intelligent visual recognition.

## Sprint 8 Planning - 2026-06-04

- Added the V1 final target: `Prompt -> UI Generation -> Component Detection -> Annotation -> Transparent PNG Slice -> 996 Export Package`.
- Defined the target `996-ready/` export structure with `ui_preview.png`, `components/`, `manifest.json`, `annotation.json`, and `preview.html`.
- Documented required `annotation.json` fields: component type, x, y, width, height, font family, font size, and font color.
- Reordered development priorities to P0 real AI generation, P1 component detection, P2 annotation system, P3 transparent PNG slicing, and P4 996 export.
- Confirmed Sprint 8 planning is documentation-only.

## 0.7C-phase2.0 - 2026-06-04

- Added `openrouter` provider type while keeping OpenAI provider support.
- Added OpenRouter `api_key_env` configuration and health check handling without storing real keys.
- Added `OpenRouterRunner` placeholder runner behind the existing `Provider -> Runner -> Asset` abstraction.
- Added `openrouter` to the provider type selector.
- Documented the multi-provider route: OpenAI, OpenRouter, and planned ComfyUI.
- Kept external OpenRouter calls out of this phase.

## 0.7C-phase1.5 - 2026-06-04

- Added Generation Wizard steps in Job Center for project, style profile, base panel, optional reference image, prompt, and real UI job creation.
- Saved full workflow context in `real_ui_generation` job `input_json`.
- Added Job Detail traceability for project, style, base panel, reference image, and prompt.
- Added Asset source context display for Project, Style, Panel, and Prompt.
- Confirmed Phase 1.5 completes the UI generation workflow without connecting OpenAI, OpenRouter, or ComfyUI.

## 0.7C-phase1.0 - 2026-06-04

- Added `real_ui_generation` job creation support in Job Center.
- Added a `RealJobRunner` skeleton for `Prompt -> Provider -> RealJobRunner -> Asset -> Preview`.
- Added placeholder PNG generation for real pipeline jobs without connecting OpenAI, OpenRouter, or ComfyUI.
- Added `real_pipeline_placeholder` asset source for Phase 1 placeholder outputs.
- Added tests for real pipeline placeholder completion and existing mock pipeline coverage.
- Updated project status and architecture docs for Sprint 7C Phase 1 scope.

## 2026-06-04 Acceptance Update

- Verified Project CRUD, Job Center, Mock UI Job Creation, Mock Job Runner, Mock Pipeline Complete Flow, Asset Record Creation, and Asset Binding To Generation Job.
- Confirmed the accepted flow: `Project -> Job -> Mock Runner -> Asset`.
- Marked Sprint 5 and Sprint 6 as accepted.
- Marked Sprint 7A and Sprint 7B as complete.
- Added development priorities for real AI UI generation, 996 package export, and provider security hardening.

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
