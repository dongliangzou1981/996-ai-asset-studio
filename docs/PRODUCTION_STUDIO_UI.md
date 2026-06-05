# Production Studio UI

## Purpose

Production Studio is a simple web console for generating 996 UI resource packages without relying mainly on terminal scripts.

It wraps the existing generation pipeline:

```text
STYLE_CODE / prompt
-> real UI generation
-> ui_preview
-> Component Processing
-> components
-> candidates
-> validator
-> 996-ready package
```

This sprint does not add ZIP export, cloud deployment, user systems, commercial admin features, database schema changes, OCR, YOLO, SAM, or model training.

## Page

Open:

```text
/studio
```

The page is intentionally small and production-focused.

## Fields

### Device Type

Supported values:

- `mobile_landscape`
- `pc_landscape`

Default:

- `mobile_landscape`

### Output Mode

Supported values:

- `ui_package`
- `resource_production`

Default:

- `resource_production`

### Style Source

Supported values:

- New style
- Existing `STYLE_CODE`

When using an existing style, the page loads available folders from `style_codes/`, such as:

- `STYLE_0001`
- `STYLE_0002`
- `STYLE_0003`

### Screen Types

Supported checkboxes:

- `main_ui`
- `role_ui`
- `bag_ui`
- `shop_ui`
- `activity_ui`

Default:

- `main_ui`

### Style Name

Example:

```text
暗黑金龙传奇风
```

### Prompt

Example:

```text
手机横屏传奇 UI，暗黑金龙风格，技能栏清晰，右侧菜单明显，整体适合 996 引擎资源生产。
```

## New Style Workflow

When `New style` is selected:

1. The backend generates `main_ui` first.
2. A new `STYLE_CODE` is created from that `main_ui`.
3. Any other selected screens inherit that same `STYLE_CODE`.
4. Each generated screen is summarized and validated.

Even if only a later screen is selected, `main_ui` is still generated first because it is the master style source.

## Existing STYLE_CODE Workflow

When `Existing STYLE_CODE` is selected:

1. The selected `STYLE_CODE` is read from `style_codes/{STYLE_CODE}/style.json`.
2. Each selected screen is generated with that style.
3. The result package is validated and summarized.

## Output

Each screen result shows:

- `STYLE_CODE`
- `screen_type`
- `generation_job_id`
- `ui_preview` thumbnail
- 996-ready path
- `components` count
- `candidates` count
- validator status
- link to `delivery_report.html`
- link to `candidate_preview.html`
- link to `component_quality_report.html`

Each generated package still contains:

- `ui_preview.png`
- `manifest.json`
- `annotation.json`
- `candidate_manifest.json`
- `candidate_preview.html`
- `delivery_report.json`
- `delivery_report.html`
- `component_quality_report.json`
- `component_quality_report.html`
- `components/`
- `candidates/`

## Current Limits

- Small icon semantic naming is still incomplete.
- The page displays whether `common_icons` still need improvement.
- Current slicing is rule-based candidate detection, not full intelligent semantic recognition.
- Resource quality still needs manual acceptance.
- Transparent PNG status is metadata-level until manual or future alpha verification confirms it.

## Compatibility

Production Studio uses the existing script-level functions:

- `run_master_style_workflow`
- `generate_screen_with_style`
- `validate_package`

It does not change database tables or replace the existing Job Center.
