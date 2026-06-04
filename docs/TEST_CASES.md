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

## Sprint 5

1. Check `POST /generation_jobs/mock-ui` creates a `mock_ui_generation` job.
2. Check `POST /generation_jobs/{id}/run-mock` moves a valid mock job to `completed`.
3. Check invalid mock `input_json` moves a job to `failed`.
4. Check mock run creates `ui_preview`, `annotated_preview`, and `sliced_component` assets.
5. Check result assets use `source = mock_generated` and contain `generation_job_id`.
6. Check `GET /generation_jobs/{id}/results` returns generated assets.
7. Check `GET /assets?generation_job_id={id}` filters generated assets.
8. Check `GET /assets/{id}/file` streams preview files.
9. Check `/job-center` can create mock jobs, run mock, show logs, and show result assets.
10. Check `/assets` shows image previews, details, source, and job filtering.
11. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
12. Run `npm test -- --runInBand` in `frontend/`.
13. Run `npm run build` in `frontend/`.
14. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 6

1. Check provider CRUD can create and update `mock`, `openai`, and `custom` provider configs.
2. Check provider health returns `ok`, `disabled`, `configured`, or `missing_config`.
3. Check `POST /generation_jobs` accepts `provider_id`.
4. Check `POST /generation_jobs/{id}/run` executes the unified runner.
5. Check completed jobs include `output_preview_path` and `output_json`.
6. Check generated assets include `thumbnail_path`, `source`, and `generation_job_id`.
7. Check generated output writes `assets/uploads/996-ready/{job_id}`.
8. Check `/assets` filters by project, job_id, type, and device_type.
9. Check `/providers` can create providers, toggle enabled state, and call health check.
10. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
11. Run `npm test -- --runInBand` in `frontend/`.
12. Run `npm run build` in `frontend/`.
13. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 7A

1. Check mock provider health returns `healthy`.
2. Check OpenAI provider without `api_key_env` returns `unhealthy`.
3. Check OpenAI provider with missing local environment variable returns `unhealthy`.
4. Check direct `api_key` in `config_json` is rejected and not echoed.
5. Check `/providers` shows type, enabled state, health status, and key safety guidance.
6. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
7. Run `npm test -- --runInBand` in `frontend/`.
8. Run `npm run build` in `frontend/`.
9. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 7B

1. Check OpenAI runner reads the API key from `config_json.api_key_env`.
2. Check missing `api_key_env` fails the job without crashing.
3. Check missing local environment variable fails the job without exposing a key.
4. Check mocked OpenAI API failure fails the job with a concise error.
5. Check mocked OpenAI response without image data fails the job.
6. Check image save failure fails the job and appends logs.
7. Check mocked OpenAI success writes `ai_generated` assets with thumbnails and `generation_job_id`.
8. Check job `output_json` includes generated paths and asset ids.
9. Check mock provider runner tests still pass.
10. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
11. Run `npm test -- --runInBand` in `frontend/`.
12. Run `npm run build` in `frontend/`.
13. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.
14. Start the backend and check `GET /health`.

## Sprint 8A

1. Create or upload a `ui_preview` asset backed by a PNG file.
2. Call `POST /assets/{asset_id}/process-components`.
3. Check the response includes `manifest_path`, `annotation_path`, `preview_html_path`, and six `component_asset_ids`.
4. Check `manifest.json` contains the six `main_ui` template components.
5. Check `annotation.json` contains `component_id`, `component_type`, `x`, `y`, `width`, `height`, `font_family`, `font_size`, `font_color`, and `notes`.
6. Check `components/` includes six PNG slices.
7. Check generated slices are saved as `sliced_component` assets with `source = component_processing`.
8. Check generated slices inherit the source UI preview `generation_job_id`.
9. Check Assets detail can trigger component processing and display manifest, annotation, component count, and `preview.html`.
10. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
11. Run `npm test -- --runInBand` in `frontend/`.
12. Run `npm run build` in `frontend/`.
13. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 8A.1

1. Check main frontend navigation shows 项目管理, 风格管理, 基础面板, 素材管理, 任务中心, and 提供商管理.
2. Check Job Center shows 创建模拟UI任务, 创建真实UI任务, 运行模拟生成, 结果素材, and Chinese wizard steps.
3. Check Assets detail shows 素材详情 and 生成组件切图与标注.
4. Process a `ui_preview` asset and check `manifest.json` includes Chinese component names, including 主功能栏.
5. Check `annotation.json` includes Chinese fields: `组件名称`, `组件类型`, `X坐标`, `Y坐标`, `宽度`, `高度`, `字体`, `字号`, `字体颜色`, and `说明`.
6. Check `preview.html` contains Chinese component names and Chinese annotation notes.
7. Confirm English internal fields such as `component_id`, `component_type`, `x`, `y`, `width`, and `height` remain available.
8. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
9. Run `npm test -- --runInBand` in `frontend/`.
10. Run `npm run build` in `frontend/`.
11. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 8B

1. Create an OpenAI provider with `config_json = {"api_key_env":"OPENAI_API_KEY"}`.
2. Create a `real_ui_generation` job with `provider_id` set to that OpenAI provider.
3. In automated tests, mock the OpenAI image response; do not call the external network.
4. Run `POST /generation_jobs/{id}/run`.
5. Check the job completes and logs `OpenAI run completed`.
6. Check an `ai_generated` `ui_preview` asset exists for the job.
7. Check six `component_processing` `sliced_component` assets exist for the job.
8. Check `output_json.component_processing` contains `manifest_path`, `annotation_path`, `preview_html_path`, and `component_asset_ids`.
9. Check `manifest.json` contains Chinese component names.
10. Check `annotation.json` contains Chinese annotation fields.
11. Check `preview.html` contains Chinese component names.
12. Check no API key value is returned in job payloads or logs.
13. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
14. Run `npm test -- --runInBand` in `frontend/`.
15. Run `npm run build` in `frontend/`.
16. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 8C

1. Create an Ofox provider with `type = ofox`.
2. Use the default setup script so users do not hand-write JSON.
3. Default config is `{"api_key_env":"OFOX_API_KEY","base_url":"https://api.ofox.ai/v1","model":"gpt-image-2"}`.
4. Check health returns `healthy` when the named local environment variable exists.
5. Check health and job payloads do not expose the real API key.
6. Create a `real_ui_generation` job with `provider_id` set to the Ofox provider.
7. In automated tests, mock the OpenAI Compatible response; do not call the external network.
8. Check the runner calls `{base_url}/images/generations`.
9. Check the request includes the configured model and prompt.
10. Check the generated UI image is saved as an `ai_generated` `ui_preview` asset.
11. Check six `component_processing` `sliced_component` assets are created.
12. Check `manifest.json` contains Chinese component names.
13. Check `annotation.json` contains Chinese annotation fields.
14. Check `preview.html` contains Chinese component names.
15. Check Assets can show generated and sliced result assets.
16. Run `backend\.venv\Scripts\python -m pytest backend\tests -q`.
17. Run `npm test -- --runInBand` in `frontend/`.
18. Run `npm run build` in `frontend/`.
19. Run `backend\.venv\Scripts\python -m alembic -c backend\alembic.ini upgrade head`.

## Sprint 8C Local Real Acceptance

1. Set `OFOX_API_KEY` in the terminal that starts the backend.
2. Start the backend on `http://127.0.0.1:8000`.
3. Run `backend\.venv\Scripts\python scripts\setup_ofox_provider.py`.
4. Run `backend\.venv\Scripts\python scripts\verify_ofox_e2e.py`.
5. Current local result: the real request reaches Ofox, but Ofox returns `402`.
6. Treat `402` as a billing/quota limitation, not a local code failure.
7. After recharge, rerun the script and check it reports `ui_preview`, `manifest`, `annotation`, `preview_html`, and `component_count`.
8. If `gpt-image-2` is unsupported, rerun both scripts with `--model`.
