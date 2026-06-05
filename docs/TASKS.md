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

## Sprint 7C Phase 2

- [x] Add `openrouter` provider type
- [x] Keep OpenAI provider support
- [x] Keep provider config limited to `api_key_env`
- [x] Add OpenRouter health checks without exposing real keys
- [x] Add `OpenRouterRunner` placeholder runner
- [x] Preserve `Provider -> Runner -> Asset` abstraction
- [x] Expose `openrouter` in the provider type selector
- [x] Avoid real external OpenRouter calls
- [x] Update multi-provider roadmap
- [ ] Real OpenRouter model acceptance test
- [ ] ComfyUI provider implementation

Multi-provider route:

- OpenAI: supported provider
- OpenRouter: provider and runner skeleton added
- ComfyUI: planned

## Sprint 8 Planning

V1 final target:

`Prompt -> UI Generation -> Component Detection -> Annotation -> Transparent PNG Slice -> 996 Export Package`

996-ready export structure:

```text
996-ready/
  ui_preview.png
  components/
  manifest.json
  annotation.json
  preview.html
```

`annotation.json` must support:

- component type
- x
- y
- width
- height
- font family
- font size
- font color

Development priorities:

- [ ] P0: Real AI generation
- [ ] P1: Component detection
- [ ] P2: Annotation system
- [ ] P3: Transparent PNG slicing
- [ ] P4: 996 export

## Sprint 8A

- [x] Add Component Processing Service
- [x] Process `ui_preview` assets
- [x] Add template-based `main_ui` component regions
- [x] Generate six component records
- [x] Generate `manifest.json`
- [x] Generate `annotation.json`
- [x] Generate `preview.html`
- [x] Crop component PNGs from source UI preview
- [x] Write `sliced_component` asset records
- [x] Set component source to `component_processing`
- [x] Inherit `generation_job_id` from source UI preview
- [x] Add `POST /assets/{asset_id}/process-components`
- [x] Add Assets page action for component slicing and annotation
- [x] Document that Sprint 8A is template-based, not intelligent visual recognition
- [ ] Intelligent component detection
- [ ] Transparent background optimization

## Sprint 8A.1

- [x] Apply Chinese-first wording to the main frontend navigation and task/material/provider surfaces
- [x] Keep API fields, code identifiers, and internal component IDs in English where required for compatibility
- [x] Add Chinese component display names:
  - `main_bottom_bar` -> 主功能栏
  - `left_status_panel` -> 左侧状态栏
  - `right_menu_panel` -> 右侧菜单栏
  - `minimap_area` -> 小地图区域
  - `chat_panel` -> 聊天区域
  - `skill_area` -> 技能区域
- [x] Add Chinese-first fields to `annotation.json`
- [x] Add Chinese component names and descriptions to `manifest.json`
- [x] Render Chinese component names and annotation notes in `preview.html`
- [x] Update tests for Chinese annotation fields, manifest names, preview HTML, and primary frontend buttons

Chinese-first principle:

- Pages default to Chinese.
- Exported result text defaults to Chinese.
- Annotation content defaults to Chinese.
- Internal code identifiers may remain English.
- API field names may remain English.

## Sprint 8B

- [x] Route `real_ui_generation` jobs with an OpenAI provider to `OpenAIJobRunner`
- [x] Keep OpenAI API keys sourced only from `config_json.api_key_env`
- [x] Save the real OpenAI output image as an `ai_generated` `ui_preview` asset
- [x] Automatically run Component Processing after the OpenAI `ui_preview` asset is created
- [x] Generate six `component_processing` `sliced_component` assets from the OpenAI image
- [x] Write component `manifest.json`, `annotation.json`, and `preview.html`
- [x] Preserve Chinese annotation fields and Chinese component names
- [x] Include component processing paths in the generation job `output_json`
- [x] Cover the end-to-end OpenAI path with mocked API tests
- [ ] Manual real-key acceptance with local `OPENAI_API_KEY`
- [ ] Transparent PNG background optimization

## Sprint 8C

- [x] Add `ofox` provider type
- [x] Allow Ofox provider configuration through `config_json.api_key_env`
- [x] Allow OpenAI Compatible Ofox config fields: `base_url` and `model`
- [x] Keep real Ofox API keys out of the database and GitHub
- [x] Add Ofox health check using local environment variables
- [x] Add `OfoxJobRunner`
- [x] Call the OpenAI Compatible `/images/generations` endpoint
- [x] Save Ofox output as an `ai_generated` `ui_preview` asset
- [x] Automatically run component slicing after Ofox UI generation
- [x] Preserve Chinese `manifest.json`, `annotation.json`, and `preview.html`
- [x] Show Ofox as selectable provider in the frontend
- [x] Cover the Ofox path with mocked API tests
- [x] Add default local Ofox provider setup script
- [x] Add local real Ofox E2E verification script
- [x] Document that only `OFOX_API_KEY` is required locally
- [x] Confirm local real E2E reaches the external Ofox Images API with backend-loaded `OFOX_API_KEY`
- [ ] Re-verify real image generation after Ofox `402` billing/quota limit is resolved

## Sprint 10A

- [x] Add `docs/996_READY_SCHEMA_V1.md`
- [x] Define `manifest.json` Schema V1 required fields
- [x] Define `annotation.json` Schema V1 required fields
- [x] Define Schema V1 component types
- [x] Define Schema V1 resource groups
- [x] Define Schema V1 path rules
- [x] Upgrade `scripts/validate_996_export.py` with Schema V1 validation
- [x] Check required fields
- [x] Check field types
- [x] Check relative path safety
- [x] Check referenced file existence
- [x] Check component classification
- [x] Upgrade `tests/fixtures/996_ready_demo/` to conform to Schema V1
- [x] Add `tests/test_996_ready_schema.py`
- [x] Keep database schema unchanged
- [x] Keep business pipeline unchanged
- [x] Avoid component recognition AI upgrades, YOLO, OCR, SAM, transparent PNG generation, ZIP export, and cloud deployment

## Sprint 10B

- [x] Add `docs/TRANSPARENT_ASSET_SCHEMA.md`
- [x] Define required-transparent component types: `button`, `icon`, `frame`, `input`
- [x] Define non-transparent-allowed component types: `panel`, `background`
- [x] Extend Schema V1 with optional `transparent` fields in `manifest.json`
- [x] Extend Schema V1 with optional `transparent` fields in `annotation.json`
- [x] Keep `transparent` backward compatible
- [x] Upgrade `scripts/validate_996_export.py` with transparent field validation
- [x] Add transparent button and icon examples to `tests/fixtures/996_ready_demo/`
- [x] Add transparent asset regression tests
- [x] Keep database schema unchanged
- [x] Keep business pipeline unchanged
- [x] Avoid component recognition upgrades, OCR, YOLO, SAM, automatic transparent PNG generation, ZIP export, and cloud deployment

## Resource Production

- [x] Add `asset_mode` values: `ui_package` and `resource_production`
- [x] Keep `ui_package` as the backward-compatible package mode
- [x] Add `resource_production` prompt guidance for reusable 996 resources
- [x] Write `asset_mode` into job input, output JSON, delivery reports, and 996-ready metadata
- [x] Add resource categories for layout bars, panels, buttons, icons, frames, inputs, slots, and tabs
- [x] Add package-level transparent policy metadata
- [x] Keep transparent PNG generation as metadata-only, not automatic image processing
- [x] Add a compact Job Center `Asset mode` selector
- [x] Add `docs/RESOURCE_PRODUCTION.md`
- [x] Add Resource Production regression tests
- [x] Keep database schema unchanged
- [x] Avoid style extraction, OCR, YOLO, SAM, ZIP export, cloud deployment, and user systems

## Sprint 15A

- [x] Add `component_quality_report.json`
- [x] Add `component_quality_report.html`
- [x] Count `button`, `icon`, `frame`, `tab`, `slot`, `input`, `panel`, and `background`
- [x] Report total component count
- [x] Report category area
- [x] Report covered area and uncovered area
- [x] Report suspected missing regions
- [x] Validate quality report structure when present
- [x] Keep older packages without quality reports valid
- [x] Avoid database changes, ZIP export, cloud deployment, OCR, YOLO, SAM, and model training

## Sprint 16

- [x] Generate `main_ui`
- [x] Generate `role_ui`
- [x] Generate `bag_ui`
- [x] Generate `shop_ui`
- [x] Generate `activity_ui`
- [x] Use a single `STYLE_CODE`
- [x] Use `mobile_landscape`
- [x] Use `resource_production`
- [x] Verify every package with `validate_996_export.py`
- [x] Add `docs/FIRST_USABLE_996_UI_PACKAGE_REPORT.md`
- [x] Document that semantic small icons still need follow-up work

## Sprint 17

- [x] Add `/studio` Production Studio page
- [x] Add device type selection
- [x] Add output mode selection
- [x] Add style source selection
- [x] Add existing `STYLE_CODE` selection
- [x] Add screen type checkboxes
- [x] Add style name input
- [x] Add prompt input
- [x] Add `生成 UI 资源` action
- [x] Add backend endpoint to list local `STYLE_CODE` folders
- [x] Add backend endpoint to run the existing production generation chain
- [x] Show `ui_preview` thumbnails
- [x] Show 996-ready package paths
- [x] Show component and candidate counts
- [x] Show validator status
- [x] Link to delivery, candidate preview, and component quality reports
- [x] Show common icon semantic naming limitation
- [x] Add `docs/PRODUCTION_STUDIO_UI.md`
- [x] Add backend Production Studio tests
- [x] Add frontend Production Studio tests
- [x] Keep Job Center compatible
- [x] Avoid database changes, ZIP export, cloud deployment, user systems, OCR, YOLO, SAM, and model training

## Sprint 17B

- [x] Add `scripts/start_local_studio.ps1`
- [x] Check that the script is run from the project root
- [x] Check `backend\.venv\Scripts\python.exe`
- [x] Prompt for `OFOX_API_KEY` when missing without printing the key
- [x] Set `OFOX_API_KEY` only in the current PowerShell session
- [x] Start backend FastAPI on `127.0.0.1:8001`
- [x] Start frontend Studio on `127.0.0.1:3001`
- [x] Configure frontend API base as `http://127.0.0.1:8001`
- [x] Ensure the default Ofox provider without storing secrets
- [x] Add `scripts/check_studio_env.ps1`
- [x] Check `OFOX_API_KEY`
- [x] Check backend `8001`
- [x] Check frontend `3001`
- [x] Check `/production-studio/style-codes`
- [x] Check provider health
- [x] Improve `/studio` generation failure guidance
- [x] Add `docs/LOCAL_STUDIO_STARTUP.md`
- [x] Avoid `.env`, real key commits, cloud deployment, user systems, and database changes

## Sprint 18

- [x] Fully Chinese user-visible `/studio` labels
- [x] Replace device values with `手机横屏` and `电脑端`
- [x] Replace output mode labels with `资源生产` and `整图预览`
- [x] Replace style source labels with `新建风格` and `使用已有风格`
- [x] Replace screen labels with `主界面`, `角色界面`, `背包界面`, `商城界面`, and `活动界面`
- [x] Replace generation action with `开始生成`
- [x] Replace validation status with `验证通过` and `验证未通过`
- [x] Add `启动工作台.ps1`
- [x] Add `环境检查.ps1`
- [x] Add Chinese environment check statuses
- [x] Remove technical generation failure guidance from `/studio`
- [x] Add Result Center
- [x] Show screen name, generation time, style code, preview, resource entry, report entry, and validation status
- [x] Add manual acceptance status: `待验收`, `验收通过`, `需要修改`
- [x] Add manual acceptance notes
- [x] Document Sprint 18 productization
- [x] Keep compatibility: no database changes, cloud deployment, user system, ZIP, OCR, YOLO, SAM, or model training
