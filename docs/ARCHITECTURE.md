# Architecture

## 目录边界

- `frontend/`: Next.js 15 应用，负责资产工作台 UI。
- `backend/`: FastAPI 服务，负责 API、数据库访问和后续生成任务编排。
- `docs/`: 产品、架构、API、数据库和测试说明。
- `prompts/`: 后续保存 prompt 模板。
- `assets/`: 本地素材占位目录，默认不提交实际素材。
- `exports/`: 导出产物占位目录，默认不提交实际导出文件。
- `scripts/`: 工具脚本目录。
- `tests/`: 跨项目测试目录。

## Sprint 1 架构

前端通过工作台页面展示项目状态，并提供项目管理与风格管理页面。后端提供 `/health`、`/schema/tables`、项目 CRUD 和风格资料 CRUD，默认使用 SQLite 持久化。

## 技术栈

- Frontend: Next.js 15, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Uvicorn, Pydantic
- Database: SQLite-compatible SQL schema for local development, Alembic migrations

## Sprint 2 数据流

1. 前端 `studioApi` 使用 `NEXT_PUBLIC_API_BASE_URL` 或默认 `http://127.0.0.1:8000` 调用后端。
2. FastAPI 使用 Pydantic schema 进行 JSON schema 验证并生成 OpenAPI。
3. 后端仓储通过 Python `sqlite3` 读写本地数据库。
4. Alembic 提供 `projects` 与 `style_profiles` 的迁移入口。
