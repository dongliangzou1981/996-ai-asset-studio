# 996 AI Asset Studio Verified / Confirmed Records

本文件只记录已经确认可用、可复用或已经验证通过的内容。未验证假设、失败实验、工具限制和风险点不要写入本文件。

## 2026-06-09

### Photoshop-style PNG Layer Package 可用于测试
- 日期：2026-06-09
- 模块：Layer Workspace / Photoshop-style Import
- 结论：Photoshop-style PNG Layer Package 流程可作为当前测试输入格式，包结构为 `source.png` + `png_layers/` + `manifest.json`。
- 证据：用户已确认该流程可用于测试，并指定为当前项目已确认记录。
- 当前状态：已确认可用。
- 后续建议：未来优先围绕 Layer Package Import 做验证和集成测试。

### PNG 图层保持原始画布尺寸和位置
- 日期：2026-06-09
- 模块：PNG Layer Package / 图层定位
- 结论：PNG 图层应保持原始画布尺寸和位置，作为稳定复现 Layer Workspace 的输入约束。
- 证据：用户已确认该规则。
- 当前状态：已确认。
- 后续建议：导入和回归测试中应检查图层画布尺寸、透明区域和定位是否保持一致。

### manifest.json 可作为 Layer Workspace 数据源
- 日期：2026-06-09
- 模块：Layer Workspace / Manifest
- 结论：`manifest.json` 可以作为 Layer Workspace 的数据源。
- 证据：用户已确认该技术路线。
- 当前状态：已确认可用。
- 后续建议：优先让导入流程读取 manifest 中的图层顺序、文件路径、尺寸和定位信息。

### Layer Package Import 优先级
- 日期：2026-06-09
- 模块：Layer Package Import
- 结论：未来优先测试 Layer Package Import。
- 证据：用户已指定该方向为当前项目确认记录。
- 当前状态：已确认的下一步技术路线。
- 后续建议：后续任务优先验证导入路径、前端展示、后端解析和测试样例一致性。
