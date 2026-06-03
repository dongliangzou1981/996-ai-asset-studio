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

### GET /generation_jobs

Accepts optional `project_id` query parameter. Sprint 3 only lists job records; AI generation is not connected.

```json
{
  "items": []
}
```

## Frontend Call Example

```ts
await studioApi.createBasePanel({
  project_id: "project-id",
  style_profile_id: "style-profile-id",
  panel_type: "main_panel",
  device_type: "mobile",
  width: 1080,
  height: 1920,
  texture: "soft_glass",
  border_style: "rounded_8",
  background_style: "layered_gradient",
  color_scheme: "blue_white",
});
```

