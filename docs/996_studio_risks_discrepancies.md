# 996 AI Asset Studio Risks / Discrepancies Records

本文件只记录错误、失败实验、工具限制、技术分歧、未验证假设、风险点、fallback 条件和不建议重复尝试的做法。已经确认可用的内容不要混入本文件。

## 2026-06-09

### Photoshop 工具 nativeImage 报错
- 日期：2026-06-09
- 模块：Photoshop / PSD 或图像处理工具链
- 结论：Photoshop 工具曾出现 `nativeImage must be object` 报错。
- 证据：用户已提供为当前项目风险记录。
- 当前状态：风险已记录，根因未在本次任务中验证。
- 后续建议：再次使用 Photoshop 工具前，先用最小样例复现并确认输入对象结构。

### 原生 PSD 分层尚未验证
- 日期：2026-06-09
- 模块：PSD Import / Layer Workspace
- 结论：当前不能证明原生 PSD 分层已成功，PSD 原生分层仍属于未验证能力。
- 证据：用户已明确“PSD 原生分层尚未验证”和“当前不能证明原生 PSD 分层已成功”。
- 当前状态：未确认。
- 后续建议：不要把 PSD 原生分层作为已完成能力；需要真实 PSD 样例和可重复导入测试后再升级到 confirmed 文档。

### game_ui_layered.psd 仅视为 placeholder_psd
- 日期：2026-06-09
- 模块：PSD 数据源
- 结论：`game_ui_layered.psd` 当前只应视为 `placeholder_psd`，不应依赖它作为真实 PSD 数据源。
- 证据：用户已指定该文件当前视为 placeholder，并列为风险记录。
- 当前状态：风险已确认。
- 后续建议：涉及真实 PSD 数据能力时，必须另行准备可验证的真实分层 PSD 样例。

### OpenCV 自动切图误切风险
- 日期：2026-06-09
- 模块：OpenCV 自动切图 / Fallback Pipeline
- 结论：OpenCV 自动切图保留为 fallback pipeline，但对复杂 UI、半透明阴影、装饰边框存在误切风险。
- 证据：用户已确认 OpenCV 是 fallback，并指出复杂 UI、半透明阴影、装饰边框的误切风险。
- 当前状态：fallback 风险已记录。
- 后续建议：优先测试 Layer Package Import；只有在缺少 Layer Package 数据时再启用 OpenCV fallback，并保留人工检查。
