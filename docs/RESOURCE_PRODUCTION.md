# Resource Production

## Scope

Resource Production makes generated packages more useful for follow-up 996 asset work.

This stage does not add style extraction, OCR, YOLO, SAM, cloud deployment, ZIP export, user systems, or database schema changes.

## asset_mode

Generation input now supports `asset_mode`.

Supported values:

- `ui_package`
- `resource_production`

Default:

```text
ui_package
```

`ui_package` keeps the existing behavior: generate a complete UI preview, annotation, component slices, candidate detection, and 996-ready package.

`resource_production` keeps the same pipeline but changes production intent:

- prefer reusable 996 resources
- keep buttons, icons, frames, inputs, tabs, and slots visually separable
- preserve clean boundaries for slicing and manual review
- record transparent-resource metadata for follow-up production
- keep full UI package compatibility

## Resource Classification

Generated `manifest.json` and `annotation.json` can include:

- `asset_mode`
- `resource_category`
- `production_usage`
- `transparent_policy`
- `resource_summary`

Current categories:

| Category | Use |
| --- | --- |
| `layout_bar` | Bottom bar or layout strip |
| `panel_region` | Panel or full rectangular UI region |
| `button_asset` | Button-like reusable asset |
| `icon_asset` | Icon-like reusable asset |
| `frame_asset` | Border/frame candidate |
| `input_asset` | Input box candidate |
| `slot_asset` | Inventory or skill slot candidate |
| `tab_asset` | Tab candidate |
| `background_asset` | Full background or panel background |
| `unknown_asset` | Needs manual review |

## Transparent Resource System

`transparent_policy` records the production expectation:

```json
{
  "required_component_types": ["button", "icon", "frame", "input"],
  "allowed_flat_component_types": ["panel", "background", "bar"],
  "verification": "metadata_only"
}
```

Important boundary:

- This stage records transparent requirements.
- It does not automatically generate transparent PNGs.
- `transparent.verified` still means metadata verification, not final art approval.

## Output Contract

`resource_production` output remains compatible with the existing 996-ready package:

```text
996-ready/
  ui_preview.png
  manifest.json
  annotation.json
  preview.html
  candidate_manifest.json
  candidate_preview.html
  component_quality_report.json
  component_quality_report.html
  components/
  candidates/
```

New fields are backward-compatible. Older packages without `asset_mode` remain valid.

## Component Quality Report

Sprint 15A adds a quality report to help decide whether the current package is useful enough for 996 follow-up production.

Generated files:

- `component_quality_report.json`
- `component_quality_report.html`

The report combines:

- template components from `manifest.json`
- candidate components from `candidate_manifest.json`

It tracks:

- total component count
- counts for `button`, `icon`, `frame`, `tab`, `slot`, `input`, `panel`, and `background`
- raw area by category
- covered area
- uncovered area
- suspected missing regions based on coarse low-coverage grid cells

Current limitation:

- The report is coverage analysis, not semantic AI recognition.
- It does not use OCR, YOLO, SAM, or model training.
- Suspected missing regions are review hints for humans, not final labels.

## Simple Operation UI

The Job Center adds one compact selector:

```text
Asset mode
  UI package
  Resource production
```

Design intent:

- keep the current generation form
- add only one production-mode choice
- show a one-line explanation of the selected mode
- avoid a new admin backend or complex production console

The default UI choice is `resource_production` for real generation, because this stage focuses on assets that can continue into 996 production.

## Validation

`scripts/validate_996_export.py` validates optional Resource Production fields when present:

- `asset_mode`
- `resource_category`
- `production_usage`
- `transparent_policy`
- `component_quality_report.json`

Legacy packages remain valid because these fields are optional.
