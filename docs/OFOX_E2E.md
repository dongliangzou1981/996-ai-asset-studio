# Ofox 本地真实端到端验收

Sprint 8C 的 Ofox 验收只需要用户提供一个本地环境变量：

```powershell
$env:OFOX_API_KEY="你的真实 Ofox API Key"
```

不要把真实 API Key 写入数据库、`config_json`、文档、截图或 GitHub。`.env.local` 如需使用，也只允许包含：

```env
OFOX_API_KEY=你的真实 Ofox API Key
```

后端进程必须能读到 `OFOX_API_KEY`。如果后端已经启动过，设置环境变量后请重启后端。

## 默认 Provider 配置

脚本会自动创建或更新名为 `Ofox UI Default` 的默认 Provider，用户不需要手写 JSON。

默认配置为：

```json
{
  "api_key_env": "OFOX_API_KEY",
  "base_url": "https://api.ofox.ai/v1",
  "model": "gpt-image-2"
}
```

真实请求 endpoint 为：

```text
https://api.ofox.ai/v1/images/generations
```

如果 `gpt-image-2` 在当前 Ofox 账号或接口中不可用，请用 Ofox 支持的图片模型替换：

```powershell
backend\.venv\Scripts\python scripts\setup_ofox_provider.py --model "你的可用图片模型"
backend\.venv\Scripts\python scripts\verify_ofox_e2e.py --model "你的可用图片模型"
```

## 本地验收命令

在后端终端设置 Key 并启动后端：

```powershell
$env:OFOX_API_KEY="你的真实 Ofox API Key"
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

打开另一个终端，执行默认 Provider 初始化：

```powershell
backend\.venv\Scripts\python scripts\setup_ofox_provider.py
```

执行真实端到端验收：

```powershell
backend\.venv\Scripts\python scripts\verify_ofox_e2e.py
```

脚本会自动完成：

1. 检查当前终端是否存在 `OFOX_API_KEY`
2. 检查后端 Provider health 是否为 `healthy`
3. 创建或复用 `Sprint8C-Ofox-E2E` 测试项目
4. 创建最小 `real_ui_generation` job
5. 调用 `POST /generation_jobs/{id}/run`
6. 检查 `ai_generated` 的 `ui_preview`
7. 检查至少 6 个 `component_processing` 的 `sliced_component`
8. 检查 `manifest.json`
9. 检查 `annotation.json` 中文字段
10. 检查 `preview.html`

## 成功输出

成功后脚本会打印：

```text
job_id=...
ui_preview=...
manifest=...
annotation=...
preview_html=...
component_count=6
manifest_sample=...
annotation_sample=...
```

同时可以在页面检查：

- `http://localhost:3001/job-center`
- `http://localhost:3001/assets`

## 失败优先检查

1. 后端是否在设置 `OFOX_API_KEY` 后重新启动
2. `/providers` 中 `Ofox UI Default` health 是否为 `healthy`
3. Ofox 是否支持当前 `model`
4. `base_url` 是否为 `https://api.ofox.ai/v1`
5. `/job-center` 中任务的 `error_message` 和 `logs`
6. 后端控制台日志
