# Style Code Spec

## Scope

Sprint 12A introduces file-based style codes for style-guided single-screen generation.

A style code is not a preset. It is the unique id of one generated UI style that can be reused later to create additional screens in the same visual family.

This stage uses JSON files only and does not change the database schema.

## Directory Layout

```text
style_codes/
  STYLE_0001/
    style.json
  STYLE_0002/
    style.json
```

Style codes are allocated sequentially by scanning existing `STYLE_####` directories.

In Master Style Workflow, the style directory also stores the master `main_ui` snapshot:

```text
style_codes/
  STYLE_0001/
    style.json
    ui_preview.png
    annotation.json
    manifest.json
    delivery_report.json
    delivery_report.html
```

## style.json

Required fields:

| Field | Type | Description |
| --- | --- | --- |
| `style_code` | string | Unique code such as `STYLE_0001` |
| `style_name` | string | Human-readable style name |
| `source_job_id` | string | Generation job used as the style source |
| `source_asset_id` | string | Source `ui_preview` asset id when available |
| `style_summary` | string | Short reusable visual summary |
| `color_palette` | array | Dominant or default color list |
| `font_style` | string | Font and typography guidance |
| `border_style` | string | Border, frame, and panel edge guidance |
| `button_style` | string | Button visual guidance |
| `icon_style` | string | Icon visual guidance |
| `texture_style` | string | Texture and material guidance |
| `created_at` | string | UTC ISO timestamp |
| `updated_at` | string | UTC ISO timestamp |

Additional Sprint 12A fields:

| Field | Type | Description |
| --- | --- | --- |
| `original_ui_preview` | string | Source `ui_preview.png` path |
| `color_description` | string | Text description of the palette |

## Example

```json
{
  "style_code": "STYLE_0001",
  "style_name": "Dark Gold Dragon",
  "source_job_id": "job-id",
  "source_asset_id": "asset-id",
  "original_ui_preview": "assets/uploads/996-ready/job-id/ui_preview.png",
  "style_summary": "Dark Gold Dragon: 996 legend game UI style derived from source job output.",
  "color_palette": ["#1A120E", "#D9A441", "#6E1F16"],
  "color_description": "Dominant palette uses #1A120E, #D9A441, #6E1F16.",
  "font_style": "Bold, readable Chinese fantasy game UI typography; high contrast over dark panels.",
  "border_style": "Layered metallic fantasy borders with gold highlights and clear panel separation.",
  "button_style": "Readable rectangular fantasy buttons with bright trim and strong pressed-state potential.",
  "icon_style": "High-contrast item and skill icons with clear silhouettes suitable for slicing.",
  "texture_style": "Dark stone, aged metal, leather, and subtle ornamental texture.",
  "created_at": "2026-06-05T12:00:00+00:00",
  "updated_at": "2026-06-05T12:00:00+00:00"
}
```

## Creation Rule

`scripts/create_style_code.py` can create a style code from:

- an existing `996-ready/{generation_job_id}` package
- a direct package directory

Command examples:

```powershell
backend\.venv\Scripts\python.exe scripts\create_style_code.py --package-dir assets\uploads\996-ready\job-id --style-name "Dark Gold Dragon"
```

```powershell
backend\.venv\Scripts\python.exe scripts\create_style_code.py --generation-job-id job-id --style-name "Dark Gold Dragon"
```

## Extraction Strategy

Sprint 12A uses lightweight extraction only:

- reads `manifest.json` for `generation_job_id` and `source_asset_id`
- records the source `ui_preview.png`
- extracts a small dominant color palette from the preview image
- fills font, border, button, icon, and texture guidance with conservative default descriptions

It does not use YOLO, OCR, SAM, model training, or complex visual recognition.
