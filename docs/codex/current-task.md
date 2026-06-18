# 当前任务上下文

## 1. 当前任务目标

初始化 Codex 项目级上下文和任务级上下文，暂不开发业务功能。

## 2. 本轮只做什么

- 创建 `AGENTS.md`。
- 创建 `docs/codex/project-context.md`。
- 创建 `docs/codex/current-task.md`。
- 创建 `docs/codex/known-issues.md`。
- 创建 `docs/codex/worklog.md`。
- 记录项目目标、固定布局规范、生成模式、生产链边界、已知风险、真实验证命令。

## 3. 本轮不做什么

- 不开发新功能。
- 不修改生产链逻辑。
- 不修改前端业务页面。
- 不修改后端 API。
- 不修改测试断言。
- 不引入新依赖。
- 不重构目录结构。
- 不生成新的业务产物。
- 不提交 `.env`、key、token 或本地敏感信息。

## 4. 当前状态

- 项目路径：`D:\Codex\Projects\Active\996美术资产生成`
- 当前分支：`sprint20b-main-ui-production-chain`
- 当前任务类型：Codex 工作流上下文初始化。
- 本轮状态：已完成上下文文件创建，等待提交。
- 业务功能开发状态：暂停。
- 最近业务进展：`main_task_panel` 已支持 mock / ai 双模式，并增加透明检测和透明后处理；真实 AI 复验显示处理后 PNG 已有真实 alpha。
- 根目录原先没有 `AGENTS.md`。
- 原先没有 `docs/codex/` 目录。

## 5. 下一步步骤

1. 每轮开始执行 `git status --short`。
2. 读取 `AGENTS.md`。
3. 读取 `docs/codex/project-context.md`。
4. 读取本文件。
5. 根据用户目标写简短 plan。
6. 只做用户确认的最小任务。
7. 结束前更新本文件、`known-issues.md`、`worklog.md`。

## 6. 验收标准

- `AGENTS.md` 存在且简短。
- `docs/codex/project-context.md` 存在。
- `docs/codex/current-task.md` 存在。
- `docs/codex/known-issues.md` 存在。
- `docs/codex/worklog.md` 存在。
- `project-context.md` 明确记录 996 项目目标、固定布局规范、生成模式、生产链边界。
- `current-task.md` 明确本轮只是上下文初始化。
- `git diff` 可审查。
- 没有业务功能改动。

## 7. 必须运行的验证命令

本轮是文档/上下文初始化，必须至少运行：

```powershell
git status --short
git diff --check
git diff --stat
```

如果依赖已安装且命令存在，可运行：

```powershell
cd frontend
npm test
npm run build
cd ..
python -m pytest tests
python -m pytest backend/tests
```

不存在的命令不要运行；例如当前 `frontend/package.json` 没有 `typecheck` script。

本轮实际验证结果：

- `git status --short`：仅显示本轮新增 `AGENTS.md` 和 `docs/codex/`。
- `git diff --check`：通过。
- `git diff --stat`：已运行。
- `cd frontend; npm test`：通过，9 个 test suites、29 个 tests。
- `cd frontend; npm run build`：首次 124 秒超时；用更长超时重跑后通过。
- `python -m pytest tests`：通过，58 passed、1 skipped。
- `python -m pytest backend/tests`：通过，54 passed。

## 8. 完成后下一轮应该做什么

下一轮 Codex 应先读本上下文，再根据用户指令继续。

如果用户继续 `main_task_panel`，建议从“人工视觉验收后的 prompt 微调或生产候选确认”开始，不要扩展其他 HUD 模块。

如果用户要求开发新功能，必须先确认不会破坏：

- 三张候选图流程。
- 人工选择和验收。
- 1728×972 固定布局骨架。
- manifest / annotation / component record 输出。
- 透明 PNG 检测和后处理。
