# 996 Gap Analysis

## 边界

本文档只基于当前系统实际输出分析，不假设未实现能力。

当前已验证输出：

```text
ui_preview
sliced_component
annotation.json
manifest.json
preview.html
```

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

## 当前系统实际输出

### ui_preview

当前 `ui_preview` 是真实 Provider 生成后的整张 UI 图片，资产记录通常为：

- `asset_type = ui_preview`
- `source = ai_generated`
- 绑定 `generation_job_id`
- 文件保存在本地上传目录

它的价值是：

- 作为整图验收依据。
- 作为坐标空间参考。
- 作为后续组件切图输入。
- 在组件缺失时可作为客户端兜底图。

它还不是：

- 996 客户端可直接拆装的资源集合。
- 分层 UI 工程。
- 可独立替换按钮、图标、边框的资源包。

### sliced_component

当前 `sliced_component` 来自 Component Processing 的模板比例裁剪，资产记录通常为：

- `asset_type = sliced_component`
- `source = component_processing`
- 继承源 `ui_preview` 的 `generation_job_id`
- 文件位于 `996-ready/{generation_job_id}/components/`

当前实际能力：

- 能稳定生成 6 个固定区域切片。
- 能证明 `ui_preview -> components/*.png` 链路跑通。
- 能为 manifest 和 annotation 提供文件引用。

当前限制：

- 属于模板切图，不是真正智能组件识别。
- 切片是矩形区域，不保证透明背景。
- 切片粒度偏粗，通常是面板区域，不是按钮、图标、边框、输入框等细组件。
- 不能表达父子层级，例如面板内按钮、按钮内图标。

### annotation.json

当前 `annotation.json` 实际包含：

- `template`
- `source_asset_id`
- `components`
- 每个组件的 `component_id`
- 每个组件的 `component_type`
- 坐标和尺寸
- 默认字体、字号、字体颜色
- 中文展示字段
- 备注

当前价值：

- 能描述每个切片在 `ui_preview` 中的位置。
- 能作为人工复核和后续 schema 标准化基础。
- 能连接组件文件和坐标信息。

当前缺口：

- 字体、字号、颜色是模板默认值，不是从图像中识别得到。
- 缺少明确 `schema_version`。
- 缺少透明 PNG 状态。
- 缺少识别方法和可信度字段。
- 缺少人工复核状态。
- 缺少组件父子关系。

### manifest.json

当前 `manifest.json` 实际包含：

- `template`
- `source_asset_id`
- `ui_preview`
- `components_dir`
- `components`
- 每个组件的 ID、类型、中文名、坐标、尺寸、文件名

当前价值：

- 能索引当前导出目录内的组件文件。
- 能让外部工具知道有哪些切片。
- 能作为 996 客户端读取协议的雏形。

当前缺口：

- manifest 与 annotation 职责边界还未完全固定。
- 路径可能来自当前本地输出方式，未来应统一成相对路径。
- 缺少包级 `schema_version`、`package_type`、`device_type`、`resolution` 等稳定字段。
- 缺少组件透明要求和验证状态。
- 缺少客户端兜底策略说明。

### preview.html

当前 `preview.html` 是人工查看页。

当前价值：

- 可低成本查看组件清单。
- 可辅助人工确认输出目录是否完整。

当前限制：

- 不应作为 996 客户端运行时依赖。
- 不表达完整资源协议。
- 不替代 manifest 和 annotation。

## 距离真正 996 项目资源包的缺口

| 缺口 | 当前状态 | 影响 |
| --- | --- | --- |
| 资源目录标准 | 已有 996-ready 雏形 | 还需要固定路径、命名和相对引用 |
| 组件粒度 | 6 个模板区域 | 不足以支撑按钮、图标、边框、输入框复用 |
| 透明 PNG | 未落地 | 客户端无法稳定叠加和重排 |
| manifest schema | 有基础索引 | 还不能作为稳定客户端契约 |
| annotation schema | 有坐标信息 | 缺少透明、识别方法、复核状态 |
| 资源路径验证 | 过去靠链路验收 | 需要独立脚本验证目录完整性 |
| 客户端读取规则 | 未实现 | 需要先定义读取顺序和失败兜底 |
| 资源组织映射 | 未按 996 目录习惯组织 | 需要和 `res/private`、`res/public`、`item`、`skill_icon` 等资源类型对齐 |
| 生产验收基线 | 无固定样例包 | 需要 fixture 作为回归测试基线 |

## 低风险落地项

Sprint 10R 可以落地的低风险事项：

1. 增加 996-ready 样例包。
2. 增加本地导出验证脚本。
3. 增加差距分析文档。
4. 明确当前切图仍为模板结果。
5. 明确当前透明 PNG 尚未完成。

这些事项不会影响：

- Ofox Provider。
- Real UI Job。
- 数据库结构。
- Component Processing 主流程。
- 已通过的 Sprint 8C 验收链路。

## 结论

当前系统已经具备“生成整图、切出模板组件、写出 JSON 和预览页”的完整链路，但距离真正 996 项目资源包还差三类关键能力：

1. 资源包协议稳定化：目录、路径、manifest、annotation。
2. 资源可组合化：透明 PNG、组件粒度、边界清理。
3. 验证基线化：样例包、验证脚本、回归测试。

Sprint 10R 的合理定位是先补“验证与标准”，而不是升级识别模型或扩展产品系统。
