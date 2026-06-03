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

前端通过静态页面展示项目状态。后端提供 `/health` 和 `/schema/tables`，数据库结构先以 SQL 文件定义，后续 Sprint 再接入迁移工具和持久化访问层。

## 技术栈

- Frontend: Next.js 15, React, TypeScript, Tailwind CSS
- Backend: FastAPI, Uvicorn
- Database: SQLite-compatible SQL schema for local development

