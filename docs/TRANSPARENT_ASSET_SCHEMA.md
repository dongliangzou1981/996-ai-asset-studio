# Transparent Asset Schema

## Scope

This document defines the Sprint 10B transparent asset standard for 996-ready packages.

It standardizes metadata only. It does not generate transparent PNGs, upgrade component recognition, modify the database, add ZIP export, or change the business pipeline.

## Transparent Field

`transparent` is an optional component-level object in both `manifest.json` and `annotation.json`.

It is optional for backward compatibility with Sprint 10A Schema V1 packages. When present, it is strictly validated.

```json
{
  "transparent": {
    "required": true,
    "verified": true,
    "status": "verified"
  }
}
```

## Field Rules

| Field | Type | Rule |
| --- | --- | --- |
| `required` | boolean | Whether this component type must be transparent |
| `verified` | boolean | Whether this component file has been verified as transparent |
| `status` | string | `not_required`, `unverified`, or `verified` |

Consistency rules:

- If `verified` is `true`, `status` must be `verified`.
- If `required` is `false`, `status` must not be `verified`.
- If `required` is `true`, `status` must not be `not_required`.
- In `annotation.json`, if `transparent.required` is `true`, `image.alpha` must be `required`.
- In `annotation.json`, if `transparent.required` is `true`, `image.transparent_background` must be `true`.

## Components That Must Be Transparent

These component types must set `transparent.required = true` when the `transparent` field is present:

```text
button
icon
frame
input
```

Reason:

- `button`: needs to sit on different panels and support future state composition.
- `icon`: needs to be reused inside buttons, slots, panels, and badges.
- `frame`: needs transparent center and edges for overlay usage.
- `input`: needs transparent outside bounds and a reusable text region.

## Components That May Be Non-Transparent

These component types may set `transparent.required = false`:

```text
panel
background
```

Reason:

- `panel`: often includes a baked background, texture, and fixed rectangular area.
- `background`: is usually a full opaque or semi-opaque layer by design.

## Manifest Example

```json
{
  "component_id": "primary_action_button",
  "component_type": "button",
  "component_name_zh": "主操作按钮",
  "resource_group": "main",
  "file": "components/primary_action_button.png",
  "bounds": {
    "x": 720,
    "y": 880,
    "width": 180,
    "height": 72
  },
  "transparent": {
    "required": true,
    "verified": true,
    "status": "verified"
  },
  "transparent_png_required": true,
  "transparent_png_verified": true
}
```

## Annotation Example

```json
{
  "component_id": "primary_action_button",
  "component_type": "button",
  "component_name_zh": "主操作按钮",
  "resource_group": "main",
  "bounds": {
    "x": 720,
    "y": 880,
    "width": 180,
    "height": 72
  },
  "image": {
    "file": "components/primary_action_button.png",
    "format": "png",
    "color_mode": "RGBA",
    "alpha": "required",
    "transparent_background": true
  },
  "transparent": {
    "required": true,
    "verified": true,
    "status": "verified"
  }
}
```

## Backward Compatibility

Packages without `transparent` remain valid if they satisfy the rest of Schema V1.

The existing fields remain supported:

```json
{
  "transparent_png_required": true,
  "transparent_png_verified": false
}
```

New packages should include both the old fields and the new `transparent` object during the transition period.

## Validator Coverage

`scripts/validate_996_export.py` checks:

- `transparent` is an object when present.
- `required` and `verified` are booleans.
- `status` is one of `not_required`, `unverified`, `verified`.
- `button`, `icon`, `frame`, and `input` require transparency when `transparent` is present.
- `panel` and `background` may be non-transparent.
- annotation image metadata agrees with `transparent.required`.

## Current Boundary

Sprint 10B standardizes transparent metadata. It does not automatically create transparent PNGs and does not prove that generated component slicing is intelligent recognition.
