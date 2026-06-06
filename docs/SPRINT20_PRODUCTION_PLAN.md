# Sprint20 生产闭环验证计划

## 0. 当前仓库基线

本计划基于 Sprint1 到 Sprint19 已完成能力进行评估，不包含代码开发。

已具备的关键基础：

- `STYLE_CODE` 风格复用链路。
- Ofox/OpenAI 兼容真实生成链路。
- `resource_production` 输出模式。
- `996-ready` 包结构。
- `manifest.json`、`annotation.json`、`candidate_manifest.json`。
- `delivery_report`、`candidate_preview`、`component_quality_report`。
- `scripts/validate_996_export.py` validator。
- `/studio` Production Studio 工作台。
- 本地启动、环境检查、结果中心、人工验收状态。
- Sprint19 固定传奇手游布局模板、参考图上传、提示词可视化、完整图预览。

当前状态已经达到“可以生成、可以看、可以验收记录、可以跑 validator”的阶段，但还没有达到“生成后可以直接交给 996 项目使用”的阶段。

## 1. 当前界面生成能力距离生产可用还差什么

### 已有能力

- 可以生成真实 `ui_preview.png`。
- 可以按 `STYLE_CODE` 复用风格。
- 可以生成 `main_ui`、`role_ui`、`bag_ui`、`shop_ui`、`activity_ui`。
- Sprint19 已把主界面生成约束到传奇手游固定布局：
  - 左下摇杆区
  - 右下环绕式技能操作区
  - 右上小地图区
  - 顶部信息区
  - 底部状态信息区
  - 右侧系统入口区
  - 左下聊天区

### 主要差距

1. 布局稳定性还没有形成可量化验收。

   当前提示词要求固定布局，但系统还没有自动检查：

   - 摇杆是否在左下。
   - 技能区是否在右下。
   - 技能按钮是否为环绕/扇形，而不是竖排。
   - 小地图是否在右上。
   - 中央战斗区是否被遮挡。

2. AI 仍可能把“风格变化”误解为“布局变化”。

   Sprint19 已降低风险，但目前主要依赖提示词约束。缺少生成后布局检查和人工验收表单的结构化判断。

3. 参考图只是路径和提示词参考，不等于真正的图像约束。

   当前链路已经支持上传参考图并传路径，但真实模型调用是否使用参考图像素，需要继续确认。现阶段参考图更像“生产上下文记录”和“提示词约束”，不是稳定的 image-to-image 布局锁定。

4. 生成质量缺少首屏生产评分。

   目前 validator 主要验证包结构、字段和文件存在，不判断画面是否符合传奇手游操作习惯。

### Sprint20 不应做的事

- 不引入 OCR、YOLO、SAM。
- 不做模型训练。
- 不做复杂视觉识别。
- 不改数据库。

Sprint20 更适合做“人工可验收 + 规则化检查”的生产闭环，而不是做智能识别升级。

## 2. 当前组件拆解能力距离生产可用还差什么

### 已有能力

- 可以自动生成 `components/` 切片。
- 可以生成 `candidates/` 候选资源。
- 可以写入 `manifest.json` 和 `annotation.json`。
- 可以生成 `component_quality_report`。
- validator 能检查组件字段、路径、类型、透明字段和质量报告结构。
- Sprint16 的五个包均通过 validator。

### 主要差距

1. 组件拆解仍然偏模板和候选框，不是生产级语义切图。

   当前可以稳定产出若干大区域和候选资源，但还不能保证：

   - 每一个按钮都被单独切出。
   - 每一个图标都有明确语义名称。
   - 每一个面板、边框、标签、输入框都被完整拆解。
   - 主攻击键、技能键、背包、角色、商城、活动等关键入口都被正确命名。

2. `common_icons` 仍是已知短板。

   Sprint16 报告已经指出，常用图标仍需要人工处理或后续规则提升。对 996 生产来说，图标语义命名比“有一张候选切片”更重要。

3. 缺少人工确认后的回写机制。

   `/studio` 目前能记录人工验收状态和笔记，但这些记录还停留在前端状态，不会写回包内 JSON。生产闭环需要把人工决定沉淀为文件：

   - 哪些候选资源保留。
   - 哪些候选资源忽略。
   - 哪些组件需要重切。
   - 哪些组件需要透明处理。

4. 缺少“切图计划”汇总。

   用户贴出的共享目录扫描脚本方向是对的：生产阶段需要一个 `component_review_analysis.json` 或类似文件，把 manifest、candidate、annotation 汇总成可人工检查的切图计划。

### Sprint20 应聚焦的拆解目标

不要追求一次性智能拆完全部 UI。最小目标应是：

- 从现有 `manifest`、`annotation`、`candidate_manifest` 中生成一个人工切图清单。
- 对关键组件进行 A/B/C 分级。
- 明确哪些资源可交付、哪些需要人工重切、哪些忽略。

## 3. 当前透明资源能力距离生产可用还差什么

### 已有能力

- Sprint10B 已定义透明资源元数据规范。
- `manifest` 和 `annotation` 支持 `transparent` 字段。
- validator 能检查透明字段合法性。
- `resource_production` 已记录透明策略：
  - `button`
  - `icon`
  - `frame`
  - `input`

### 主要差距

1. 当前透明能力仍是 metadata-only。

   文档已经明确：当前不会自动生成最终透明 PNG。`transparent.required = true` 表示生产要求，不代表图片已经干净透明。

2. 切片文件多为矩形裁剪。

   对按钮、图标、边框来说，矩形裁剪通常包含背景或邻近 UI 内容。直接交给 996 使用会遇到：

   - 背景残留。
   - 边缘不干净。
   - Alpha 不正确。
   - 无法叠加到其他界面。

3. 缺少透明验证报告。

   validator 目前验证字段，不验证真实像素级 Alpha 质量。生产上至少需要一个轻量检查：

   - PNG 是否有 alpha 通道。
   - 透明区域比例是否合理。
   - required 透明组件是否仍全不透明。

4. 缺少“透明处理状态”。

   当前有 `transparent.status`，但缺少面向验收人员的状态流：

   - 待处理
   - 已人工处理
   - 透明验证通过
   - 透明验证失败

### Sprint20 应聚焦的透明目标

Sprint20 不应做自动抠图或复杂透明化。最小目标是：

- 对现有切片做透明可用性扫描。
- 生成透明检查报告。
- 把每个关键资源标记为“可直接用 / 需透明处理 / 暂不处理”。

## 4. 当前 Production Studio 流程距离生产可用还差什么

### 已有能力

- 用户可以打开 `/studio`。
- 可以选择设备、输出模式、风格来源、界面类型、布局模板、生成模式。
- 可以上传参考图。
- 可以编辑提示词。
- 可以看到结果中心。
- 可以看到完整图预览、验证状态、报告入口、资源入口。
- 可以记录人工验收状态和备注。
- 本地启动脚本和环境检查脚本已存在。

### 主要差距

1. 失败原因仍然过于粗。

   前端目前把很多失败都收敛成“本地工作台还没有准备好”。这适合小白用户，但对生产闭环不够。需要在不暴露日志的前提下区分：

   - 后端不可用。
   - provider 不健康。
   - 请求字段错误。
   - 模型额度/请求失败。
   - 生成成功但 validator 失败。

2. 人工验收状态没有持久化。

   当前人工验收记录在页面状态里，刷新后会丢。生产闭环需要写入包内文件，例如：

   - `manual_acceptance.json`
   - 或更新 `delivery_report.json`

   但 Sprint20 如果坚持不改数据库，可以只写文件，不改 DB。

3. 缺少“生产闭环总览”。

   用户不应该自己去目录里找：

   - 哪些图已生成。
   - 哪些通过 validator。
   - 哪些组件需要重切。
   - 哪些透明资源不合格。
   - 哪些待人工验收。

4. 结果中心还没有“验收导出”。

   生产验收需要一个稳定文件给后续人员继续处理，而不只是页面显示。

5. 本地端口和前端 API 地址仍需彻底固化。

   Sprint17B/Sprint18B 规定后端为 `8001`、前端为 `3001`。如果前端默认地址仍可能落到 `8000`，会造成用户点击生成失败。Sprint20 前需要把本地默认地址和启动脚本行为作为前置检查项。

## 5. Sprint20 最小可落地方案

Sprint20 的目标应定义为：

> 不增强 AI，不引入新模型，不做智能识别；把一次真实生成结果转成可人工验收、可交接、可继续切图处理的生产闭环包。

### P0：生产闭环报告文件

新增一个本地文件级产物，例如：

```text
production_review.json
```

每次对一个 `996-ready` 包执行生产检查时，输出：

- package path
- style_code
- screen_type
- generation_job_id
- validator result
- ui_preview path
- component count
- candidate count
- transparent scan summary
- manual cut plan
- acceptance status
- blocking issues

### P0：组件审查清单

基于现有：

- `manifest.json`
- `annotation.json`
- `candidate_manifest.json`
- `component_quality_report.json`

生成：

```text
component_review_analysis.json
```

建议结构：

```json
{
  "package_dir": "...",
  "ui_preview": "...",
  "validator_ok": true,
  "cut_plan": [
    {
      "component_id": "primary_action_button",
      "component_name": "主攻击键",
      "component_type": "button",
      "level": "A",
      "recommended_action": "keep_or_recrop",
      "reason": "核心操作按钮，必须可复用",
      "bounds": { "x": 0, "y": 0, "width": 0, "height": 0 },
      "transparent_required": true,
      "transparent_ready": false
    }
  ]
}
```

分级建议：

- A：必须生产可用，影响 996 接入。
- B：建议可用，影响效率和完整度。
- C：可忽略或仅作为参考。

### P0：透明资源扫描

只做轻量像素检查，不做抠图：

- PNG 是否存在。
- 是否 RGBA。
- 是否存在 alpha 通道。
- alpha 是否全 255。
- required 透明组件是否标记为 `unverified`。

输出：

- `transparent_ready_count`
- `transparent_required_count`
- `transparent_blockers`

### P1：Production Studio 结果中心接入报告入口

在不改数据库的前提下，后续可以让结果中心显示：

- 生产闭环报告
- 组件审查清单
- 透明扫描结果

但 Sprint20 最小方案可以先只生成文件和文档，不强求 UI 深度改造。

### P1：人工验收文件化

新增包内文件：

```text
manual_acceptance.json
```

记录：

- `pending`
- `approved`
- `needs_change`
- reviewer notes
- updated_at

不改数据库。

### 本 Sprint 不做

- 不做 OCR。
- 不做 YOLO。
- 不做 SAM。
- 不训练模型。
- 不做 ZIP。
- 不做云部署。
- 不做用户系统。
- 不改数据库。

## 6. Sprint20 开发顺序

### Step 1：冻结生产闭环验收口径

先定义通过标准：

- `ui_preview.png` 存在且尺寸正确。
- validator PASS。
- `manifest`、`annotation`、`candidate_manifest` 存在。
- 至少生成组件审查清单。
- 至少生成透明扫描结果。
- 至少生成人工验收文件。

验收输出：

- 更新或新增文档。
- 不改运行链路。

### Step 2：新增离线分析脚本

新增脚本建议：

```text
scripts/analyze_production_package.py
```

输入：

```text
--package-dir assets/uploads/996-ready/STYLE_0004/main_ui/...
```

输出到包内：

```text
component_review_analysis.json
production_review.json
```

脚本只读现有包并写分析文件，不调用模型。

### Step 3：加入透明扫描

在同一脚本中读取 `components/*.png` 和 `candidates/*.png`：

- 检查图片模式。
- 检查 alpha。
- 汇总阻断项。

不修改图片。

### Step 4：补 validator 或单独检查命令

两种方案：

- 保守方案：先不改 validator，只让分析脚本输出生产报告。
- 进阶方案：validator 增加可选检查，发现 `production_review.json` 时验证字段结构。

推荐 Sprint20 采用保守方案，避免扩大 validator 责任。

### Step 5：把分析接入 `/studio` 生成后流程

生成完成后自动跑分析脚本或后端函数，结果中心显示：

- 生产检查通过/需要处理。
- A 级组件数量。
- 透明阻断数量。
- 查看生产报告。

仍然不改数据库。

### Step 6：人工验收文件化

把页面里的验收状态和备注写入包内：

```text
manual_acceptance.json
```

可以先做单包文件写入，不做多用户协作。

### Step 7：用一个真实包跑完整闭环

建议以当前真实生成包作为 Sprint20 样例：

```text
STYLE_0004/main_ui/be45d132dcaf4cdbb41659fc52504bb1
```

如果要评估更多样本，再加入 `STYLE_0003` 五屏包。

最终验收：

- 能打开 `/studio`。
- 能看到生成结果。
- 能生成生产审查报告。
- 能看到 A/B/C 组件清单。
- 能看到透明阻断项。
- 能写入人工验收文件。
- 不需要用户手动翻目录判断生产状态。

## 7. Sprint20 推荐范围

推荐 Sprint20 只做一个最小闭环：

1. 离线分析一个 `996-ready` 包。
2. 生成 `component_review_analysis.json`。
3. 生成 `production_review.json`。
4. 扫描透明状态但不处理图片。
5. 在 `/studio` 结果中心展示报告入口。
6. 将人工验收状态写入包内文件。

这样可以把系统从“生成工具”推进到“生产验收工作流”，同时不引入高风险能力。

## 8. Sprint20 完成判定

Sprint20 完成不应以“AI 画得更好”为标准，而应以闭环是否成立为标准：

- 生成结果能被稳定归档。
- 组件可被分级审查。
- 透明问题能被明确暴露。
- 人工验收能留下文件记录。
- 生产人员知道下一步该切什么、修什么、忽略什么。

达到以上标准，即可进入下一轮人工验收和资源精修阶段。
