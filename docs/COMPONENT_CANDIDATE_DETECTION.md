# Component Candidate Detection

## Scope

Sprint 11B adds a low-risk candidate slicing layer on top of the existing Component Processing flow.

This is not final intelligent component recognition. It is a rule and image-feature based pre-slicing step that finds likely component regions for later human review and 996 asset preparation.

It does not introduce:

- database schema changes
- user system changes
- ZIP export
- cloud deployment
- YOLO
- OCR
- SAM
- model training
- transparent PNG generation

## Compatibility

The existing Sprint 8C and Sprint 11A chain remains unchanged:

```text
ui_preview.png
components/
manifest.json
annotation.json
preview.html
```

`manifest.json` and `annotation.json` continue to follow `996_READY_SCHEMA_V1`.

`scripts/validate_996_export.py` still validates the legacy package contract and does not require candidate files. Candidate outputs are additive and can be ignored by older consumers.

## Existing Fallback Logic

The original fixed-region template slicing stays in `COMPONENT_RULES`.

It still produces:

- `main_bottom_bar`
- `left_status_panel`
- `right_menu_panel`
- `minimap_area`
- `chat_panel`
- `skill_area`

These slices remain the fallback baseline for current 996-ready packages.

## Candidate Detection Logic

The new candidate layer first scans the preview image for high-contrast edge regions, groups connected edge pixels into bounding boxes, and then classifies those boxes by shape and position.

If a supported candidate type is not found from image features, the detector falls back to a proportional region rule for that type so the package still contains a reviewable baseline.

The current confidence score is based on local luminance contrast inside the candidate crop. It is only a review hint, not a recognition guarantee.

Current candidate types:

| Candidate Type | Purpose |
| --- | --- |
| `button_candidate` | Likely clickable button region |
| `icon_candidate` | Likely square icon region |
| `input_candidate` | Likely text input or chat input region |
| `frame_candidate` | Likely frame, panel, or large bordered container |
| `tab_candidate` | Likely tab header region |
| `slot_candidate` | Likely inventory or backpack grid slot |

## Output Layout

Candidate files are written next to the existing 996-ready package:

```text
996-ready/{job_id}/
  ui_preview.png
  components/
  candidates/
    button_candidate_01.png
    icon_candidate_01.png
    input_candidate_01.png
    frame_candidate_01.png
    tab_candidate_01.png
    slot_candidate_01.png
  manifest.json
  annotation.json
  preview.html
  candidate_manifest.json
  candidate_preview.html
```

## candidate_manifest.json

Top-level fields:

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Uses the current package schema version |
| `package_type` | string | `996-ready` |
| `detection_method` | string | `rule_and_image_feature` |
| `source_asset_id` | string | Source `ui_preview` asset id |
| `generation_job_id` | string | Generation job id, or source asset id fallback |
| `ui_preview` | string | Relative path to `ui_preview.png` |
| `candidates_dir` | string | Relative candidate directory |
| `coordinate_space` | string | `ui_preview_pixels` |
| `candidates` | array | Candidate component list |

Each `candidates[]` item contains:

| Field | Type | Rule |
| --- | --- | --- |
| `candidate_id` | string | Stable candidate id, such as `button_candidate_01` |
| `candidate_type` | string | One of the supported candidate types |
| `bounds` | object | Pixel bounds in `ui_preview` coordinate space |
| `confidence` | number | 0.0 to 1.0 review hint |
| `image_path` | string | Relative path under `candidates/` |
| `review_status` | string | Starts as `pending` |

## candidate_preview.html

`candidate_preview.html` overlays candidate boxes on top of `ui_preview.png`.

It is intended for manual review of:

- whether the candidate box covers a useful component
- whether the crop is too large or too small
- whether the candidate type is reasonable
- whether later 996 asset extraction should accept, adjust, or reject the candidate

## Current Limitations

This stage can identify likely high-contrast UI regions only. It does not understand text, semantic UI meaning, or arbitrary layout variation.

Known risks:

- visually similar panels may be labeled as frame candidates
- decorative square elements may be labeled as icon or slot candidates
- unusual layouts may place real components outside the current proportional regions
- confidence reflects local contrast, not semantic correctness

## Recommended Next Steps

1. Collect review feedback from `candidate_preview.html`.
2. Tune candidate region rules using real accepted/rejected examples.
3. Add more fixture images that represent backpack, shop, activity, and role-panel screens.
4. Keep candidate outputs additive until the review quality is stable enough to affect downstream export decisions.
