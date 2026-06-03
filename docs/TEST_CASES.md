# Test Cases

## Sprint 1 验证

1. 前端依赖安装后运行 `npm run build`。
2. 后端依赖安装后运行 `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`。
3. 请求 `GET /health` 返回 `status: ok`。
4. 请求 `GET /schema/tables` 返回 7 张核心表。

