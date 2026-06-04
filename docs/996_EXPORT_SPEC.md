# 996 Export Spec

## 背景与边界

本文档是 Sprint 9 预研文档，仅分析当前 Sprint 8C 已验收输出，并提出后续导出标准化建议。

本阶段不修改核心业务代码、不修改数据库结构、不新增 ZIP、不新增运营后台、不新增用户系统、不做云部署。

已验证链路：

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

## 当前输出结构分析

当前真实 Ofox 路径通过 `real_ui_generation` job 生成 `ai_generated` 来源的 `ui_preview` 资产。`ui_preview` 资产创建后自动进入 Component Processing，生成 6 个 `component_processing` 来源的 `sliced_component` 资产，并输出 `manifest.json`、`annotation.json`、`preview.html`。

当前 Component Processing 输出目录为：

```text
assets/uploads/996-ready/{generation_job_id}/
  ui_preview.png
  components/
    main_bottom_bar.png
    left_status_panel.png
    right_menu_panel.png
    minimap_area.png
    chat_panel.png
    skill_area.png
  manifest.json
  annotation.json
  preview.html
```

当前 mock/unified runner 还存在较早的 `package/manifest.json` 输出形态：

```text
assets/uploads/996-ready/{generation_job_id}/
  previews/
  components/
  thumbnails/
  package/
    manifest.json
```

结论：

- Sprint 8C 真实验收主链路应以 Component Processing 的根目录 `manifest.json`、`annotation.json`、`preview.html` 为准。
- `package/manifest.json` 属于较早 mock/unified runner 结构，后续标准化时应避免让 996 客户端同时依赖两套 manifest。
- 当前 `components/*.png` 是从整张 UI 预览图裁剪出的矩形 PNG，不等同于已经完成透明背景优化的独立透明组件。

## 996-ready 目录规范

建议 Sprint 10 以后将 996-ready 输出目录固定为以下结构：

```text
996-ready/
  ui_preview.png
  components/
    {component_id}.png
  manifest.json
  annotation.json
  preview.html
```

目录职责：

- `ui_preview.png`：整图预览，用于人工验收、坐标校准、客户端兜底展示。
- `components/`：组件切片目录，只存放客户端可直接引用的组件 PNG。
- `manifest.json`：包级索引，描述文件、组件列表、版本、来源和兼容信息。
- `annotation.json`：组件级标注，描述坐标、尺寸、字体、颜色、透明度和识别置信度等信息。
- `preview.html`：人工预览页面，用于低成本检查导出结果，不作为客户端运行时依赖。

建议约束：

- 一个 `generation_job_id` 对应一个 996-ready 输出目录。
- 目录内文件名使用小写英文字母、数字和下划线。
- 路径引用优先使用相对路径，避免客户端消费本机绝对路径。
- `preview.html` 可以引用 `manifest.json` 和组件文件，但客户端正式集成只依赖 JSON 与 PNG。

## 组件命名规范

当前组件 ID：

```text
main_bottom_bar
left_status_panel
right_menu_panel
minimap_area
chat_panel
skill_area
```

建议命名规则：

- `component_id` 使用稳定英文 snake_case。
- 文件名使用 `{component_id}.png`。
- 同一包内 `component_id` 必须唯一。
- `component_type` 表示类别，允许多个组件共享同一类别。
- 中文显示名放入 `component_name_zh`，不进入文件名。
- 坐标含义保持相对于 `ui_preview.png` 左上角的像素坐标。

推荐类型分层：

```text
bar
panel
button
icon
input
border
background
text
unknown
```

当前 6 个模板组件可映射为：

| component_id | 建议 component_type | 用途 |
| --- | --- | --- |
| `main_bottom_bar` | `bar` | 底部主操作栏 |
| `left_status_panel` | `panel` | 左上状态信息区域 |
| `right_menu_panel` | `panel` | 右上菜单区域 |
| `minimap_area` | `panel` | 小地图或导航区域 |
| `chat_panel` | `panel` | 聊天或提示区域 |
| `skill_area` | `panel` | 技能或快捷操作区域 |

## manifest 标准

当前 `manifest.json` 已包含：

- `template`
- `source_asset_id`
- `ui_preview`
- `components_dir`
- `components`

当前单个 component 已包含：

- `component_id`
- `type`
- `component_name_zh`
- 中文组件名字段
- 中文描述字段
- `x`
- `y`
- `width`
- `height`
- `file_name`

建议标准化为：

```json
{
  "schema_version": "1.0",
  "package_type": "996-ready",
  "source_asset_id": "asset-id",
  "generation_job_id": "job-id",
  "device_type": "mobile",
  "resolution": {
    "width": 1024,
    "height": 1024
  },
  "ui_preview": "ui_preview.png",
  "components_dir": "components",
  "components": [
    {
      "component_id": "main_bottom_bar",
      "component_type": "bar",
      "component_name_zh": "主功能栏",
      "file": "components/main_bottom_bar.png",
      "bounds": {
        "x": 0,
        "y": 840,
        "width": 1024,
        "height": 184
      },
      "transparent_png_required": true
    }
  ]
}
```

manifest 的职责应限定为包级索引，不建议把字体、颜色、识别过程、调试日志放入 manifest。此类内容应放在 `annotation.json`。

## annotation 标准

当前 `annotation.json` 已包含：

- `template`
- `source_asset_id`
- `components`
- 每个组件的 `component_id`、`component_type`、坐标、尺寸、字体、字号、字体颜色、备注
- 中文展示字段

建议标准化为：

```json
{
  "schema_version": "1.0",
  "source_asset_id": "asset-id",
  "coordinate_space": "ui_preview_pixels",
  "components": [
    {
      "component_id": "main_bottom_bar",
      "component_type": "bar",
      "component_name_zh": "主功能栏",
      "bounds": {
        "x": 0,
        "y": 840,
        "width": 1024,
        "height": 184
      },
      "style": {
        "font_family": "Microsoft YaHei",
        "font_size": 16,
        "font_color": "#F5D78E"
      },
      "image": {
        "file": "components/main_bottom_bar.png",
        "format": "png",
        "color_mode": "RGBA",
        "alpha": "required"
      },
      "recognition": {
        "method": "template",
        "confidence": null
      },
      "notes": "模板规则切图，尚未进行智能视觉识别"
    }
  ]
}
```

annotation 的职责是服务后续校准、透明化处理、客户端适配和人工复核。它可以比 manifest 更详细。

## 资源引用方式

建议客户端消费时只读取相对路径：

```text
manifest.json
annotation.json
ui_preview.png
components/main_bottom_bar.png
```

不建议客户端依赖：

- Windows 绝对路径。
- 后端上传目录绝对路径。
- 数据库 asset id 作为唯一资源路径。
- `preview.html` 内部结构。

推荐引用优先级：

1. `manifest.components[].file`
2. `annotation.components[].image.file`
3. `ui_preview.png` 兜底

资源路径规则：

- 所有路径以 996-ready 根目录为基准。
- JSON 内路径统一使用 `/`。
- 文件名大小写固定，避免跨平台差异。
- 不把临时目录、开发机用户名、本地盘符写入未来客户端协议。

## 导出规范建议

Sprint 9 预研结论：

- 先统一 996-ready 文件结构，再考虑导出方式。
- 当前不做 ZIP，避免提前引入包管理、下载、权限和失败恢复复杂度。
- 当前不做云部署，路径协议应先满足本地客户端集成。
- 当前不做运营后台，人工验收可继续通过 `preview.html` 和文件目录完成。
- 当前不做数据库变更，标准可以先沉淀在文档中，后续实现时再评估字段落点。

建议 Sprint 10 只做三件事：

1. 固定 `manifest.json` 与 `annotation.json` schema。
2. 固定组件 PNG 透明化要求。
3. 固定 996 客户端读取路径与兜底策略。

短期验收标准建议：

- 每次输出都有 `ui_preview.png`。
- 每次输出都有至少 6 个 `components/*.png`。
- `manifest.json` 可完整索引所有组件文件。
- `annotation.json` 可还原每个组件在整图中的位置。
- 所有 JSON 路径均为相对路径。
- 996 客户端即使某个组件缺失，也能用 `ui_preview.png` 兜底。
