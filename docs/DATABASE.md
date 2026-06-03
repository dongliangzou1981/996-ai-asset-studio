# Database

Sprint 1 定义 7 张核心表，SQL 文件位于 `backend/app/db/schema.sql`。

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

