# 996 Pipeline Integration

## 背景与边界

本文档是 Sprint 9 预研分析，描述从 AI 生成到 996 客户端使用的完整生产流程，并指出缺失环节和未来优化方向。

本阶段不实现代码、不修改数据库、不做 ZIP、不做云部署、不做运营后台、不做用户系统。

## 当前已验证链路

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

这条链路已经证明：

- 真实 Provider 能进入统一 Job Runner。
- Ofox 能作为 OpenAI Compatible 图片生成入口。
- 生成图能保存为 `ai_generated` 来源的 `ui_preview`。
- `ui_preview` 能触发 Component Processing。
- Component Processing 能写出组件 PNG、manifest、annotation、preview。
- 结果资产能通过现有 job/result 和 assets 流程被追踪。

## 完整生产流程

目标生产流程：

```text
AI 生成
-> 切图
-> 标注
-> 996 客户端使用
```

展开后建议定义为：

```text
1. 输入 Prompt
2. 选择 Provider
3. 创建 Real UI Job
4. Provider 生成 UI 图片
5. 保存 ui_preview
6. 执行组件识别
7. 生成组件切片
8. 透明 PNG 标准化
9. 生成 annotation.json
10. 生成 manifest.json
11. 人工预览 preview.html
12. 996 客户端读取 manifest
13. 996 客户端加载 components
14. 缺失或失败时回退 ui_preview
```

当前 Sprint 8C 已覆盖 1 到 7、9 到 11 的基础链路。第 8 步透明 PNG 标准化、第 12 到 14 步客户端消费协议仍处于预研阶段。

## AI 生成阶段

当前输入：

- `project_id`
- `provider_id`
- `job_type = real_ui_generation`
- `prompt`
- `device_type`
- `width`
- `height`
- 可选 `style_profile_id`
- 可选 `base_panel_id`
- 可选 `reference_image_id`

当前输出：

- `ui_preview` asset
- `source = ai_generated`
- `generation_job_id`
- `output_preview_path`
- `output_json.component_processing`

当前优势：

- Provider API Key 不入库，只通过环境变量读取。
- Ofox 使用 `base_url` 和 `model` 非秘密配置。
- 生成失败会进入 job `failed` 状态。
- 生成成功后自动进入组件处理。

当前缺失：

- Prompt 与 996 组件需求之间还没有稳定模板。
- 生成图是否符合透明切图目标没有前置约束。
- 没有对生成图进行质量评分。
- 没有对 UI 密度、按钮可切性、图标独立性做检查。

未来优化方向：

- 在 Prompt 模板中明确“组件边界清晰、按钮独立、图标不要与背景粘连”。
- 为不同设备和 UI 类型建立 Prompt 模板。
- 在 AI 生成后增加轻量质量检查，但不阻塞已通过链路。

## 切图阶段

当前切图方式：

- 从 `ui_preview.file_path` 读取整图。
- 转为 RGBA。
- 按固定比例裁剪 6 个区域。
- 写入 `components/{component_id}.png`。
- 生成 `sliced_component` asset。

当前优势：

- 稳定。
- 可重复。
- 不依赖外部模型。
- 能满足 E2E 链路验收。

当前缺失：

- 不是真实组件识别。
- 不会识别按钮、图标、输入框、边框。
- 不会去背景。
- 不会处理透明 Alpha。
- 不会生成父子层级。

未来优化方向：

- 先把模板切图结果标记为 `method = template`。
- 增加 `transparent_png_verified` 和 `requires_manual_review` 标识。
- 逐步加入视觉启发式检测。
- 保留模板规则作为兜底。

## 标注阶段

当前标注输出：

```text
annotation.json
manifest.json
preview.html
```

当前 annotation 包含：

- `component_id`
- `component_type`
- 坐标和尺寸
- 字体、字号、字体颜色
- 备注
- 中文展示字段

当前 manifest 包含：

- `template`
- `source_asset_id`
- `ui_preview`
- `components_dir`
- 组件列表

当前优势：

- 标注与文件产物已成体系。
- 中文展示字段已进入输出。
- 组件 asset 与 generation job 关联。

当前缺失：

- manifest 与 annotation 职责边界还不够清晰。
- 字体、字号、颜色目前是默认值，不是识别值。
- 缺少 schema_version。
- 缺少相对路径标准。
- 缺少透明 PNG 状态。
- 缺少识别方法和置信度。

未来优化方向：

- manifest 只负责包级索引。
- annotation 负责坐标、样式、透明、识别方法和人工复核信息。
- 所有客户端资源路径标准化为相对路径。
- 增加 schema version，避免后续客户端无法兼容。

## 996 客户端使用阶段

建议客户端读取顺序：

```text
读取 manifest.json
-> 定位 ui_preview.png
-> 遍历 manifest.components
-> 加载 components/*.png
-> 读取 annotation.json 获取坐标和样式
-> 组件缺失时回退 ui_preview.png
```

建议客户端不要依赖：

- 本机绝对路径。
- 后端数据库 ID 作为文件路径。
- `preview.html`。
- 未声明透明状态的组件。

建议 996 客户端最小消费协议：

- `manifest.schema_version`
- `manifest.ui_preview`
- `manifest.components[].component_id`
- `manifest.components[].component_type`
- `manifest.components[].file`
- `annotation.components[].bounds`
- `annotation.components[].image.color_mode`
- `annotation.components[].image.alpha`

当前缺失：

- 客户端读取协议尚未形成文档化契约。
- 组件 PNG 透明状态未验证。
- 不同组件类型的客户端组合方式未定义。
- 缺少失败兜底规则。

未来优化方向：

- 先做本地目录读取标准，不做 ZIP。
- 先做透明 PNG 和相对路径标准，不做云部署。
- 先让客户端能消费固定结构，再考虑更复杂的导出形态。

## 缺失环节汇总

| 环节 | 当前状态 | 缺失点 | 建议优先级 |
| --- | --- | --- | --- |
| AI 生成 | 已跑通 | Prompt 未针对可切图优化 | P2 |
| 切图 | 已跑通模板裁剪 | 非智能识别，非透明 PNG | P0 |
| 标注 | 已有 JSON | 缺少 schema、置信度、透明状态 | P0 |
| manifest | 已有基础索引 | 路径和职责需标准化 | P0 |
| 预览 | 已有 preview.html | 仅供人工，不是客户端协议 | P2 |
| 客户端消费 | 未实现 | 缺少读取契约和兜底规则 | P1 |

## Sprint 9 结论

当前最值得保护的是 Sprint 8C 已通过的真实链路。未来优化应以文档和 schema 约定先行，逐步把“能输出”推进到“996 客户端能稳定消费”。

推荐顺序：

1. 透明 PNG 标准化。
2. 996 导出标准化。
3. 组件识别准确率提升。

这个顺序能最大化利用当前已跑通的 Ofox E2E，同时避免在识别能力还不稳定时提前扩展 ZIP、云平台、后台或用户体系。
