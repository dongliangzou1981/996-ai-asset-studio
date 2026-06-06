# Production Loop Validation

## Current Branch

- Branch: `main`
- Git status before validation: clean against local working tree.
- Git status after P0 validation fixes:
  - `M backend/app/component_processing.py`
  - `M backend/app/job_runner.py`
  - `M scripts/generate_screen_with_style.py`
  - `A docs/production-loop-validation.md`

## Latest Commit

- Latest commit: `1992be0 sync local changes before cursor migration`

## Test Scene

- Entry point: `scripts/generate_screen_with_style.py`
- Style code: `STYLE_0005`
- Scene: `bag_ui`
- Device type: `mobile_landscape`
- Asset mode: `resource_production`
- Generation job id: `0525bddf18c04e4cb4a802d7d035e16f`
- Package path: `assets/uploads/996-ready/STYLE_0005/bag_ui/0525bddf18c04e4cb4a802d7d035e16f`

## Generated Outputs

- Full UI image: `ui_preview.png`
- Component slices:
  - `components/chat_panel.png`
  - `components/left_status_panel.png`
  - `components/main_bottom_bar.png`
  - `components/minimap_area.png`
  - `components/right_menu_panel.png`
  - `components/skill_area.png`
  - `components/sliced_component.png`
- Manifest: `manifest.json`
- Annotation: `annotation.json`
- Candidate manifest: `candidate_manifest.json`
- Delivery report: `delivery_report.json`
- Component quality report: `component_quality_report.json`

## Validation Result

- Existing validator command:
  - `backend/.venv/Scripts/python.exe scripts/validate_996_export.py assets/uploads/996-ready/STYLE_0005/bag_ui/0525bddf18c04e4cb4a802d7d035e16f`
- Validator result: `PASS`
- File existence:
  - `ui_preview.png`: exists
  - `manifest.json`: exists
  - `annotation.json`: exists
  - `components/`: exists
- JSON validity:
  - `manifest.json`: valid UTF-8 JSON
  - `annotation.json`: valid UTF-8 JSON
  - `delivery_report.json`: valid UTF-8 JSON
- Component counts:
  - Manifest components: `6`
  - Annotation components: `6`
- Path checks:
  - Manifest component files exist: yes
  - Annotation component image files exist: yes
- Scene metadata checks:
  - `manifest.template`: `bag_ui`
  - `annotation.template`: `bag_ui`
  - `delivery_report.screen_type`: `bag_ui`

## Blocking Issues

1. The first real `bag_ui` package was generated, but `manifest.template` and `annotation.template` were still hardcoded as `main_ui`.
   - Impact: downstream review could misidentify the test scene even though the package directory was under `bag_ui`.
2. The CLI completed generation and package validation, then failed while printing the result JSON on Windows CP950 because the JSON included Chinese text.
   - Impact: automation saw exit code `1` even though the output package had already been created.

## Fixes Applied

1. `backend/app/job_runner.py`
   - Propagates the requested `screen_type` from generation input into the preview asset metadata and job output manifest.
2. `backend/app/component_processing.py`
   - Reads `screen_type` from preview asset metadata.
   - Defaults to `main_ui` for old assets without metadata.
   - Writes the resolved scene into `manifest.template`, `annotation.template`, candidate manifest template, and component asset metadata.
3. `scripts/generate_screen_with_style.py`
   - Prints CLI result JSON with `ensure_ascii=True` to avoid Windows console encoding failures.

## Remaining Risks

- Component slicing is still based on the existing fixed region rules. This validates the production loop, not scene-specific bag inventory segmentation quality.
- The generated `bag_ui` package has correct scene metadata, but the component names and regions still follow the current template-level component processing rules.
- Transparent resource validation is metadata-based; it does not yet prove production-grade transparent PNG quality.
- Candidate detection is heuristic and should remain under manual review before production use.
