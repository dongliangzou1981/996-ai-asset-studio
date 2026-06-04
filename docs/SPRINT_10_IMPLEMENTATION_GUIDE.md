# Sprint 10 Implementation Guide

## 边界

本指南基于 Sprint 8C 真实验收、Sprint 9 预研和 Sprint 10R 验证结果制定。

明确不做：

- 用户系统。
- 商业化。
- 运营后台。
- 云部署。
- ZIP 导出。
- 数据库结构修改。
- 组件识别 AI 升级。

目标是高价值研究加低风险落地，优先把当前输出变成可验证、可回归、可逐步生产化的资源包标准。

## 当前事实

当前系统已经跑通：

```text
Prompt
-> Ofox Provider
-> Real UI Job
-> ui_preview
-> Component Processing
-> sliced_component
-> annotation.json
-> manifest.json
-> preview.html
```

当前实际能力：

- 能生成整张 `ui_preview`。
- 能生成 6 个模板 `sliced_component`。
- 能生成 `annotation.json`。
- 能生成 `manifest.json`。
- 能生成 `preview.html`。

当前实际限制：

- 当前属于模板切图。
- 当前不是智能组件识别。
- 当前透明 PNG 标准尚未落地。
- 当前 996 导出规范尚未被独立验证。

## Sprint 10 推荐实施顺序

### P0：996 导出验证基线

目标：

先确认一个输出目录是否能被认为是合格 996-ready 包。

建议实施：

- 保留 `tests/fixtures/996_ready_demo/` 作为标准样例包。
- 使用 `scripts/validate_996_export.py` 验证 manifest、annotation、preview、资源路径和组件文件。
- 把验证脚本纳入后续回归检查。

验收标准：

- 样例包验证通过。
- 缺失组件时验证失败并给出明确错误。
- 验证脚本只读本地文件，不依赖数据库和后端服务。

### P1：996-ready schema 固化

目标：

把 manifest 和 annotation 从“当前能写出的 JSON”固化为后续客户端可消费的协议。

建议实施：

- 固定 `manifest.schema_version`。
- 固定 `manifest.package_type = 996-ready`。
- 固定 `manifest.ui_preview` 和 `manifest.components[].file` 使用相对路径。
- 固定 `annotation.coordinate_space = ui_preview_pixels`。
- 固定 `annotation.components[].bounds`。
- 固定 `annotation.components[].image`。

验收标准：

- 新输出与 fixture 字段方向一致。
- 路径不包含盘符、本机用户名或绝对路径。
- manifest 负责索引，annotation 负责标注，不混用职责。

### P2：透明 PNG 状态标注

目标：

先在协议里表达透明需求和验证状态，再做实际透明化处理。

建议实施：

- 在 manifest component 中表达 `transparent_png_required`。
- 在 manifest component 中表达 `transparent_png_verified`。
- 在 annotation image 中表达 `color_mode`、`alpha`、`transparent_background`。
- 当前模板切图如果未透明化，应明确标记为未验证。

验收标准：

- 必须透明和允许整图的组件能被 JSON 区分。
- 客户端或人工流程能知道哪些资产不能直接作为透明组件使用。

## Sprint 11 推荐实施顺序

### P0：组件类型体系扩展

目标：

让输出从 6 个粗区域逐步过渡到生产组件类型。

建议组件类型：

```text
panel
bar
button
icon
slot
tab
badge
progress
input
border
background
text
unknown
```

验收标准：

- manifest 和 annotation 支持上述类型。
- 当前模板区域可继续输出，不破坏 Sprint 8C 链路。
- 新类型先服务手工标注和验证，不强行要求自动识别。

### P1：资源族组织

目标：

对齐传奇项目常见资源目录，让未来 996 客户端接入更自然。

建议资源族：

```text
main
bag_ui
shop
activity
player_main_layer_ui
public
item
skill_icon
```

验收标准：

- manifest 能表达组件所属资源族。
- 样例包能覆盖至少 `main` 和 `bag_ui` 两类。
- 仍保持本地目录输出，不做 ZIP。

### P2：人工复核字段

目标：

把模板切图的不确定性暴露出来，避免误用。

建议字段：

- `recognition.method`
- `recognition.confidence`
- `requires_manual_review`
- `review_status`

验收标准：

- 当前模板结果标记为模板来源。
- 低可信或未透明组件可被复核流程识别。

## Sprint 12 推荐实施顺序

### P0：透明 PNG 质量验证

目标：

从“字段声明”推进到“文件质量可验证”。

建议验证项：

- PNG 是否存在 Alpha 通道。
- 必须透明组件的四角或外部边界是否存在透明像素。
- 文件是否仍是整块不透明矩形。
- 组件文件是否超出合理尺寸。

验收标准：

- 验证脚本能报告透明 PNG 风险。
- 不合格组件不会被误标为已验证。

### P1：样例包扩展

目标：

用更多本地 fixture 覆盖真实 UI 结构，不依赖外部服务。

建议样例：

- 主界面样例。
- 背包样例。
- 商城样例。
- 活动样例。
- 角色面板样例。

验收标准：

- 每个样例包都能通过验证脚本。
- 每个样例包覆盖不同组件类型。
- 样例仍是本地测试基线，不进入业务数据库。

### P2：客户端消费协议草案

目标：

为后续 996 客户端接入准备最小读取协议。

建议读取顺序：

```text
manifest.json
-> ui_preview.png
-> manifest.components[].file
-> annotation.components[].bounds
-> annotation.components[].image
```

验收标准：

- 客户端读取协议仍基于本地目录。
- 组件缺失时可回退 `ui_preview.png`。
- 不依赖 `preview.html`。

## 总体建议

Sprint 10 先做验证基线和 schema 固化，Sprint 11 做组件类型和资源族组织，Sprint 12 再做透明 PNG 质量验证和更多样例包。

推荐节奏：

1. 先让包能被验证。
2. 再让包能被稳定理解。
3. 最后让组件逐步接近真实生产可用。

这条路线能保护 Sprint 8C 已通过链路，同时把未来生产效率提升落在低风险、可回归的基础设施上。
