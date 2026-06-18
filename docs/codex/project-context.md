# 996 美术资产生成 Codex 项目上下文

## 1. 项目目标

本项目面向 996 传奇引擎，目标是生成可落地使用的游戏 UI 美术资产。

核心输出包括：

- UI 完整图
- 组件切图
- 中文标注
- `manifest.json`
- `annotation.json`
- `candidate_manifest.json`
- `delivery_report.json`
- `996-ready` 导出包

本项目不是知桥 AI，不记录课程、教师端、学生端、Supabase、Obsidian、iOS 签名或其他独立问题。

## 2. 当前核心方向

- 主界面生成生产链
- 固定布局骨架
- 参考图生成
- 参考图按比例生成
- 三张候选图
- 人工确认
- 自动标记
- 自动切图
- 透明 PNG 检测和后处理
- 组件验收
- 导出闭环

当前重点链路之一是 `main_task_panel`：生成 3 候选，人工选择，贴回 1728×972 主画布，验收入库，导出 `main_task_panel.png`、`manifest.json`、`component_record.json`。

## 3. 主要目录

- `backend/`：FastAPI 后端、数据库、API、后端测试。
- `frontend/`：Next.js 前端，Production Studio 页面和 Jest 测试。
- `scripts/`：生产链、样式生成、996-ready 校验、Ofox 配置、本地启动和环境检查脚本。
- `tests/`：根级脚本和生产链 pytest。
- `docs/`：项目文档、生产规范、Sprint 记录、验收记录。
- `harness/`：验收和示例输出辅助目录。
- `training_samples/`：prompt、候选、验收样本数据。
- `assets/`：上传、生成和 996-ready 运行时产物。
- `exports/`：导出产物目录。
- `style_codes/`：风格编号和样式包。

## 4. 关键业务模块

- Production Studio：前端 `/studio` 工作台和结果中心。
- 主界面生产链：`scripts/main_ui_production_chain.py`。
- 候选图生成：主界面候选、HUD 模块候选。
- `candidate_preview`：用于审核候选，不等于最终正式资源。
- 人工确认：候选选择、组件确认、验收入库。
- 标记验收测试模式：`MARKING_TEST` 相关工作流。
- 切图和导出：`components/`、`confirmed_components/`、`996-ready` 包。
- prompt 学习闭环：`training_samples/` 和 prompt samples。
- manifest / annotation 输出：`manifest.json`、`annotation.json`、`candidate_manifest.json`。
- 透明 PNG 后处理：AI 候选图需要验证 alpha，不得只看文件格式。

## 5. 主界面固定布局规范

画面：

- 16:9 横屏手机主界面。
- 基准布局：`1728×972`。
- 其他尺寸按比例缩放。

左上任务区：

- `x=24`
- `y=40`
- `w=286`
- `h=330`
- 允许小误差。
- 总宽不得超过 `302 px`。

底部中间信息区：

- 聊天+物品整体区域：`x=596, y=666, w=448, h=192`
- 物品栏：`x=596, y=666, w=448, h=56`
- 聊天框：`x=596, y=722, w=448, h=136`
- 聊天框和物品栏宽度必须一致。
- 聊天框宽度不得超过 `468 px`。

红蓝球整体区域：

- `x=318`
- `y=640`
- `w=266`
- `h=218`
- 红蓝球右边缘与聊天框左边缘之间的间距 `8~18 px`。
- 目标间距 `12 px`。

右侧辅助区：

- `x=1056`
- `y=640`
- `w=210`
- `h=218`
- 左缘与聊天框右缘之间的间距 `8~18 px`。
- 目标间距 `12 px`。

右下技能区：

- 后续可能支持一圈或二圈技能。
- 必须合入主界面生成。
- 横屏操作体验优先。
- 风格随整体 UI。

## 6. 生成模式

三种生成模式必须区分，不能混淆。

模式一：普通生成

- 不使用参考图。
- 不使用参考比例。
- 前端标签为“普通生成”。

模式二：参考图生成

- 使用参考图。
- 不使用比例参数。
- 前端标签为“参考图生成（不按比例）”。

模式三：参考图按比例生成

- 使用参考图。
- 使用比例参数。
- 前端标签为“参考图生成（按比例）”。
- 参考比例只属于第三种模式，不能混入普通生成。

代码层注意：后端 `ProductionGenerationMode` 当前为 `auto_generate` / `reference_guided`，前端在 UI 层区分 `plain` / `reference` / `reference_ratio`。修改时必须看真实映射，不能只按名称猜。

## 7. 开发约束

- 不推翻已完成生产链。
- 不大规模重构。
- 优先生产可用。
- 固定骨架不能随意漂移。
- 不把知桥项目内容混入本项目。
- 不随意删除候选图、人工确认、验收、导出流程。
- 不编造不存在的 AI 接口能力。
- 不把真实 key 写入代码、文档、测试或提交。
- 对透明图、标记、切图相关改动必须验证。
- 自动标记和切图结果必须允许人工复核。
- 预览图只用于审核，不作为正式 996 资源。

## 8. 重要命令

已确认项目根目录没有根级 `package.json`，前端命令在 `frontend/package.json`。

Git：

```powershell
git status --short
git diff --check
git diff --stat
```

前端：

```powershell
cd frontend
npm test
npm run build
```

注意：`frontend/package.json` 当前没有 `typecheck` script，不要编造 `npm run typecheck`。

后端 / pytest：

```powershell
python -m pytest tests
python -m pytest backend/tests
python -m pytest tests/test_main_ui_production_chain.py
python -m pytest backend/tests/test_main_ui_production_api.py
```

如果使用项目虚拟环境且存在：

```powershell
backend\.venv\Scripts\python.exe -m pytest tests
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

996-ready 校验：

```powershell
python scripts/validate_996_export.py <996-ready-package-path>
```

本地工作台：

```powershell
scripts/start_local_studio.ps1
scripts/check_studio_env.ps1
```

脚本会使用 `backend\.venv\Scripts\python.exe`，默认后端 `127.0.0.1:8001`，前端 `127.0.0.1:3001/studio`。

## 9. 当前项目边界

本上下文只记录 996 美术资产生成内容。

不要记录或迁入：

- 知桥 AI 课程、教师端、学生端、Supabase 内容。
- Obsidian 工作流。
- iOS 签名。
- 其他独立产品或临时问题。
