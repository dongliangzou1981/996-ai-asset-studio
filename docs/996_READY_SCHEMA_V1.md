# 996-ready Schema V1

## Scope

Schema V1 fixes the local `996-ready/` package contract for Sprint 10A.

It covers:

- `manifest.json`
- `annotation.json`
- local relative paths
- component classification
- validation rules

It does not cover:

- database schema changes
- business pipeline changes
- AI component recognition upgrades
- YOLO, OCR, or SAM
- automatic transparent PNG generation
- ZIP export
- cloud deployment

## Package Layout

```text
996-ready/
  ui_preview.png
  components/
    {component_id}.png
  manifest.json
  annotation.json
  preview.html
```

All JSON paths are relative to the package root and must use `/`.

## manifest.json

### Required Top-Level Fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Must be `"1.0"` |
| `package_type` | string | Must be `"996-ready"` |
| `source_asset_id` | string | Non-empty source UI preview asset id |
| `generation_job_id` | string | Non-empty generation job id |
| `device_type` | string | Must be `mobile_landscape`, `pc_landscape`, or legacy `mobile` / `pc` |
| `asset_mode` | string | Optional; `ui_package` or `resource_production` |
| `resolution` | object | Required width and height object |
| `ui_preview` | string | Relative path to UI preview image |
| `components_dir` | string | Relative component directory |
| `transparent_policy` | object | Optional Resource Production transparent policy |
| `resource_summary` | object | Optional Resource Production summary |
| `components` | array | Non-empty component list |

### resolution

| Field | Type | Rule |
| --- | --- | --- |
| `width` | integer | Positive integer |
| `height` | integer | Positive integer |

Device-specific resolution rules:

- `mobile_landscape`: must be strict 16:9 landscape, recommended `1536x864` or `1280x720`
- `pc_landscape`: must be PC landscape, allowing common 4:3, 3:2, or 16:9 canvases such as `1536x1024` or `1280x960`
- legacy `mobile` / `pc`: accepted for backward compatibility and not upgraded in-place by the validator

### components[]

| Field | Type | Rule |
| --- | --- | --- |
| `component_id` | string | Non-empty unique component id |
| `component_type` | string | Must be one of Schema V1 component types |
| `asset_mode` | string | Optional; `ui_package` or `resource_production` |
| `resource_category` | string | Optional Resource Production category |
| `production_usage` | string | Optional usage hint for 996 follow-up work |
| `component_name_zh` | string | Non-empty Chinese display name |
| `resource_group` | string | Must be one of Schema V1 resource groups |
| `file` | string | Relative path to component PNG |
| `bounds` | object | Component bounds in `ui_preview` pixels |
| `transparent` | object | Optional Sprint 10B transparent asset metadata |
| `transparent_png_required` | boolean | Whether the component should eventually be transparent |
| `transparent_png_verified` | boolean | Whether transparency has been verified |

### bounds

| Field | Type | Rule |
| --- | --- | --- |
| `x` | integer | Non-negative integer |
| `y` | integer | Non-negative integer |
| `width` | integer | Positive integer |
| `height` | integer | Positive integer |

## annotation.json

### Required Top-Level Fields

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Must be `"1.0"` |
| `source_asset_id` | string | Non-empty source UI preview asset id |
| `device_type` | string | Optional for legacy packages; new output should match `manifest.device_type` |
| `asset_mode` | string | Optional; new Resource Production output should match `manifest.asset_mode` |
| `coordinate_space` | string | Must be `"ui_preview_pixels"` |
| `transparent_policy` | object | Optional Resource Production transparent policy |
| `components` | array | Non-empty component annotation list |

### components[]

| Field | Type | Rule |
| --- | --- | --- |
| `component_id` | string | Non-empty component id |
| `component_type` | string | Must be one of Schema V1 component types |
| `asset_mode` | string | Optional; `ui_package` or `resource_production` |
| `resource_category` | string | Optional Resource Production category |
| `production_usage` | string | Optional usage hint for 996 follow-up work |
| `component_name_zh` | string | Non-empty Chinese display name |
| `resource_group` | string | Must be one of Schema V1 resource groups |
| `bounds` | object | Same coordinate meaning as manifest |
| `style` | object | Font style metadata |
| `image` | object | Component image metadata |
| `transparent` | object | Optional Sprint 10B transparent asset metadata |
| `recognition` | object | Recognition source metadata |
| `requires_manual_review` | boolean | Whether manual review is required |
| `review_status` | string | Review status enum |
| `notes` | string | Human-readable notes, may be empty |

### style

| Field | Type | Rule |
| --- | --- | --- |
| `font_family` | string | Non-empty string |
| `font_size` | integer | Positive integer |
| `font_color` | string | `#RRGGBB` color |

### image

| Field | Type | Rule |
| --- | --- | --- |
| `file` | string | Relative component PNG path |
| `format` | string | Must be `"png"` |
| `color_mode` | string | Must be `"RGBA"` |
| `alpha` | string | `required`, `optional`, or `none` |
| `transparent_background` | boolean | Whether background transparency is expected |

### recognition

| Field | Type | Rule |
| --- | --- | --- |
| `method` | string | `template`, `fixture`, or `manual` |
| `confidence` | number or null | Null or number between 0 and 1 |

### transparent

`transparent` is optional for backward compatibility. When present, it must follow [Transparent Asset Schema](./TRANSPARENT_ASSET_SCHEMA.md).

| Field | Type | Rule |
| --- | --- | --- |
| `required` | boolean | Whether this component type must be transparent |
| `verified` | boolean | Whether this component file has been verified as transparent |
| `status` | string | `not_required`, `unverified`, or `verified` |

## Component Types

Schema V1 component types:

```text
panel
bar
button
icon
frame
slot
tab
badge
progress
input
border
background
text
decoration
unknown
```

## Resource Groups

Schema V1 resource groups:

```text
main
bag_ui
shop
activity
player_main_layer_ui
public
item
skill_icon
skill_icon_c
unknown
```

## Resource Production Fields

`asset_mode` values:

```text
ui_package
resource_production
```

`resource_category` values:

```text
layout_bar
panel_region
button_asset
icon_asset
frame_asset
input_asset
slot_asset
tab_asset
background_asset
unknown_asset
```

`transparent_policy` is optional. When present, it should include:

| Field | Type | Rule |
| --- | --- | --- |
| `required_component_types` | array | String array |
| `allowed_flat_component_types` | array | String array |
| `verification` | string | Non-empty verification description |

## Review Status

Schema V1 review statuses:

```text
pending
reviewed
approved
rejected
```

## Path Rules

All resource paths must:

- be relative to the package root
- use `/` separators
- avoid absolute paths
- avoid `..`
- point to an existing local file when validated

Valid:

```text
ui_preview.png
components/main_bottom_bar.png
```

Invalid:

```text
C:/assets/main_bottom_bar.png
../main_bottom_bar.png
components\main_bottom_bar.png
```

## Validator Coverage

`scripts/validate_996_export.py` validates:

- required package files
- Schema V1 top-level fields
- required component fields
- field types
- component type enum
- optional transparent field
- resource group enum
- review status enum
- `device_type` enum
- optional Resource Production `asset_mode`, `resource_category`, `production_usage`, and `transparent_policy`
- `mobile_landscape` 16:9 landscape resolution rule
- `pc_landscape` PC landscape resolution rule
- relative path rules
- referenced file existence

## Current Implementation Boundary

Schema V1 validates the package contract. It does not mean current component slicing is intelligent recognition, and it does not mean transparent PNG generation is complete.
