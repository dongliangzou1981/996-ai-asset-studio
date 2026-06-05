# Style Guided Screen Workflow

## Scope

Sprint 12A adds the first style-code driven single-screen generation workflow.

The workflow is intentionally narrow:

- one style code
- one reference image
- one screen type
- one generated 996 UI screen
- automatic Component Processing and candidate detection after generation

It does not support batch full-set generation yet.

## 1. Create STYLE_0001 From An Existing Result

Start from a completed `996-ready` package.

```powershell
backend\.venv\Scripts\python.exe scripts\create_style_code.py --package-dir assets\uploads\996-ready\{generation_job_id} --style-name "Dark Gold Dragon"
```

The script writes:

```text
style_codes/
  STYLE_0001/
    style.json
```

`style.json` records:

- source job id
- source asset id
- original `ui_preview.png`
- style summary
- color palette
- font guidance
- border guidance
- button guidance
- icon guidance
- texture guidance

## 2. Generate Main UI With STYLE_0001

Use a main UI reference image:

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type main_ui `
  --reference-image assets\references\main-ui-reference.png `
  --prompt "主界面需要突出底部技能栏、右侧菜单和小地图"
```

The script:

1. Reads `style_codes/STYLE_0001/style.json`.
2. Builds a reference-guided prompt.
3. Creates a `real_ui_generation` job.
4. Uses the existing real provider runner.
5. Generates `ui_preview`.
6. Runs Component Processing.
7. Produces Schema V1 files.
8. Produces `candidate_manifest.json`.
9. Produces `candidate_preview.html`.
10. Copies the final package into the style-guided output directory.

## 3. Generate Role UI With STYLE_0001

Use a role panel reference image:

```powershell
backend\.venv\Scripts\python.exe scripts\generate_screen_with_style.py `
  --style-code STYLE_0001 `
  --screen-type role_ui `
  --reference-image assets\references\role-ui-reference.png `
  --prompt "角色界面需要突出装备槽、角色立绘区域、战力和属性列表"
```

The output keeps the same style code but writes to the role UI branch.

## 4. Output Directory

Main UI:

```text
assets/uploads/996-ready/
  STYLE_0001/
    main_ui/
      {generation_job_id}/
        ui_preview.png
        manifest.json
        annotation.json
        preview.html
        candidate_manifest.json
        candidate_preview.html
        components/
        candidates/
```

Role UI:

```text
assets/uploads/996-ready/
  STYLE_0001/
    role_ui/
      {generation_job_id}/
        ui_preview.png
        manifest.json
        annotation.json
        preview.html
        candidate_manifest.json
        candidate_preview.html
        components/
        candidates/
```

## 5. Validate Output

The validator supports both direct and style-guided package paths:

```powershell
backend\.venv\Scripts\python.exe scripts\validate_996_export.py assets\uploads\996-ready\STYLE_0001\main_ui\{generation_job_id}
```

The validation report includes layout metadata:

- `mode`
- `style_code`
- `screen_type`
- `generation_job_id`

## Provider Requirement

The generation script requires an enabled real provider:

- `openai`
- `ofox`

The provider must have `config_json.api_key_env`, and the matching environment variable must be set.

If the API key environment variable is missing, the script exits with a clear error such as:

```text
Failed to generate style-guided screen: Environment variable OFOX_API_KEY is not set
```

## Current Limitations

- Only single-screen generation is supported.
- Batch full-set generation is not supported.
- ZIP export is not supported.
- Cloud deployment is not supported.
- User system and commercial admin backend are not supported.
- Complex AI visual recognition is not included.
- YOLO, OCR, SAM, and model training are not included.
- The reference image is recorded and used in the reference-guided prompt. The current provider runner does not yet send reference image pixels to a dedicated image-to-image endpoint.
