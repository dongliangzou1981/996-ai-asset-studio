# Codex Verified Methods

本文件只记录 Codex / Agent / AI 自动化相关的已验证方法、稳定流程、可复用命令、提示词和成功案例。未验证假设、失败实验和工具限制不要写入本文件。

## 2026-06-09

### 长期记录拆分规则
- 日期：2026-06-09
- 模块：Codex 项目记忆 / 文档维护
- 结论：项目长期记录默认拆分为 confirmed / verified 与 risks / discrepancies 两类文档，避免已验证内容和风险内容混写。
- 证据：用户在本项目中明确指定该文档维护规则。
- 当前状态：已作为本项目后续 Codex 工作流程采用。
- 后续建议：每次任务完成后检查是否有新条目需要分别写入 confirmed 或 risks 文档。

### 本项目专用长期记录文件
- 日期：2026-06-09
- 模块：996 AI Asset Studio / Codex 文档维护
- 结论：本项目使用以下长期记录文件维护知识：`docs/996_studio_verified_confirmed.md`、`docs/996_studio_risks_discrepancies.md`、`docs/codex_verified_methods.md`、`docs/codex_risks_discrepancies.md`。
- 证据：用户要求立即创建或更新这 4 个文件。
- 当前状态：已落地。
- 后续建议：后续项目默认使用 `docs/project_verified_confirmed.md` 和 `docs/project_risks_discrepancies.md`；涉及 Codex / Agent / AI 自动化时额外维护 Codex 两类文档。

### 记录条目字段模板
- 日期：2026-06-09
- 模块：Codex 文档维护
- 结论：每条长期记录尽量包含日期、模块、结论、证据、当前状态和后续建议。
- 证据：用户明确指定该记录字段要求。
- 当前状态：已采用。
- 后续建议：新增条目时保持字段完整；证据不足的内容写入 risks / discrepancies，而不是 confirmed / verified。
