# Legend UI Analysis

## 研究边界

本文档分析传奇类项目常见真实 UI 结构，服务 996-ai-asset-studio 的资源包标准化预研。

本阶段不实现组件识别升级，不引入新的识别模型，不做云部署、不做后台、不做 ZIP。

参考资料：

- [《传奇》游戏界面基本操作界面，新浪游戏](https://games.sina.com.cn/z/cq/2/yxjm/)
- [《传奇永恒》背包系统介绍，盛趣官方](https://actcq.web.sdo.com/project/2015/CqIntro/systemIntro/content.aspx?aid=247751&cid=5908)
- [传奇 996 引擎新手界面引导功能说明](https://www.tayewan.com/article-985-1.html)
- [传奇 996 引擎移动端、客户端资源结构图说明](https://www.tayewan.com/article-927-1.html)
- [Open996 Client GUI framework summary](https://context7.com/shengfeiyue/996m2_client_open_dev)

## 总体结构观察

传奇类 UI 通常不是单一整图，而是由多个高复用资源族组成：

- 主界面 HUD。
- 角色和装备界面。
- 背包与道具格子。
- 商城与充值入口。
- 活动、任务和奖励面板。
- 聊天、小地图、技能栏、快捷菜单。

996 客户端资源结构资料中可以看到资源按用途拆分，例如 `res/private/official/bag_ui`、`main`、`minimap`、`player_main_layer_ui`、`player_skill_layer_ui`、`skill`、`public`、`item`、`skill_icon`、`skill_icon_c` 等。这说明真正可用的项目资源包通常需要按 UI 系统和资源类型组织，而不是只交付一张整图。

## 主界面

### 组件构成

主界面通常包含：

- 角色头像。
- 生命、魔法或状态条。
- 等级、经验、负重等状态提示。
- 小地图入口或小地图区域。
- 聊天区域。
- 技能快捷栏。
- 背包、角色、商城、活动、任务等入口按钮。
- PC 端或移动端右下角快捷按钮组。

996 引擎引导资料中提到主界面 ID、右下角切换按钮、玩家主面板、PC 端下方按钮等概念，说明主界面不是一张静态背景，而是多个可定位、可引导、可绑定事件的 UI 节点组合。

### 资源组织方式

建议资源族：

```text
main/
  bottom_bar/
  status/
  minimap/
  chat/
  shortcut_buttons/
  skill_slots/
```

### 透明资源需求

必须透明：

- 入口图标。
- 技能按钮。
- 快捷按钮。
- 状态条前景。
- 红点、徽章、角标。
- 小地图边框。

允许整图：

- 主界面整图预览。
- 大面积 HUD 背板。
- 聊天背景面板。

## 背包

### 组件构成

背包通常包含：

- 背包主面板。
- 分类页签。
- 道具格子网格。
- 道具图标。
- 锁定格子。
- 负重信息。
- 整理、拆分、使用、出售等按钮。
- 关闭按钮。
- 道具说明弹窗入口。

盛趣官方背包说明中明确背包用于存放道具，支持快捷键和主界面入口打开，并存在格子解锁、负重等机制。Open996 GUI 资料也展示了背包格子、道具显示、PC 鼠标和移动触摸交互的差异。

### 资源组织方式

建议资源族：

```text
bag_ui/
  panel/
  tabs/
  grid/
  item_slots/
  buttons/
  lock_icon/
item/
  item_icons/
```

### 透明资源需求

必须透明：

- 道具图标。
- 锁定图标。
- 格子选中态。
- 按钮。
- 页签前景。
- 关闭按钮。

允许整图：

- 背包主面板底图。
- 大块网格背景。

## 商城

### 组件构成

商城通常包含：

- 商城主面板。
- 分类页签。
- 商品卡片。
- 商品图标。
- 价格标签。
- 货币图标。
- 购买按钮。
- 限购、折扣、推荐角标。
- 关闭按钮。

996 引擎引导资料中把 9-12 视为商城面板相关入口，说明商城可能存在多个页签或子面板。

### 资源组织方式

建议资源族：

```text
shop/
  panel/
  tabs/
  item_cards/
  price/
  currency_icons/
  buttons/
  badges/
```

### 透明资源需求

必须透明：

- 商品图标。
- 货币图标。
- 购买按钮。
- 折扣角标。
- 推荐标识。

允许整图：

- 商城主背景。
- 商品卡片底板。

## 活动

### 组件构成

活动界面通常包含：

- 活动主面板。
- 左侧活动列表。
- 活动 banner。
- 奖励格子。
- 奖励图标。
- 进度条。
- 领取按钮。
- 倒计时或日期标签。
- 红点提示。

### 资源组织方式

建议资源族：

```text
activity/
  panel/
  list_tabs/
  banners/
  reward_slots/
  reward_icons/
  progress/
  buttons/
  badges/
```

### 透明资源需求

必须透明：

- 奖励图标。
- 领取按钮。
- 红点。
- 进度条前景。
- 日期或状态徽章。

允许整图：

- 大 banner。
- 活动主背景。

## 角色面板

### 组件构成

角色面板通常包含：

- 角色主面板。
- 人物内观或模型展示区域。
- 装备槽位。
- 属性列表。
- 战力数值。
- 页签。
- 装备图标。
- 强化、技能、称号等入口按钮。

996 引擎相关资料中存在角色界面、玩家主面板、英雄主面板、人物装备页签、角色内观部件位等概念，说明角色面板需要支持模型展示、装备槽位和多页签结构。

### 资源组织方式

建议资源族：

```text
player_main_layer_ui/
  panel/
  model_area/
  equip_slots/
  attributes/
  tabs/
  buttons/
player_model/
  body_parts/
item/
  equipment_icons/
```

### 透明资源需求

必须透明：

- 装备图标。
- 装备槽边框。
- 页签按钮。
- 强化入口。
- 战力装饰字牌。
- 模型外观部件，如果作为 UI 资源交付。

允许整图：

- 角色面板主底图。
- 模型展示背景。

## 对当前 996-ready 输出的启示

当前系统输出的 6 个模板组件：

```text
main_bottom_bar
left_status_panel
right_menu_panel
minimap_area
chat_panel
skill_area
```

更接近主界面 HUD 的粗区域切片，不足以覆盖背包、商城、活动、角色面板的真实资源组织。

对后续标准的启示：

- `component_type` 需要从 `panel`、`bar` 扩展到 `button`、`icon`、`slot`、`badge`、`tab`、`progress` 等生产类型。
- `manifest.json` 应能表达资源族，例如 `bag_ui`、`shop`、`activity`、`player_main_layer_ui`。
- `annotation.json` 应表达透明需求、复核状态和坐标来源。
- `components/` 目录不应长期只放 6 个大区域，应逐步支持细颗粒资源。

## 结论

真正传奇项目资源包通常按 UI 系统和资源类型组织：主界面、背包、商城、活动、角色面板分别有面板、按钮、图标、格子、页签、状态条和角标等资源。

当前系统已经能生成主界面粗区域切片，但距离真实 996 项目资源包，还需要补齐：

1. 按 UI 系统组织资源。
2. 按组件类型区分透明需求。
3. 提供可验证的 manifest 与 annotation。
4. 先用样例包和验证脚本建立基线，再逐步提高切图粒度。
