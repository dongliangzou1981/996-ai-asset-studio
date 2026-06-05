# First Usable 996 UI Package Report

## Scope

Sprint 16 produced one unified mobile landscape 996 legend UI package set for production validation.

This validation did not add ZIP export, cloud deployment, user systems, commercial admin features, database schema changes, OCR, YOLO, SAM, or model training.

## Production Settings

- `STYLE_CODE`: `STYLE_0003`
- `style_name`: `Sprint 16 Dark Gold Dragon Mobile`
- `device_type`: `mobile_landscape`
- `asset_mode`: `resource_production`
- Target resolution: `1536x864`
- Generation mode:
  - `main_ui`: `auto_generate`
  - Other screens: `style_inheritance`
- Visual direction: dark gold dragon legend game style

## Package Summary

| Screen | Generation Job ID | 996-ready Path | Validator | Manifest Components | Component Files | Candidates | Candidate Files |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `main_ui` | `14115d5fb8df4bfe91b9b2e504019167` | `assets/uploads/996-ready/STYLE_0003/main_ui/14115d5fb8df4bfe91b9b2e504019167` | PASS | 6 | 7 | 6 | 6 |
| `role_ui` | `d4b8e13ac79d42f5820b02899e6eefbd` | `assets/uploads/996-ready/STYLE_0003/role_ui/d4b8e13ac79d42f5820b02899e6eefbd` | PASS | 6 | 7 | 6 | 6 |
| `bag_ui` | `03cc14e509ad4a33a4ce5e3ddb726d7f` | `assets/uploads/996-ready/STYLE_0003/bag_ui/03cc14e509ad4a33a4ce5e3ddb726d7f` | PASS | 6 | 7 | 6 | 6 |
| `shop_ui` | `bd5b81c98d8a4e51b72ac8554b07fb2f` | `assets/uploads/996-ready/STYLE_0003/shop_ui/bd5b81c98d8a4e51b72ac8554b07fb2f` | PASS | 6 | 7 | 6 | 6 |
| `activity_ui` | `0f95bbdd82cb408d8b9afeb9ed8669aa` | `assets/uploads/996-ready/STYLE_0003/activity_ui/0f95bbdd82cb408d8b9afeb9ed8669aa` | PASS | 6 | 7 | 6 | 6 |

Every package contains:

- `ui_preview.png`
- `manifest.json`
- `annotation.json`
- `candidate_manifest.json`
- `candidate_preview.html`
- `delivery_report.json`
- `delivery_report.html`
- `component_quality_report.json`
- `component_quality_report.html`
- `components/`
- `candidates/`

All `ui_preview.png` files were verified at `1536x864`.

## Component Quality Summary

| Screen | Total Quality Components | Button | Icon | Frame | Tab | Slot | Input | Panel | Background | Covered Ratio | Suspected Missing Regions |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `main_ui` | 12 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 0 | 0.8365 | 0 |
| `role_ui` | 12 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 0 | 0.6261 | 3 |
| `bag_ui` | 12 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 0 | 0.8699 | 1 |
| `shop_ui` | 12 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 0 | 0.8859 | 0 |
| `activity_ui` | 12 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 0 | 0.8239 | 1 |

Current coverage is enough for a first production validation package, but not enough to claim production-grade full semantic slicing.

## Resources Already Usable For 996

- Full-screen `ui_preview.png` for all five screens.
- Template sliced `components/` for major layout regions.
- Candidate sliced `candidates/` for:
  - `button_candidate`
  - `icon_candidate`
  - `input_candidate`
  - `frame_candidate`
  - `tab_candidate`
  - `slot_candidate`
- `manifest.json` and `annotation.json` with Schema V1 fields, bounds, component types, and transparent metadata.
- `candidate_manifest.json` with candidate type, bounds, confidence, image path, transparent metadata, and review status.
- `candidate_preview.html` and `component_quality_report.html` for manual visual review.

## Resources Requiring Manual Processing

- Standalone named small icons are not yet guaranteed:
  - bag
  - role
  - skill
  - shop
  - activity
  - settings
  - close
  - back
  - confirm
  - cancel
- The current rule-based candidate detector outputs generic `icon_candidate` slices, not semantic named icon assets.
- Transparent PNG status is metadata-level only. Required transparent components are marked `unverified` until art review or alpha processing confirms them.
- Some component display names still need manual cleanup before direct handoff to artists or 996 client integration.
- `role_ui`, `bag_ui`, and `activity_ui` have suspected missing regions and should receive manual review before being treated as final production cuts.

## First Usable Package Assessment

This package set reaches the first production validation threshold:

- unified `STYLE_CODE`
- five mobile landscape screens
- consistent `resource_production` intent
- 1536x864 output
- real 996-ready package directories
- components and candidate slices present
- validator PASS for every screen
- component quality reports present

It should enter manual 996 technical review, not full v1.0 production acceptance.

## Known Issues

- Candidate detection still produces one generic candidate per type rather than dense semantic slicing.
- `background` count is currently `0` because full background extraction is not yet classified as a separate reusable background asset.
- Named small icon extraction is not yet implemented.
- Current transparent PNG support is policy metadata plus sliced RGBA files, not final verified transparent art.
- Quality coverage is uneven. `role_ui` has the weakest coverage at `0.6261`.

## Next Recommendations

1. Run manual review against `candidate_preview.html` for each screen.
2. Manually rename and approve the most useful candidates.
3. Add production review notes for missing named icons.
4. Improve component density in the next sprint while staying rule-based unless a later sprint explicitly approves AI recognition upgrades.
5. Keep this package as the first 996 technical handoff baseline.
