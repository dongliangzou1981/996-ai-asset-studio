# API

Base URL: `http://127.0.0.1:8000`

Swagger / OpenAPI: `http://127.0.0.1:8000/docs`

## Health

### GET /health

```json
{
  "status": "ok",
  "service": "996-ai-asset-studio-api"
}
```

### GET /schema/tables

Returns the current core table list.

## Projects

### POST /projects

```json
{
  "name": "Match-3 Launch",
  "description": "Playable ad art",
  "status": "draft"
}
```

### GET /projects

```json
{
  "items": []
}
```

### GET /projects/{project_id}

Returns one project or `404`.

### PUT /projects/{project_id}

Uses the same JSON body as `POST /projects`.

### DELETE /projects/{project_id}

Returns `204 No Content`.

## Style Profiles

### POST /style_profiles

```json
{
  "project_id": "project-id",
  "name": "Candy UI",
  "description": "Bright, rounded, mobile friendly",
  "palette_json": "{\"primary\":\"#ff6b9a\"}",
  "prompt_notes": "Use glossy buttons"
}
```

### GET /style_profiles

Accepts optional `project_id` query parameter.

### PUT /style_profiles/{style_profile_id}

Uses the same JSON body as `POST /style_profiles`.

### DELETE /style_profiles/{style_profile_id}

Returns `204 No Content`.

## Base Panels

Supported `panel_type` values:

- `main_panel`
- `sub_panel`
- `popup_panel`
- `list_panel`
- `input_panel`
- `button_panel`
- `icon_panel`

### POST /base_panels

```json
{
  "project_id": "project-id",
  "style_profile_id": "style-profile-id",
  "panel_type": "main_panel",
  "device_type": "mobile",
  "width": 1080,
  "height": 1920,
  "texture": "soft_glass",
  "border_style": "rounded_8",
  "background_style": "layered_gradient",
  "color_scheme": "blue_white"
}
```

### GET /base_panels

Accepts optional `project_id` query parameter.

### GET /base_panels/{base_panel_id}

Returns one base panel or `404`.

### PUT /base_panels/{base_panel_id}

Uses the same JSON body as `POST /base_panels`.

### DELETE /base_panels/{base_panel_id}

Returns `204 No Content`.

### POST /base_panels/{base_panel_id}/copy

Creates a copy of an existing base panel.

## Generation Jobs

Supported `status` values:

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`

### POST /generation_jobs

```json
{
  "project_id": "project-id",
  "provider_id": "provider-id",
  "job_type": "asset_prepare",
  "status": "pending",
  "progress": 0,
  "input_json": "{}",
  "output_json": "",
  "output_preview_path": "",
  "error_message": "",
  "logs": "queued",
  "auto_run": false
}
```

### GET /generation_jobs

Accepts optional `project_id` query parameter.

```json
{
  "items": []
}
```

### GET /generation_jobs/{generation_job_id}

Returns one generation job or `404`.

Response includes `provider_id`, `output_preview_path`, `output_json`, `logs`, and retry fields.

### PATCH /generation_jobs/{generation_job_id}

Updates status flow fields such as `status`, `progress`, `output_json`, `error_message`, and `logs`.

```json
{
  "status": "running",
  "progress": 50,
  "logs": "queued\nrunning"
}
```

### POST /generation_jobs/{generation_job_id}/retry

Resets a failed job to `pending`, clears `error_message`, sets `progress` to `0`, increments `retry_count`, and appends a retry log line.

### POST /generation_jobs/{generation_job_id}/run

Runs a job through the unified Job Runner. Supported provider types are `mock`, `openai`, and `custom`.

Successful runs create a 996-ready output directory under `assets/uploads/996-ready/{generation_job_id}` with previews, components, thumbnails, and `package/manifest.json`.

For `openai` providers, the runner reads the API key only from the environment variable named by `ai_providers.config_json.api_key_env`. The key is not saved to the database and is not returned in job responses.

OpenAI success writes `ai_generated` result assets, stores thumbnail paths, links assets to `generation_job_id`, and writes generated paths plus asset ids to `output_json`.

OpenAI failures set the job to `failed`, append logs, and write a concise `error_message` for missing `api_key_env`, missing environment variables, API failures, empty image responses, or image save failures.

### POST /generation_jobs/mock-ui

Creates a `mock_ui_generation` job. This endpoint does not call a real AI model.

```json
{
  "project_id": "project-id",
  "device_type": "mobile",
  "width": 1080,
  "height": 1920
}
```

### POST /generation_jobs/{generation_job_id}/run-mock

Runs the local mock worker for a `mock_ui_generation` job. Success flow is `pending -> running -> completed`; invalid mock input can produce `pending -> running -> failed`.

The mock worker creates:

- `ui_preview`
- `annotated_preview`
- `sliced_component`

Each result is written to `assets`, linked by `generation_job_id`, and summarized in `job.output_json`.

### GET /generation_jobs/{generation_job_id}/results

Returns assets created by a generation job.

## Assets

Supported `asset_type` values:

- `reference_image`
- `ui_preview`
- `annotated_preview`
- `sliced_component`
- `base_panel`
- `icon`

### POST /assets

```json
{
  "project_id": null,
  "asset_type": "reference_image",
  "device_type": "mobile",
  "width": 1080,
  "height": 1920,
  "file_path": "assets/uploads/reference.png",
  "original_filename": "reference.png",
  "metadata_json": "{}",
  "source": "uploaded",
  "generation_job_id": null
}
```

### GET /assets

Accepts optional `project_id`, `asset_type`, `device_type`, and `generation_job_id` query parameters.

### GET /assets/{asset_id}

Returns one asset or `404`.

### GET /assets/{asset_id}/file

Streams the asset file for browser previews.

### GET /assets/{asset_id}/thumbnail

Streams the generated thumbnail when present, otherwise falls back to the source image.

### POST /assets/{asset_id}/process-components

Processes a `ui_preview` asset with Sprint 8A template-based component rules. This is not intelligent visual recognition.

Creates:

- `996-ready/ui_preview.png`
- `996-ready/components/*.png`
- `996-ready/manifest.json`
- `996-ready/annotation.json`
- `996-ready/preview.html`

Response:

```json
{
  "manifest_path": "assets/uploads/996-ready/job-id/manifest.json",
  "annotation_path": "assets/uploads/996-ready/job-id/annotation.json",
  "preview_html_path": "assets/uploads/996-ready/job-id/preview.html",
  "component_asset_ids": ["asset-id"]
}
```

The component assets are written to `assets` with `asset_type = sliced_component`, `source = component_processing`, and the source `ui_preview` asset's `generation_job_id`.

### PUT /assets/{asset_id}

Uses the same JSON body as `POST /assets`.

### DELETE /assets/{asset_id}

Returns `204 No Content`.

### POST /assets/upload

Multipart upload endpoint. Fields:

- `file`: required image file, supported extensions `png`, `jpg`, `jpeg`, `webp`
- `project_id`: optional
- `asset_type`: defaults to `reference_image`
- `device_type`: optional
- `metadata_json`: optional

Returns the created asset record with file path, width, height, type, and original filename. Real AI generation is not connected.

## AI Providers

Provider config supports `mock`, `openai`, and `custom`.

OpenAI config may only include `api_key_env`. Do not store real keys in `config_json`.

### POST /ai_providers

```json
{
  "name": "Mock Provider",
  "type": "mock",
  "enabled": false,
  "config_json": "{}"
}
```

### GET /ai_providers

```json
{
  "items": []
}
```

### PUT /ai_providers/{provider_id}

Uses the same JSON body as `POST /ai_providers`.

### GET /ai_providers/{provider_id}/health

Returns health status for one provider.

Status values are `healthy` and `unhealthy`. Health responses never include real API keys.

### GET /ai_providers/health

Returns health status for all providers.

## Frontend Call Example

```ts
await studioApi.uploadAsset({
  file,
  project_id: null,
  asset_type: "reference_image",
  device_type: "mobile",
});

await studioApi.createGenerationJob({
  project_id: null,
  provider_id: null,
  job_type: "asset_prepare",
  status: "pending",
  progress: 0,
  input_json: "{}",
  output_json: "",
  output_preview_path: "",
  error_message: "",
  logs: "queued",
});

await studioApi.createMockUiGenerationJob({
  project_id: "project-id",
  device_type: "mobile",
  width: 1080,
  height: 1920,
});

await studioApi.runMockGenerationJob("generation-job-id");

await studioApi.runGenerationJob("generation-job-id");
```
