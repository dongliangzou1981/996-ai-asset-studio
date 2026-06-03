# API

Base URL: `http://127.0.0.1:8000`

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

