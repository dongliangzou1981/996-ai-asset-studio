# Screen Edit Workflow

## Scope

Sprint 12E adds single-screen edit capability for already generated 996-ready UI packages.

The edit workflow is style-preserving:

- reads `style_codes/{STYLE_CODE}/style.json`
- reads the existing screen package
- uses the existing `ui_preview.png` or an optional uploaded screenshot as reference
- builds an edit prompt that preserves the original style and layout
- runs the existing real provider pipeline
- runs Component Processing
- writes a new 996-ready package version

This stage supports whole-image editing through prompt fallback. Box-selected local editing is not included yet.

## Select An Existing Screen

Choose an existing package such as:

```text
assets/uploads/996-ready/STYLE_0001/main_ui/{old_generation_job_id}/
```

The package should contain:

- `ui_preview.png`
- `manifest.json`
- `annotation.json`
- `candidate_manifest.json` when available
- `components/`
- `candidates/` when available

## Input An Edit Request

Example edit requests:

- Make the right-side shop button larger.
- Make the bottom skill bar more ornate.
- Make the chat box darker.
- Keep the layout, only enhance gold ornaments.
- Add dragon-pattern borders to the role avatar frame.

## Run The Edit

Use the existing `ui_preview.png`:

```powershell
backend\.venv\Scripts\python.exe scripts\edit_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type main_ui `
  --device-type mobile_landscape `
  --source-package assets\uploads\996-ready\STYLE_0001\main_ui\{old_generation_job_id} `
  --edit-prompt "把右侧商城按钮改大一点，底部技能栏更华丽"
```

Use an uploaded screenshot instead:

```powershell
backend\.venv\Scripts\python.exe scripts\edit_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type main_ui `
  --device-type mobile_landscape `
  --source-package assets\uploads\996-ready\STYLE_0001\main_ui\{old_generation_job_id} `
  --reference-image assets\references\current-main-ui-screenshot.png `
  --edit-prompt "保留布局，只增强金色纹饰"
```

Default `device_type` is `mobile_landscape`.

Supported values:

- `mobile_landscape`
- `pc_landscape`

PC landscape edit example:

```powershell
backend\.venv\Scripts\python.exe scripts\edit_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type main_ui `
  --device-type pc_landscape `
  --source-package assets\uploads\996-ready\STYLE_0001\main_ui\{old_generation_job_id} `
  --edit-prompt "keep the same PC layout, make the right function area clearer for mouse clicking"
```

## Style Preservation

The script reads:

```text
style_codes/STYLE_0001/style.json
```

The edit prompt includes:

- `STYLE_CODE`
- style name
- style summary
- color palette
- font style
- border style
- button style
- icon style
- texture style
- source package path
- source preview path
- `device_type`
- annotation summary
- candidate summary when available
- user edit request

The prompt explicitly asks the provider to preserve the `STYLE_CODE` visual style and keep the layout and operation flow intact.

## New Version Output

The old package is not overwritten.

Old:

```text
assets/uploads/996-ready/STYLE_0001/main_ui/{old_generation_job_id}/
```

New:

```text
assets/uploads/996-ready/STYLE_0001/main_ui/{new_generation_job_id}/
```

Each new package contains:

- `ui_preview.png`
- `annotation.json`
- `manifest.json`
- `candidate_manifest.json`
- `candidate_preview.html`
- `delivery_report.json`
- `delivery_report.html`
- `components/`
- `candidates/`

## Edit Metadata

`delivery_report.json` records:

```json
{
  "device_type": "mobile_landscape",
  "edit_metadata": {
    "parent_generation_job_id": "old-generation-job-id",
    "edit_request": "把右侧商城按钮改大一点，底部技能栏更华丽",
    "edit_mode": "prompt_fallback",
    "style_code": "STYLE_0001",
    "device_type": "mobile_landscape",
    "source_preview_path": "assets/uploads/996-ready/STYLE_0001/main_ui/old-generation-job-id/ui_preview.png"
  }
}
```

The generation job input also records:

- `parent_generation_job_id`
- `edit_request`
- `edit_mode`
- `style_code`
- `device_type`
- `source_preview_path`

## Compare Old And New Versions

Compare:

```text
old/ui_preview.png
new/ui_preview.png
```

Then inspect:

- `new/candidate_preview.html`
- `new/delivery_report.html`
- `new/manifest.json`
- `new/annotation.json`

Run validator:

```powershell
backend\.venv\Scripts\python.exe scripts\validate_996_export.py assets\uploads\996-ready\STYLE_0001\main_ui\{new_generation_job_id}
```

## Current Limits

- Whole-image edit only.
- Box-selected local edit is not supported yet.
- No complex online editor.
- No mouse selection UI.
- No ZIP export.
- No cloud deployment.
- No user system.
- No database schema changes.
- No YOLO, OCR, or SAM.
- No model training.
- If the provider does not expose image edit or image-to-image through the current runner, the workflow uses prompt fallback.
