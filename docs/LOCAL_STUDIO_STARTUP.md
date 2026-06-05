# Local Studio Startup

## 一键启动

推荐在项目根目录运行中文入口：

```powershell
.\启动工作台.ps1
```

底层脚本仍然保留：

```powershell
scripts/start_local_studio.ps1
```

脚本会检查：

- 当前目录是否是项目根目录
- `backend\.venv\Scripts\python.exe` 是否存在
- 当前 PowerShell 会话是否存在 `OFOX_API_KEY`

如果没有 `OFOX_API_KEY`，脚本会提示你输入。输入时不会显示 key。

启动完成后打开：

```text
http://127.0.0.1:3001/studio
```

## 重要说明

- 不要手动分多个终端配置环境变量和启动服务。
- `OFOX_API_KEY` 只会设置在当前 PowerShell 会话里。
- key 不会写入仓库。
- key 不会写入 `.env`。
- key 不会写入数据库。
- 关闭当前 PowerShell 后，本次输入的 key 会失效。

## 环境检查

如果 `/studio` 点击生成失败，先运行中文检查脚本：

```powershell
.\环境检查.ps1
```

底层检查脚本仍然保留：

```powershell
scripts/check_studio_env.ps1
```

检查项包括：

- `OFOX_API_KEY` 是否存在
- 后端 `http://127.0.0.1:8001/health` 是否可访问
- 前端 `http://127.0.0.1:3001/studio` 是否可访问
- `/production-studio/style-codes` 是否可访问
- Ofox provider health 是否正常

## 常见问题

### 生成失败：后端没有读取到 OFOX_API_KEY

请关闭旧的本地服务后，在项目根目录重新运行：

```powershell
scripts/start_local_studio.ps1
```

不要只在另一个终端里设置 key，因为已经启动的后端进程不会自动读取后来设置的环境变量。
