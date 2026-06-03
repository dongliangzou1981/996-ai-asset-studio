# API

Base URL: `http://127.0.0.1:8000`

Swagger / OpenAPI: `http://127.0.0.1:8000/docs`

## GET /health

返回后端运行状态。

```json
{
  "status": "ok",
  "service": "996-ai-asset-studio-api"
}
```

## GET /schema/tables

返回 Sprint 1 定义的数据库表名。

```json
{
  "tables": [
    "projects",
    "style_profiles",
    "base_panels",
    "reference_images",
    "ui_screens",
    "assets",
    "exports"
  ]
}
```

## Projects

### POST /projects

Request:

```json
{
  "name": "Match-3 Launch",
  "description": "Playable ad art",
  "status": "draft"
}
```

Response:

```json
{
  "id": "generated-id",
  "name": "Match-3 Launch",
  "description": "Playable ad art",
  "status": "draft",
  "created_at": "2026-06-03 10:00:00",
  "updated_at": "2026-06-03 10:00:00"
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

Request:

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

```json
{
  "items": []
}
```

### PUT /style_profiles/{style_profile_id}

Uses the same JSON body as `POST /style_profiles`.

### DELETE /style_profiles/{style_profile_id}

Returns `204 No Content`.

## Frontend Call Example

```ts
await studioApi.createProject({
  name: "Match-3 Launch",
  description: "Playable ad art",
  status: "draft",
});
```
