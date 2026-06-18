# AGENTS.md

- 开始任何工作前必须先执行 `git status --short`。
- 不覆盖、不回滚用户未提交改动；如有冲突，先汇报。
- 非简单任务先读 `docs/codex/project-context.md`。
- 每轮开始先读 `docs/codex/current-task.md`。
- 复杂任务先写 plan，再执行。
- 默认最小改动；不做无关重构。
- 不编造命令、文件、接口、环境变量或测试结果。
- 关键改动必须运行 `docs/codex/project-context.md` 记录的相关验证命令。
- 不把 API key、token、账号密码写入代码、文档、测试或提交。
- 每轮结束必须更新 `docs/codex/current-task.md`、`docs/codex/known-issues.md`、`docs/codex/worklog.md`。
