# Sprint20 Production Pass Implementation

## Summary

Sprint20 adds a file-based production review loop for generated `996-ready` packages:

```text
996-ready package
-> production analysis
-> transparent PNG checks
-> manual acceptance JSON
-> Studio result center display
```

The implementation does not add AI capability, does not write the database, and only reads or writes review files inside the package directory.

## Added Files

- `scripts/analyze_production_package.py`
- `tests/test_analyze_production_package.py`
- `backend/tests/test_production_review_api.py`
- `frontend/src/features/studio/ProductionReviewCard.test.tsx`
- `docs/SPRINT20_IMPLEMENTATION.md`
- `docs/SPRINT20_PROGRESS.md`

## Modified Files

- `backend/app/main.py`
- `backend/app/production_studio.py`
- `backend/app/schemas.py`
- `backend/tests/test_production_studio_api.py`
- `frontend/src/lib/api.ts`
- `frontend/src/features/studio/ProductionStudio.tsx`
- `frontend/src/features/studio/ProductionStudio.test.tsx`

## Analyzer

Command:

```text
python scripts/analyze_production_package.py <996-ready-package-path>
```

Required input files:

- `manifest.json`
- `annotation.json`

Optional input files:

- `candidate_manifest.json`
- `component_quality_report.json`
- `delivery_report.json`

Generated output files:

- `component_review_analysis.json`
- `production_review.json`
- `manual_acceptance.json`
- `production_review.html`

## Classification

Production levels:

- A: `button`, `icon`, `input`, `tab`, `skill_icon`, `equipment_slot`, `close_button`, `currency_icon`
- B: `panel`, `chat`, `map`, `skill_bar`, `hud_bar`, `activity_panel`, `inventory_panel`, `role_panel`, `shop_panel`
- C: `text`, `number`, `red_dot`, `dynamic_content`, `effect`, `decoration`, `unknown`

Production categories:

- `Screen`
- `Panel`
- `Atomic`
- `Effect`
- `Ignore`

## Transparent PNG Checks

The analyzer checks:

- `file_exists`
- `is_png`
- `image_mode`
- `has_alpha_channel`
- `has_transparent_pixels`
- `is_fully_transparent`
- `is_fully_opaque`
- `required_transparency`

A-level components default to `required_transparency=true`.

A-level components add blockers when:

- file is missing
- file is not PNG
- file has no alpha channel
- file is fully opaque

The analyzer does not modify image files.

## production_review.json Example

```json
{
  "schema_version": "1.0",
  "production_score": 70,
  "production_ready": false,
  "components_count": 6,
  "candidates_count": 3,
  "level_a_count": 2,
  "level_b_count": 3,
  "level_c_count": 4,
  "screen_count": 1,
  "panel_count": 3,
  "atomic_count": 2,
  "effect_count": 1,
  "ignore_count": 2,
  "transparent_issues": 1,
  "blockers": ["primary_action_button: required transparent PNG is fully opaque"],
  "warnings": ["Optional package file missing: delivery_report.json"],
  "missing_files": [],
  "generated_at": "2026-06-07T00:00:00Z"
}
```

## manual_acceptance.json Example

```json
{
  "schema_version": "1.0",
  "review_status": "pending",
  "reviewer": "",
  "remarks": "",
  "updated_at": "2026-06-07T00:00:00Z",
  "accepted_at": null,
  "accepted_by": "",
  "components": [
    {
      "component_id": "primary_action_button",
      "level": "A",
      "production_category": "Atomic",
      "review_status": "pending",
      "remarks": ""
    }
  ]
}
```

Supported top-level statuses:

- `pending`
- `accepted`
- `rejected`

## API

All APIs resolve package paths under the configured upload root and do not write the database.

```text
POST /production-studio/analyze?package_dir=<path>
GET  /production-studio/production-review?package_dir=<path>
GET  /production-studio/component-review?package_dir=<path>
GET  /production-studio/manual-acceptance?package_dir=<path>
PUT  /production-studio/manual-acceptance?package_dir=<path>
```

`GET /production-studio/manual-acceptance` returns a pending default structure when `manual_acceptance.json` does not exist.

`PUT /production-studio/manual-acceptance` writes only `manual_acceptance.json` inside the package directory.

## Studio Acceptance Steps

1. Open `/studio`.
2. Generate or reuse a style and screen package.
3. In the result center, inspect the Production Review Card.
4. Open `production_review.json`, `component_review_analysis.json`, `manual_acceptance.json`, or `production_review.html` from the card links.
5. Change manual acceptance status to `pending`, `accepted`, or `rejected`.
6. Confirm `manual_acceptance.json` inside the package directory reflects the selected status.

## Test Results

Verified commands:

```text
backend/.venv/Scripts/python.exe -m pytest -q
npm test -- --runInBand
npm run build
```

Results:

- Backend pytest: `84 passed`
- Frontend Jest: `12 passed`
- Frontend build: passed

## Remaining Issues

- Component slicing still uses existing fixed regions. Sprint20 analysis classifies and reviews output; it does not improve segmentation.
- Transparent checks verify PNG metadata and alpha pixels, but do not judge art quality.
- Candidate detection remains heuristic and should be manually reviewed.
- Manual acceptance is file-based only and not searchable in the database.

## Sprint21 Suggestions

- Add per-component manual review editing in Studio.
- Add a package-level review history instead of overwriting `manual_acceptance.json`.
- Add scene-specific component rules for `bag_ui`, `role_ui`, `shop_ui`, and `activity_ui`.
- Add optional export packaging once review files are complete.
