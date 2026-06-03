# Test Cases

## Sprint 1 验证

1. 前端依赖安装后运行 `npm run build`。
2. 后端依赖安装后运行 `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`。
3. 请求 `GET /health` 返回 `status: ok`。
4. 请求 `GET /schema/tables` 返回 7 张核心表。

## Sprint 2 验证

1. 运行 `backend\.venv\Scripts\python -m pytest backend\tests -q`，验证项目与风格资料 CRUD。
2. 运行 `npm test -- --runInBand`，验证前端项目管理和风格管理组件。
3. 运行 `npm run build`，验证 Next.js 生产构建。
4. 启动后端并请求 `/health`、`/projects`、`/style_profiles`。
5. 请求 `/openapi.json`，确认 CRUD schema 存在。
