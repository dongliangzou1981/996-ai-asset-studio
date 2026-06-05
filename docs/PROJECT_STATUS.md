# Project Status

## 2026-06-04 Acceptance

Verified:

- Project CRUD
- Job Center
- Mock UI Job Creation
- Mock Job Runner
- Mock Pipeline Complete Flow
- Asset Record Creation
- Asset Binding To Generation Job

Accepted flow:

`Project -> Job -> Mock Runner -> Asset`

Sprint status:

- Sprint 5: accepted
- Sprint 6: accepted
- Sprint 7A: complete
- Sprint 7B: complete

Development priorities:

- P0: Real AI UI generation loop, `Prompt -> Provider -> Image -> Asset -> Preview`
- P1: 996 package export, slicing, manifest
- P2: Provider security hardening, audit, concurrency control, batch jobs

## Sprint 7C Phase 1

Status: complete

Scope:

- Establish Real Generation Pipeline skeleton.
- Add `real_ui_generation` job creation from Job Center.
- Add `RealJobRunner` placeholder execution.
- Create one placeholder `ui_preview` asset per completed real pipeline job.
- Link placeholder asset records to `generation_job_id`.
- Show completed jobs and result assets through existing Job Center and Assets flows.

Phase 1 does not connect OpenAI, OpenRouter, or ComfyUI. It does not add ZIP export or production slicing.

Current priority after Phase 1:

- P0: Connect a real model provider behind the existing pipeline boundary.
- P1: Add 996 package export, slicing, and manifest output.
- P2: Add provider security hardening, audit, concurrency control, and batch jobs.

## Sprint 7C Phase 1.5

Status: complete

Workflow status:

- Project selection: complete
- Style profile selection: complete
- Base panel selection: complete
- Optional reference image selection: complete
- Prompt capture: complete
- Real UI job creation: complete
- RealJobRunner placeholder execution: complete
- Asset creation and job binding: complete
- Job Detail traceability: complete
- Asset source traceability: complete

Closed workflow:

`Project -> Style Profile -> Base Panel -> Reference Image -> Prompt -> Real UI Job -> Asset -> Preview`

Conclusion:

The system now has the full UI generation workflow. The remaining work is real model provider integration.

## Sprint 7C Phase 2

Status: complete

Provider status:

- OpenAI: supported and preserved
- OpenRouter: provider type and runner skeleton added
- ComfyUI: planned

OpenRouter scope:

- Provider configuration uses only `api_key_env`
- Health check validates local environment variable presence
- Runner participates in the existing `Provider -> Runner -> Asset` structure
- No external OpenRouter request is made in this phase

Conclusion:

OpenRouter is now selectable and wired into the unified provider abstraction. The next step is a controlled real-model acceptance phase.

## Sprint 8 Planning

Status: planned

V1 final target:

`Prompt -> UI Generation -> Component Detection -> Annotation -> Transparent PNG Slice -> 996 Export Package`

Target export structure:

```text
996-ready/
  ui_preview.png
  components/
  manifest.json
  annotation.json
  preview.html
```

`annotation.json` requirements:

- component type
- x
- y
- width
- height
- font family
- font size
- font color

Priority order:

- P0: Real AI generation
- P1: Component detection
- P2: Annotation system
- P3: Transparent PNG slicing
- P4: 996 export

Sprint 8 can begin with P0 real AI generation while keeping the later detection, annotation, slicing, and export stages behind stable pipeline boundaries.

## Sprint 8A

Status: complete

Automatic acceptance: passed

Scope:

- Template-based component processing is available for `ui_preview` assets.
- `main_ui` currently generates six fixed proportional regions.
- The backend writes `manifest.json`, `annotation.json`, component PNGs, and `preview.html`.
- Component PNGs are recorded as `sliced_component` assets.
- Component assets use `source = component_processing`.
- Component assets inherit the source UI preview `generation_job_id`.
- Assets detail can trigger processing and display manifest, annotation, component count, and preview link.

Auto verification:

- Project `Sprint8-Auto-Verify` was created or reused.
- A `ui_preview` verification asset was created or reused.
- `POST /assets/{asset_id}/process-components` generated the full output chain.
- Generated output includes `components/`, at least six PNG slices, `manifest.json`, `annotation.json`, and `preview.html`.
- `manifest.json` includes Chinese component names.
- `annotation.json` includes Chinese fields for component name, component type, coordinates, size, font, font size, and font color.
- `preview.html` includes Chinese component names.
- Conclusion: Sprint 8A has passed automatic acceptance.

Limitations:

- This is not intelligent visual recognition.
- Transparent background optimization is not implemented yet.
- The existing Mock Pipeline and Real Pipeline remain intact.

## Sprint 8A.1

Status: complete

Chinese-first principle:

- Pages default to Chinese user-facing copy.
- Exported results default to Chinese text.
- Annotation content defaults to Chinese.
- Internal code identifiers may remain English.
- API field names may remain English.

Implemented:

- Main navigation and key task/material/provider surfaces use Chinese labels.
- Component display names are Chinese while internal `component_id` values remain English.
- `annotation.json` now includes Chinese fields for component name, component type, coordinates, size, font, font size, font color, and notes.
- `manifest.json` now includes Chinese component names and Chinese descriptions.
- `preview.html` now shows Chinese component names and Chinese annotation notes.

Remaining:

- Some lower-level CRUD form fields still expose technical identifiers where the backend contract expects them.
- Intelligent component detection and transparent background optimization remain future work.

## Sprint 8B

Status: complete

Implemented:

- `real_ui_generation` with an OpenAI provider now uses `OpenAIJobRunner`.
- Prompt-driven OpenAI image output is saved as an `ai_generated` `ui_preview` asset.
- The OpenAI `ui_preview` asset automatically runs through the Sprint 8A Component Processing Service.
- The pipeline now produces component PNGs, Chinese annotation fields, `manifest.json`, and `preview.html` after OpenAI image generation.
- `generation_jobs.output_json` records component processing paths and component asset ids.

Verified:

- Automated tests mock OpenAI and verify the end-to-end flow without external network access.
- Generated component assets use `source = component_processing`.
- Component assets inherit the OpenAI generation job id.
- Chinese component names and annotation fields remain present.

Remaining:

- Manual real-key acceptance with local `OPENAI_API_KEY`.
- Template detection still needs intelligent visual recognition.
- Transparent PNG slicing is not optimized yet.

## Sprint 8C

Status: complete

Implemented:

- Ofox is available as provider type `ofox`.
- Ofox can be configured in the Providers page.
- Ofox uses an OpenAI Compatible image generation endpoint.
- Ofox config supports `api_key_env`, `base_url`, and `model`.
- Default local Ofox config uses `base_url = https://api.ofox.ai/v1` and `model = gpt-image-2`.
- Ofox API keys remain local environment variables and are not stored in the database.
- Successful Ofox generation writes an `ai_generated` `ui_preview` asset.
- Successful Ofox generation automatically runs component processing.
- Component processing generates PNG slices, Chinese annotations, `manifest.json`, and `preview.html`.
- Results appear in Assets through existing job result and asset listing APIs.
- `scripts/setup_ofox_provider.py` creates or updates the default non-secret Ofox Provider config.
- `scripts/verify_ofox_e2e.py` runs local real Ofox acceptance and verifies `ui_preview`, sliced components, `annotation.json`, `manifest.json`, and `preview.html`.

Verified:

- Automated tests mock Ofox's OpenAI Compatible response.
- Health checks validate `OFOX_API_KEY` presence without exposing the key.
- The Ofox path creates six `component_processing` sliced component assets.
- Local real E2E reached the external Ofox Images API with `OFOX_API_KEY` loaded by the backend.
- Real image generation is blocked by Ofox API `402` billing/quota response and should be re-verified after recharge.

Remaining:

- Real image generation after Ofox billing/quota is available.
- If `gpt-image-2` is unsupported by the local Ofox account, rerun the scripts with a supported image model.
- Template detection still needs intelligent visual recognition.
- Transparent PNG slicing is not optimized yet.

## Sprint 10A

Status: complete

Scope:

- Solidify 996-ready Schema V1 for local package validation.
- Define `manifest.json` required fields, types, path rules, component types, and resource groups.
- Define `annotation.json` required fields, style metadata, image metadata, recognition metadata, review status, and notes.
- Upgrade `scripts/validate_996_export.py` to validate Schema V1.
- Upgrade `tests/fixtures/996_ready_demo/` to fully conform to Schema V1.
- Add Schema V1 regression coverage in `tests/test_996_ready_schema.py`.

Out of scope:

- Database changes
- Business pipeline changes
- Component recognition AI upgrades
- YOLO, OCR, or SAM
- Automatic transparent PNG generation
- ZIP export
- Cloud deployment

Verification:

- Schema V1 fixture validates successfully.
- Missing required fields fail validation.
- Invalid field types fail validation.
- Unsafe paths fail validation.
- Unknown component types fail validation.

Conclusion:

Sprint 10A establishes the first strict 996-ready package contract without touching the Sprint 8C generation and component processing chain.

## Sprint 10B

Status: complete

Scope:

- Define transparent asset metadata in `docs/TRANSPARENT_ASSET_SCHEMA.md`.
- Extend Schema V1 with optional `transparent` fields in `manifest.json` and `annotation.json`.
- Preserve backward compatibility for packages without `transparent`.
- Upgrade `scripts/validate_996_export.py` to validate transparent field legality.
- Upgrade `tests/fixtures/996_ready_demo/` with transparent button and icon examples.
- Add transparent asset regression coverage in `tests/test_transparent_asset_schema.py`.

Rules:

- `button`, `icon`, `frame`, and `input` require transparency when `transparent` metadata is present.
- `panel` and `background` may remain non-transparent.

Out of scope:

- Database changes
- Business pipeline changes
- Component recognition upgrades
- OCR, YOLO, or SAM
- Automatic transparent PNG generation
- ZIP export
- Cloud deployment

## Resource Production

Status: complete

Scope:

- Add `asset_mode` support with `ui_package` and `resource_production`.
- Keep `ui_package` compatible with the existing 996-ready output chain.
- Add Resource Production metadata to `manifest.json`, `annotation.json`, and `candidate_manifest.json`.
- Add resource categories and production usage hints for 996 follow-up work.
- Add package-level transparent policy metadata without generating transparent PNGs automatically.
- Add a compact Job Center `Asset mode` selector for real UI generation.
- Document the Resource Production contract in `docs/RESOURCE_PRODUCTION.md`.

Out of scope:

- Style extraction
- OCR
- YOLO
- SAM
- Cloud deployment
- ZIP export
- Database schema changes

Verification:

- Resource Production package metadata is covered by `tests/test_resource_production.py`.
- Validator remains backward-compatible with older packages.

## Sprint 15A

Status: complete

Scope:

- Add `component_quality_report.json`.
- Add `component_quality_report.html`.
- Report combined template component and candidate component statistics.
- Track counts for `button`, `icon`, `frame`, `tab`, `slot`, `input`, `panel`, and `background`.
- Calculate total component count, category area, covered area, and uncovered area.
- Add coarse suspected missing regions for manual review.
- Validate quality report structure when present.

Out of scope:

- Database changes
- ZIP export
- Cloud deployment
- OCR
- YOLO
- SAM
- Model training

Verification:

- `tests/test_candidate_detection.py` covers quality report generation and validator compatibility.
- Existing packages without quality reports remain valid.

## Sprint 16

Status: complete

Scope:

- Produce the first usable 996 UI package set.
- Use `STYLE_CODE = STYLE_0003`.
- Generate `main_ui`, `role_ui`, `bag_ui`, `shop_ui`, and `activity_ui`.
- Keep `device_type = mobile_landscape`.
- Keep `asset_mode = resource_production`.
- Output `1536x864` previews.
- Include `components/`, `candidates/`, delivery reports, candidate previews, and component quality reports for every screen.
- Add `docs/FIRST_USABLE_996_UI_PACKAGE_REPORT.md`.

Verification:

- Every Sprint 16 package passed `scripts/validate_996_export.py`.
- Python pytest passed with 66 tests.

Limit:

- Named `common_icons` still need manual handling or later rule improvements.

## Sprint 17

Status: complete

Scope:

- Add a simple `/studio` Production Studio page.
- Add web fields for `device_type`, `asset_mode`, style source, `STYLE_CODE`, screen types, style name, and prompt.
- Add backend endpoints for listing `STYLE_CODE` folders and generating production packages.
- Reuse the existing master style and style-guided generation scripts.
- Show `ui_preview`, 996-ready path, component counts, candidate counts, validator status, and report links.
- Explicitly show when semantic common icons are still missing.
- Add `docs/PRODUCTION_STUDIO_UI.md`.

Out of scope:

- ZIP export
- Cloud deployment
- User systems
- Commercial admin backend
- Database schema changes
- OCR, YOLO, SAM, or model training

Verification:

- Backend Production Studio API tests cover new style and existing `STYLE_CODE` flows.
- Frontend Studio tests cover form defaults, style selection, screen type selection, and result display.
