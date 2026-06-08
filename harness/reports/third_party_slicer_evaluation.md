# Sprint21A 第三方切图/分层工具可用性验证报告

日期：2026-06-09
分支：sprint20b-main-ui-production-chain

## 验证边界

本轮只做第三方工具可用性验证与开源工具搜寻，不接入 Studio，不修改现有生成、标记、切图主流程，不开发 PSD，不修改提示词。

本地轻量验证结果：

- 当前仓库内无既有 `game-auto-slicer`、`uislicer`、`UIED`、`vulca`、`third_party_slicer` 相关代码。
- 后端虚拟环境 Python 可用，Pillow 可用。
- 本地 `cv2` 未安装：自研 OpenCV 方案需要新增 `opencv-python` 或 `opencv-python-headless` 依赖后才能运行。

## 996 Layer Workspace 目标格式

第三方工具若要进入 996 UI Asset Studio，建议统一转换为以下中间层格式，而不是直接耦合工具原始输出：

```json
{
  "source_image": "original.png",
  "workspace_id": "main_ui_candidate_001",
  "layers": [
    {
      "layer_id": "skill_001",
      "component_type": "skill",
      "level": "A",
      "layout_zone": "bottom_right_skill_area",
      "shape_type": "circle",
      "bbox": [1420, 760, 108, 108],
      "outline_points": [[1474, 760], [1528, 814], [1474, 868], [1420, 814]],
      "mask_path": "masks/skill_001.png",
      "slice_path": "slices/skill_001.png",
      "confidence": 0.82,
      "source_tool": "third_party_tool_name"
    }
  ],
  "warnings": []
}
```

## 总结矩阵

| 工具 | 公开可访问性 | 星标/热度 | 安装/运行验证 | GPU/CUDA | 主要输入 | 主要输出 | 转 Layer Workspace | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| king-code-9527/game-auto-slicer | 未找到稳定公开仓库入口 | 不可记录 | 未运行，无法验证源码和 CLI | 未知 | 未知 | 未知 | 暂不可评估 | 不推荐 |
| bigFayer/uislicer | 未找到稳定公开仓库入口 | 不可记录 | 未运行，无法验证源码和 CLI | 未知 | 未知 | 未知 | 暂不可评估 | 不推荐 |
| MulongXie/UIED | 公开仓库可访问 | 约 544 stars | 未本地安装；可按 Python/OpenCV 工具链研究 | 通常不强制，取决于检测模式 | GUI/UI 截图 PNG/JPG | UI element bbox、组件检测结果、可视化图 | bbox 可转，语义类型需二次映射 | 可研究 |
| vulca-org/vulca | PyPI 包与 GitHub 项目链接可见 | GitHub stars 未读取 | 未本地安装；偏创意生成/语义分层 SDK | 取决于 provider/SAM extras | 图片资产 | semantic layers、mask、manifest 类产物 | 可研究，但需强适配 | 可研究/非近期 |
| 自研 OpenCV 方案 | 本地可控 | OpenCV 约 87.7k stars | 当前缺 `cv2`，依赖补齐后可直接运行 | 不需要 | PNG/JPG/UI 大图 | contour、bbox、mask、preview | 最容易直接产出目标 JSON | 推荐 |

## 指定工具评估

### king-code-9527/game-auto-slicer

- 仓库：`https://github.com/king-code-9527/game-auto-slicer`
- 公开检索结果：未能确认稳定公开仓库入口或 README。
- 安装方式：无法确认。
- 运行结果：未运行，原因是公开源码和命令入口不可验证。
- 是否需要 GPU/CUDA：无法确认。
- 支持平台：无法确认。
- 支持输入格式：无法确认。
- 输出能力：无法确认是否输出 PNG、JSON、bbox 或 mask。
- 转 Layer Workspace：当前不可评估。
- 风险点：
  - 仓库可访问性不稳定或不存在。
  - 无法确认许可证、依赖、CLI、批处理能力。
  - 无法作为当前 Studio 主链路的可靠依赖。
- 推荐级别：不推荐。除非后续获得可访问源码、许可证和 CLI 文档，否则不建议接入。

### bigFayer/uislicer

- 仓库：`https://github.com/bigFayer/uislicer`
- 公开检索结果：未能确认稳定公开仓库入口或 README。
- 安装方式：无法确认。
- 运行结果：未运行，原因是公开源码和命令入口不可验证。
- 是否需要 GPU/CUDA：无法确认。
- 支持平台：无法确认。
- 支持输入格式：无法确认。
- 输出能力：无法确认是否输出 PNG、JSON、bbox 或 mask。
- 转 Layer Workspace：当前不可评估。
- 风险点：
  - 仓库可访问性不稳定或不存在。
  - 无法确认是否支持游戏 UI 大图、透明切图或组件语义。
  - 接入前无法评估维护风险。
- 推荐级别：不推荐。除非后续拿到可运行仓库，否则不进入接入顺序。

### MulongXie/UIED

- 仓库：`https://github.com/MulongXie/UIED`
- 项目定位：GUI/UI element detection，面向截图中的 UI 组件检测。
- 安装方式：公开资料显示为 Python/OpenCV 相关工具链，可能需要按仓库 README 配置依赖。
- 运行结果：本轮未本地安装运行，原因是当前任务只做验证报告且本地环境没有 OpenCV；未引入新依赖。
- 是否需要 GPU/CUDA：基础图像处理通常不强制 GPU；若使用深度学习模型或 OCR 扩展，则可能需要额外模型依赖。
- 支持平台：理论上 Python 支持 Windows/macOS/Linux，但需验证依赖版本。
- 支持输入格式：GUI 截图，通常可处理 PNG/JPG。
- 输出能力：适合输出 UI element bbox、检测可视化结果；组件类型语义对 996 游戏主界面仍需二次映射。
- 转 Layer Workspace：
  - bbox 可直接映射到 `bbox`。
  - 检测类别需映射到 `background/panel/button/icon/skill`。
  - 非矩形组件、圆形技能按钮需要额外轮廓或 mask 后处理。
- 风险点：
  - 原项目偏通用 GUI，不是游戏 UI 专用。
  - 可能把纹饰、文字、按钮边框拆得过碎。
  - 对技能区、摇杆、小地图等游戏语义需要规则补强。
- 推荐级别：可研究。适合作为标记候选生成器或对照工具，不建议直接替代现有标记主流程。

### vulca-org/vulca

- 仓库：`https://github.com/vulca-org/vulca`
- PyPI：`https://pypi.org/project/vulca/`
- 项目定位：agent-native cultural art SDK，覆盖图像生成、语义分层、mask、layer editing、评估和归档，不是专门的游戏 UI 切图器。
- 安装方式：`pip install vulca`，要求 Python >= 3.10，并按需要启用 `layers`、`sam`、`sam3` 等 extras。
- 运行结果：未本地安装运行，原因是该项目依赖面较宽，且本轮只做验证报告。
- 是否需要 GPU/CUDA：核心 SDK 不一定强制，但启用 SAM/SAM3、本地图像模型或 ComfyUI/Ollama provider 时可能需要更高硬件资源。
- 支持平台：Python 3.10+，理论上多平台；Windows 仍需单独验证 provider 和模型依赖。
- 支持输入格式：图片资产，具体格式需按 layer/decompose 工具确认。
- 输出能力：公开说明中包含 semantic layers、mask、manifest 类产物，可能可用于分层研究。
- 转 Layer Workspace：有研究价值，但需要把语义层转换为 996 的 `background/panel/button/icon/skill` 等游戏 UI 组件语义。
- 风险点：
  - 项目偏创意图像语义分层，不是按钮/面板/技能区级别的 UI slicer。
  - 引入 provider、模型、MCP 或外部运行时后链路会变重。
  - 语义层可能太粗，不能直接满足游戏 UI 细颗粒度切图。
- 推荐级别：可研究/非近期。可作为语义 mask 与 layer manifest 参考，不建议放入近期主链路。

### 自研 OpenCV 方案

- 方案定位：基于 OpenCV 的边缘、轮廓、形态学、连通域、模板/颜色规则，生成候选 bbox、outline、mask 和切图。
- 本地验证：
  - Python 可用。
  - Pillow 可用。
  - `cv2` 当前未安装。
- 安装方式建议：
  - 后端无 GUI 环境优先使用 `opencv-python-headless`。
  - 若需要本地可视化调试，可使用 `opencv-python`。
- 是否需要 GPU/CUDA：不需要。
- 支持平台：Windows/macOS/Linux 均可，取决于 Python wheel。
- 支持输入格式：PNG/JPG/UI 大图。
- 输出能力：
  - bbox：可直接输出。
  - mask：可通过阈值、轮廓填充、GrabCut 或分水岭生成。
  - PNG/JPG：可直接切图输出。
  - JSON：可完全按 Studio candidate_manifest / Layer Workspace 格式输出。
- 转 Layer Workspace：最直接，可从一开始按目标 schema 输出。
- 风险点：
  - 对复杂纹饰和半透明光效容易误切。
  - 需要结合固定布局区域规则，否则会把背景纹理拆成大量噪声组件。
  - 组件语义分类需要规则或后续模型辅助。
- 推荐级别：推荐。适合先做稳定 baseline，再用 UIED/SAM/检测模型补强。

## GitHub 开源候选工具

| 仓库 | Stars | License | 类型 | 依赖/平台 | 输出能力 | 适用性 | 风险 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `microsoft/OmniParser` | 约 24.2k | CC-BY-4.0；部分模型权重另有许可 | 屏幕解析、UI 元素理解 | Python，模型权重，Windows/macOS/Linux 需验证 | UI 元素框、语义描述、可视化 | 可研究 | 模型依赖重，部分权重有 AGPL 继承风险，可能偏桌面/网页 UI |
| `facebookresearch/segment-anything` | 约 53k-54k | Apache-2.0 | 通用分割/mask | Python/PyTorch，CPU 可跑但 GPU 更实际 | mask、轮廓、区域 | 可研究 | 无组件语义，需 prompt/box 引导，批处理成本高 |
| `ultralytics/ultralytics` | 约 57.7k-58k | AGPL-3.0 或企业许可 | YOLO 检测/分割训练框架 | Python/PyTorch，多平台；GPU 推荐 | bbox、mask、分类 | 可研究 | 许可证和训练数据成本需评估；不是开箱即用 UI slicer |
| `open-mmlab/mmdetection` | 约 32.7k | Apache-2.0 | 检测/实例分割框架 | Python/PyTorch，多平台；GPU 推荐 | bbox、mask、分类 | 可研究 | 工程较重，需要训练集和模型管理 |
| `opencv/opencv` | 约 87.7k | Apache-2.0 | 计算机视觉基础库 | C++/Python，多平台 | contour、bbox、mask、图像处理 | 推荐 | 无语义，需要规则层；复杂 UI 需调参 |
| `MulongXie/UIED` | 约 544 | Apache-2.0 | GUI 元素检测 | Python 3.5、OpenCV 3.4.2、Pandas；多平台需验证 | GUI element bbox、JSON、preview | 可研究 | 通用 GUI 语义与游戏 UI 有差距，Google OCR/Paddle OCR 路径需验证 |

## 对 996 UI Asset Studio 的接入建议

### 推荐接入顺序

1. 自研 OpenCV baseline
   - 先按固定主界面布局区域做候选生成。
   - 输出 bbox、outline_points、mask、candidate_preview、Layer Workspace JSON。
   - 不依赖 GPU，最容易在 Windows 本地和 CI 中稳定运行。

2. UIED 作为候选补充/对照工具
   - 用于补充按钮、面板、图标的候选框。
   - 与自研规则做交叉验证，低置信度结果进入人工确认。

3. Segment Anything / OmniParser 作为研究增强
   - SAM 用于复杂非矩形 mask。
   - OmniParser 用于语义辅助，但不作为主链路依赖。

4. YOLO / MMDetection 训练型方案
   - 在 `training_samples/main_ui` 样本积累足够后再考虑。
   - 适合长期提升 skill/icon/button/panel 分类精度。

5. game-auto-slicer / uislicer
   - 当前不进入接入计划。
   - 只有在源码、许可证、CLI、批处理、输出格式全部确认后再重新评估。

6. Vulca
   - 作为语义分层/manifest 思路参考单独研究。
   - 不作为近期游戏 UI 自动切图主工具。

### 建议的非侵入式试验方式

- 新增独立 harness 命令，不接入 Studio：
  - 输入：`harness/examples/main_ui/marking_test/original.png`
  - 输出：`harness/examples/main_ui/third_party_probe/<tool>/`
  - 产物：`layers.json`、`candidate_preview.png`、`masks/`、`slices/`
- 对比现有 `marking_acceptance_report.json`：
  - total_marks
  - missing_required
  - bbox 越界/重叠
  - slice 成功率
  - 人工确认 accepted/rejected_reason

### 主要风险

- 许可证风险：训练型框架和工具的许可证必须在正式接入前逐一确认。
- 模型依赖风险：需要权重下载、GPU、CUDA 或 PyTorch 的工具不适合作为默认本地链路。
- 语义错配风险：多数开源工具面向网页/移动 App UI，不理解传奇手游的技能区、摇杆、小地图、聊天区。
- 分层质量风险：bbox 容易满足统计，但真实切图还需要透明 mask、边缘贴合和组件完整性。
- Windows 稳定性风险：部分研究项目安装脚本优先支持 Linux，Windows 需单独验证。

## 结论

当前最适合 996 UI Asset Studio 的路线是：先用自研 OpenCV 建立可控、可批处理、可解释的 Layer Workspace baseline；再引入 UIED/SAM/OmniParser 做候选补充和质量对照；训练型检测框架等待训练样本积累后再进入。指定的 `game-auto-slicer`、`uislicer` 当前无法确认公开可运行源码，不建议接入。`vulca` 有语义分层参考价值，但不是游戏 UI slicer，不建议作为近期主链路依赖。

## 参考来源

- king-code-9527/game-auto-slicer：`https://github.com/king-code-9527/game-auto-slicer`
- bigFayer/uislicer：`https://github.com/bigFayer/uislicer`
- MulongXie/UIED：`https://github.com/MulongXie/UIED`
- Vulca PyPI：`https://pypi.org/project/vulca/`
- microsoft/OmniParser：`https://github.com/microsoft/OmniParser`
- facebookresearch/segment-anything：`https://github.com/facebookresearch/segment-anything`
- ultralytics/ultralytics：`https://github.com/ultralytics/ultralytics`
- open-mmlab/mmdetection：`https://github.com/open-mmlab/mmdetection`
- opencv/opencv：`https://github.com/opencv/opencv`
