# Component Recognition Analysis

## 背景与边界

本文档是 Sprint 9 预研分析，仅分析当前组件识别流程、风险、瓶颈和提升路线图。不实现代码。

当前已验证链路：

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

## 当前组件识别流程分析

当前 Component Processing 并不是智能视觉识别，而是模板比例切图。

流程如下：

```text
ui_preview asset
-> 读取 ui_preview.file_path
-> 打开图片并转为 RGBA
-> 按 COMPONENT_RULES 中的固定比例计算 6 个矩形区域
-> 裁剪 components/{component_id}.png
-> 写入 sliced_component asset
-> 写入 manifest.json
-> 写入 annotation.json
-> 写入 preview.html
```

当前 6 个固定区域：

| component_id | x 比例 | y 比例 | width 比例 | height 比例 | 语义 |
| --- | --- | --- | --- | --- | --- |
| `main_bottom_bar` | 0.00 | 0.82 | 1.00 | 0.18 | 底部主操作栏 |
| `left_status_panel` | 0.00 | 0.00 | 0.24 | 0.22 | 左上状态区域 |
| `right_menu_panel` | 0.76 | 0.00 | 0.24 | 0.35 | 右上菜单区域 |
| `minimap_area` | 0.76 | 0.36 | 0.22 | 0.24 | 小地图区域 |
| `chat_panel` | 0.02 | 0.58 | 0.34 | 0.22 | 聊天区域 |
| `skill_area` | 0.56 | 0.62 | 0.42 | 0.20 | 技能区域 |

当前流程优点：

- 稳定，容易验收。
- 不依赖额外模型或视觉算法。
- 产物链路完整，能生成 manifest、annotation、preview.html。
- 适合验证 `Prompt -> Provider -> Asset -> Component Processing -> Export` 的主流程。

当前流程限制：

- 不能理解 UI 真实布局。
- 不能识别按钮、图标、输入框、边框等细粒度组件。
- 不能判断透明背景。
- 不能处理不同风格、不同构图、不同设备比例下的布局变化。
- 当前 annotation 的字体、字号、颜色是默认模板值，不是从图像中识别得到。

## 误识别风险

误识别指系统把非组件区域当作组件，或把组件类型判断错误。

主要风险：

- 固定区域覆盖了背景、插画或角色，导致输出被误认为 UI 组件。
- `skill_area` 可能覆盖广告素材、底部装饰或非交互元素。
- `chat_panel` 可能覆盖字幕、任务提示、装饰框或空白区域。
- `minimap_area` 可能在没有小地图的画面中误切出背景。
- `right_menu_panel` 可能把奖励图、活动入口、纯装饰角标混为菜单。
- `main_bottom_bar` 可能把底部全宽背景、地面、人物脚部和按钮一起切出。

对 996 客户端的影响：

- 客户端会拿到不可复用的矩形截图。
- 组件透明化难度上升。
- 坐标标注看似完整，但语义不可靠。
- 后续人工修正成本可能高于直接手工切图。

## 漏识别风险

漏识别指系统没有切出真实需要的组件。

主要风险：

- 小按钮没有单独切出。
- 单个技能图标没有单独切出。
- 输入框、边框、弹窗关闭按钮没有单独切出。
- 顶部资源条、头像、红点、徽章等没有单独切出。
- 动态层级组件没有独立记录。
- 同一区域内多个组件被合并成一个大图。

对生产效率的影响：

- 996 客户端无法直接复用单个图标或按钮。
- 后续需要人工二次切分。
- manifest 只能描述粗颗粒区域，无法支撑精细 UI 还原。
- annotation 无法表达组件层级和父子关系。

## 当前瓶颈

当前最大瓶颈不是 Ofox 生成链路，而是 Component Processing 的语义能力。

瓶颈列表：

- 识别方法是固定比例模板，不感知图像内容。
- 组件类型体系较粗，缺少按钮、图标、输入框、边框、文本、背景等分类。
- 缺少父子层级，例如面板内按钮、按钮内图标、输入框内文本。
- 缺少置信度，人工无法判断哪些结果值得信任。
- 缺少透明背景判断，无法区分透明 PNG 和整图裁剪。
- 缺少文本 OCR 或字体检测，当前字体信息是默认值。
- 缺少视觉后处理，例如去背景、裁剪收边、Alpha 检测。
- 缺少人工校准回路，识别错误无法形成下一轮改进数据。

## 提升准确率路线图

### 阶段 1：规则标准化

目标：不引入复杂模型，先把当前模板结果变得可管理。

建议：

- 固定 `component_id`、`component_type`、文件名和坐标字段。
- 在 annotation 中加入 `recognition.method = template`。
- 在 annotation 中加入 `confidence = null` 或 `confidence = 0`。
- 标记 `transparent_png_verified = false`。
- 标记 `requires_manual_review = true`。

价值：

- 让 996 客户端和人工验收知道当前结果的可信边界。
- 为后续智能识别留出兼容字段。

### 阶段 2：组件类型细分

目标：从 6 个大区域过渡到可生产使用的组件类型体系。

建议优先类型：

```text
panel
bar
button
icon
input
border
text
background
decoration
unknown
```

价值：

- 透明 PNG 规范可以按类型执行。
- 996 客户端可以按类型决定布局和兜底策略。
- 人工复核可以按类型过滤。

### 阶段 3：视觉启发式检测

目标：在不改变主链路的前提下提升粗识别准确率。

可预研方向：

- 边缘检测识别矩形面板、按钮和输入框。
- Alpha 或背景色差分析识别可透明区域。
- 连通域分析识别图标和独立装饰件。
- 颜色聚类识别 UI 层与背景层。
- 文本区域检测辅助识别按钮和输入框。

注意：

- 这一阶段仍应保留模板识别作为兜底。
- 不应影响 Sprint 8C Ofox E2E 的通过链路。

### 阶段 4：模型辅助识别

目标：对复杂 UI 使用视觉模型或检测模型输出组件候选。

建议输出不是直接替代切图，而是生成候选：

```json
{
  "component_id": "candidate_001",
  "component_type": "button",
  "bounds": {
    "x": 120,
    "y": 860,
    "width": 180,
    "height": 72
  },
  "recognition": {
    "method": "vision_model",
    "confidence": 0.82
  }
}
```

价值：

- 模型可以识别模板覆盖不到的小组件。
- 置信度可以驱动人工复核优先级。
- 仍可用现有 Component Processing 输出结构承接结果。

### 阶段 5：人工校准闭环

目标：让识别结果能被修正并沉淀为规则或样本。

建议先只做数据标准，不急着做后台：

- annotation 支持 `manual_override` 字段。
- annotation 支持 `review_status` 字段。
- manifest 不保存人工过程，只保存最终可用资源索引。
- 校准数据未来可作为识别准确率评估样本。

## Sprint 9 结论

当前组件识别已经能证明生产链路跑通，但还不能证明组件可直接生产使用。

短期最有价值的改进不是马上上复杂模型，而是先把当前模板识别的可信度、类型、透明状态和人工复核状态写清楚。这样既不破坏 Sprint 8C 链路，又能为 Sprint 10 的透明 PNG 标准化和 996 导出标准化打基础。
