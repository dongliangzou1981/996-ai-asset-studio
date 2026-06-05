# Master Style Workflow

## Scope

Sprint 12C introduces the Master Style Workflow.

The master style starts from a generated `main_ui`. The generated main interface becomes the style source, and the system creates a new independent `STYLE_CODE`.

Later screens inherit that style code:

- `role_ui`
- `bag_ui`
- `shop_ui`
- `activity_ui`

This stage does not implement batch full-set generation. It provides the repeatable foundation for generating one screen at a time under the same style.

## Device Type

Generation scripts accept `--device-type`.

Supported values:

- `mobile_landscape`
- `pc_landscape`

Default:

```text
mobile_landscape
```

`mobile_landscape` uses a strict 16:9 horizontal mobile game target, currently `1536x864` by default.

`pc_landscape` uses a PC-oriented landscape target, currently `1536x1024` by default.

The selected `device_type` is written into:

- `style.json`
- `manifest.json`
- `annotation.json`
- `delivery_report.json`

## Screen Generation Modes

### auto_generate

Inputs:

- `screen_type`: must be `main_ui` for master style creation
- `style_name`
- `prompt`

Flow:

```text
auto_generate main_ui
-> Real UI Job
-> ui_preview
-> Component Processing
-> candidate detection
-> 996-ready package
-> STYLE_CODE creation
-> master style snapshot
```

Command:

```powershell
backend\.venv\Scripts\python.exe scripts\master_style_workflow.py `
  --screen-generation-mode auto_generate `
  --style-name "Dark Gold Dragon" `
  --device-type mobile_landscape `
  --prompt "dark gold dragon ornament, clear combat controls"
```

### reference_guided

Inputs:

- `reference_image`
- `screen_type`: must be `main_ui` for master style creation
- `style_name`
- `prompt`

Flow:

```text
reference image
-> reference-guided main_ui prompt
-> Real UI Job
-> ui_preview
-> Component Processing
-> candidate detection
-> 996-ready package
-> STYLE_CODE creation
-> master style snapshot
```

Command:

```powershell
backend\.venv\Scripts\python.exe scripts\master_style_workflow.py `
  --screen-generation-mode reference_guided `
  --style-name "Retro Red Gold" `
  --device-type mobile_landscape `
  --reference-image assets\references\main-ui-reference.png `
  --prompt "keep the layout rhythm, create a new red gold legend UI"
```

PC example:

```powershell
backend\.venv\Scripts\python.exe scripts\master_style_workflow.py `
  --screen-generation-mode auto_generate `
  --style-name "PC Dark Gold Dragon" `
  --device-type pc_landscape `
  --prompt "PC legend main UI, dense information panels, clear mouse-click controls"
```

The reference image constrains layout structure, but the prompt explicitly asks the provider not to copy the reference artwork directly.

## STYLE_CODE Creation

Each generated master style creates the next independent style code:

```text
STYLE_0001
STYLE_0002
STYLE_0003
```

Existing style codes are not overwritten.

The master style snapshot is saved under:

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

## 996-ready Output

The master `main_ui` package is written to:

```text
assets/uploads/996-ready/
  STYLE_0001/
    main_ui/
      {generation_job_id}/
        ui_preview.png
        annotation.json
        manifest.json
        preview.html
        candidate_manifest.json
        candidate_preview.html
        delivery_report.json
        delivery_report.html
        components/
        candidates/
```

## STYLE_CODE Selection

After `STYLE_0001` exists, later screens can be generated from it.

The style inheritance prompt reuses:

- color palette
- font style
- border style
- button style
- icon style
- texture style

## Generate Role UI

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type role_ui `
  --device-type mobile_landscape `
  --prompt "role panel with equipment slots, combat power, attributes, and character preview"
```

Output:

```text
assets/uploads/996-ready/STYLE_0001/role_ui/{generation_job_id}/
```

## Generate Bag UI

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type bag_ui `
  --device-type mobile_landscape `
  --prompt "bag interface with item grid, tabs, item details, and clear action buttons"
```

Output:

```text
assets/uploads/996-ready/STYLE_0001/bag_ui/{generation_job_id}/
```

## Generate Shop UI

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type shop_ui `
  --device-type mobile_landscape `
  --prompt "shop interface with category tabs, product cards, prices, and purchase buttons"
```

Output:

```text
assets/uploads/996-ready/STYLE_0001/shop_ui/{generation_job_id}/
```

## Generate Activity UI

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type activity_ui `
  --device-type mobile_landscape `
  --prompt "activity panel with event list, rewards, progress, and claim buttons"
```

Output:

```text
assets/uploads/996-ready/STYLE_0001/activity_ui/{generation_job_id}/
```

## Validation

`scripts/validate_996_export.py` supports style-guided package paths:

```powershell
backend\.venv\Scripts\python.exe scripts\validate_996_export.py assets\uploads\996-ready\STYLE_0001\main_ui\{generation_job_id}
```

The report identifies:

- `style_code`
- `screen_type`
- `generation_job_id`

## Current Limits

- No ZIP export.
- No cloud deployment.
- No user system.
- No commercial admin backend.
- No database schema changes.
- No YOLO.
- No OCR.
- No SAM.
- No model training.
- No batch full-set generation yet.
