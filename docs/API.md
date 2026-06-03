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
  "job_type": "asset_prepare",
  "status": "pending",
  "progress": 0,
  "input_json": "{}",
  "output_json": "",
  "error_message": "",
  "logs": "queued"
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
  "metadata_json": "{}"
}
```

### GET /assets

Accepts optional `project_id` and `asset_type` query parameters.

### GET /assets/{asset_id}

Returns one asset or `404`.

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
  job_type: "asset_prepare",
  status: "pending",
  progress: 0,
  input_json: "{}",
  output_json: "",
  error_message: "",
  logs: "queued",
});
```
