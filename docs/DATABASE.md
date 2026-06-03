# Database

Sprint 1 定义 7 张核心表，SQL 文件位于 `backend/app/db/schema.sql`。

Sprint 2 初始化 Alembic，迁移配置位于 `backend/alembic.ini`，迁移脚本位于 `backend/migrations/versions/0001_create_projects_style_profiles.py`。

## 表

- `projects`: 项目主表。
- `style_profiles`: 项目风格资料。
- `base_panels`: 基础画面或底图面板。
- `reference_images`: 参考图元数据。
- `ui_screens`: UI 界面稿记录。
- `assets`: 生成或导入的素材记录。
- `exports`: 导出任务与产物记录。

## 关系

- 一个 project 可拥有多个 style profile、base panel、reference image、ui screen、asset 和 export。
- `assets` 可选关联 `ui_screens`。
- `exports` 通过 `project_id` 关联项目。

## 迁移

本地默认 SQLite URL:

```text
sqlite:///backend/data/studio.db
```

可通过 `DATABASE_URL` 覆盖为 PostgreSQL 等 SQLAlchemy 支持的连接字符串。Sprint 2 的首个迁移脚本覆盖 `projects` 和 `style_profiles` 两张表。
