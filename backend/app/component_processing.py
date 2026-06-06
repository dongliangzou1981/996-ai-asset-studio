from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageStat

from app.db import StudioDatabase
from app.schemas import Asset, AssetCreate


COMPONENT_RULES = [
    ("main_bottom_bar", 0.0, 0.82, 1.0, 0.18),
    ("left_status_panel", 0.0, 0.0, 0.24, 0.22),
    ("right_menu_panel", 0.76, 0.0, 0.24, 0.35),
    ("minimap_area", 0.76, 0.36, 0.22, 0.24),
    ("chat_panel", 0.02, 0.58, 0.34, 0.22),
    ("skill_area", 0.56, 0.62, 0.42, 0.2),
]

CANDIDATE_RULES = [
    ("button_candidate", 0.62, 0.82, 0.22, 0.08),
    ("icon_candidate", 0.82, 0.64, 0.1, 0.1),
    ("input_candidate", 0.24, 0.74, 0.4, 0.06),
    ("frame_candidate", 0.2, 0.2, 0.6, 0.54),
    ("tab_candidate", 0.28, 0.12, 0.18, 0.06),
    ("slot_candidate", 0.12, 0.62, 0.07, 0.07),
]

QUALITY_COMPONENT_TYPES = ["button", "icon", "frame", "tab", "slot", "input", "panel", "background"]
SCHEMA_VERSION = "1.0"
PACKAGE_TYPE = "996-ready"
COORDINATE_SPACE = "ui_preview_pixels"
ASSET_MODES = {"ui_package", "resource_production"}
DEFAULT_ASSET_MODE = "ui_package"
DEFAULT_SCREEN_TYPE = "main_ui"
SUPPORTED_SCREEN_TYPES = {"main_ui", "role_ui", "bag_ui", "shop_ui", "activity_ui"}

COMPONENT_TYPE_BY_ID = {
    "main_bottom_bar": "bar",
    "left_status_panel": "panel",
    "right_menu_panel": "panel",
    "minimap_area": "panel",
    "chat_panel": "panel",
    "skill_area": "panel",
}

RESOURCE_CATEGORY_BY_COMPONENT_TYPE = {
    "bar": "layout_bar",
    "panel": "panel_region",
    "button": "button_asset",
    "icon": "icon_asset",
    "frame": "frame_asset",
    "input": "input_asset",
    "slot": "slot_asset",
    "tab": "tab_asset",
    "background": "background_asset",
}

RESOURCE_CATEGORY_BY_CANDIDATE_TYPE = {
    "button_candidate": "button_asset",
    "icon_candidate": "icon_asset",
    "input_candidate": "input_asset",
    "frame_candidate": "frame_asset",
    "tab_candidate": "tab_asset",
    "slot_candidate": "slot_asset",
}

COMPONENT_NAME_ZH = {
    "main_bottom_bar": "主功能栏",
    "left_status_panel": "左侧状态栏",
    "right_menu_panel": "右侧菜单栏",
    "minimap_area": "小地图区域",
    "chat_panel": "聊天区域",
    "skill_area": "技能区域",
}


def normalize_device_type(device_type: str) -> str:
    if device_type == "pc_landscape":
        return "pc_landscape"
    if device_type == "mobile_landscape":
        return "mobile_landscape"
    return "pc" if device_type in {"pc", "desktop"} else "mobile"


def normalize_asset_mode(asset_mode: Any) -> str:
    value = str(asset_mode or DEFAULT_ASSET_MODE)
    return value if value in ASSET_MODES else DEFAULT_ASSET_MODE


def asset_metadata(asset: Asset) -> dict[str, Any]:
    try:
        data = json.loads(asset.metadata_json or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def asset_mode_from_preview(ui_preview: Asset) -> str:
    return normalize_asset_mode(asset_metadata(ui_preview).get("asset_mode"))


def screen_type_from_preview(ui_preview: Asset) -> str:
    value = str(asset_metadata(ui_preview).get("screen_type") or DEFAULT_SCREEN_TYPE)
    return value if value in SUPPORTED_SCREEN_TYPES else DEFAULT_SCREEN_TYPE


def resource_category(component_type: str) -> str:
    return RESOURCE_CATEGORY_BY_COMPONENT_TYPE.get(component_type, "unknown_asset")


def production_usage(component_type: str) -> str:
    if component_type in {"button", "icon", "frame", "input", "slot", "tab"}:
        return "reusable_996_asset"
    if component_type in {"panel", "background", "bar"}:
        return "layout_or_full_region"
    return "manual_review_required"


def transparent_policy() -> dict[str, Any]:
    return {
        "required_component_types": ["button", "icon", "frame", "input"],
        "allowed_flat_component_types": ["panel", "background", "bar"],
        "verification": "metadata_only",
    }


def transparent_metadata(component_type: str) -> dict[str, bool | str]:
    required = component_type in {"button", "icon", "frame", "input"}
    return {
        "required": required,
        "verified": False,
        "status": "unverified" if required else "not_required",
    }


def component_quality_type(component_type: str) -> str | None:
    normalized = component_type.replace("_candidate", "")
    if normalized == "bar":
        return "panel"
    return normalized if normalized in QUALITY_COMPONENT_TYPES else None


def bounds_area(bounds: dict[str, int]) -> int:
    return max(0, bounds["width"]) * max(0, bounds["height"])


def union_covered_area(
    *,
    source_width: int,
    source_height: int,
    bounds_list: list[dict[str, int]],
) -> int:
    mask = Image.new("1", (source_width, source_height), 0)
    draw = ImageDraw.Draw(mask)
    for bounds in bounds_list:
        x1 = max(0, bounds["x"])
        y1 = max(0, bounds["y"])
        x2 = min(source_width, bounds["x"] + bounds["width"])
        y2 = min(source_height, bounds["y"] + bounds["height"])
        if x2 <= x1 or y2 <= y1:
            continue
        draw.rectangle((x1, y1, x2 - 1, y2 - 1), fill=1)
    return int(mask.histogram()[1])


def suspected_missing_regions(
    *,
    source_width: int,
    source_height: int,
    covered_bounds: list[dict[str, int]],
) -> list[dict[str, Any]]:
    regions: list[dict[str, Any]] = []
    columns = 4
    rows = 3
    minimum_area = max(1, round(source_width * source_height * 0.04))
    for row in range(rows):
        for column in range(columns):
            x = round(source_width * column / columns)
            y = round(source_height * row / rows)
            next_x = round(source_width * (column + 1) / columns)
            next_y = round(source_height * (row + 1) / rows)
            bounds = {"x": x, "y": y, "width": next_x - x, "height": next_y - y}
            cell_area = bounds_area(bounds)
            covered_area = union_covered_area(
                source_width=bounds["width"],
                source_height=bounds["height"],
                bounds_list=[
                    {
                        "x": max(0, item["x"] - x),
                        "y": max(0, item["y"] - y),
                        "width": min(next_x, item["x"] + item["width"]) - max(x, item["x"]),
                        "height": min(next_y, item["y"] + item["height"]) - max(y, item["y"]),
                    }
                    for item in covered_bounds
                    if item["x"] < next_x
                    and item["x"] + item["width"] > x
                    and item["y"] < next_y
                    and item["y"] + item["height"] > y
                ],
            )
            uncovered_area = cell_area - covered_area
            if uncovered_area >= minimum_area and uncovered_area / cell_area >= 0.65:
                regions.append(
                    {
                        "region_id": f"missing_r{row + 1}_c{column + 1}",
                        "bounds": bounds,
                        "uncovered_area": uncovered_area,
                        "uncovered_ratio": round(uncovered_area / cell_area, 4),
                        "reason": "large grid region has low component coverage",
                        "review_status": "pending",
                    }
                )
    return regions


def build_component_quality_report(
    *,
    source_width: int,
    source_height: int,
    manifest_components: list[dict[str, Any]],
    candidate_components: list[dict[str, Any]],
) -> dict[str, Any]:
    category_counts = {component_type: 0 for component_type in QUALITY_COMPONENT_TYPES}
    category_area = {component_type: 0 for component_type in QUALITY_COMPONENT_TYPES}
    report_components: list[dict[str, Any]] = []

    for component in manifest_components:
        component_type = component_quality_type(str(component.get("component_type") or ""))
        bounds = component.get("bounds")
        if component_type is None or not isinstance(bounds, dict):
            continue
        area = bounds_area(bounds)
        category_counts[component_type] += 1
        category_area[component_type] += area
        report_components.append(
            {
                "id": str(component.get("component_id") or ""),
                "source": "component",
                "component_type": component_type,
                "bounds": bounds,
                "area": area,
            }
        )

    for candidate in candidate_components:
        component_type = component_quality_type(str(candidate.get("candidate_type") or ""))
        bounds = candidate.get("bounds")
        if component_type is None or not isinstance(bounds, dict):
            continue
        area = bounds_area(bounds)
        category_counts[component_type] += 1
        category_area[component_type] += area
        report_components.append(
            {
                "id": str(candidate.get("candidate_id") or ""),
                "source": "candidate",
                "component_type": component_type,
                "bounds": bounds,
                "area": area,
                "confidence": candidate.get("confidence"),
            }
        )

    covered_bounds = [component["bounds"] for component in report_components]
    total_area = source_width * source_height
    covered_area = union_covered_area(
        source_width=source_width,
        source_height=source_height,
        bounds_list=covered_bounds,
    )
    uncovered_area = max(0, total_area - covered_area)

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "component_quality",
        "coordinate_space": COORDINATE_SPACE,
        "resolution": {"width": source_width, "height": source_height},
        "total_components": len(report_components),
        "category_counts": category_counts,
        "category_area": category_area,
        "coverage": {
            "total_area": total_area,
            "covered_area": covered_area,
            "covered_ratio": round(covered_area / total_area, 4) if total_area else 0,
            "uncovered_area": uncovered_area,
            "uncovered_ratio": round(uncovered_area / total_area, 4) if total_area else 0,
        },
        "suspected_missing_regions": suspected_missing_regions(
            source_width=source_width,
            source_height=source_height,
            covered_bounds=covered_bounds,
        ),
        "components": report_components,
    }


def candidate_bounds(
    source_width: int,
    source_height: int,
    x_ratio: float,
    y_ratio: float,
    width_ratio: float,
    height_ratio: float,
) -> dict[str, int]:
    x = round(source_width * x_ratio)
    y = round(source_height * y_ratio)
    width = max(1, round(source_width * width_ratio))
    height = max(1, round(source_height * height_ratio))
    width = min(width, source_width - x)
    height = min(height, source_height - y)
    return {"x": x, "y": y, "width": width, "height": height}


def candidate_confidence(image: Image.Image, bounds: dict[str, int]) -> float:
    crop = image.crop(
        (
            bounds["x"],
            bounds["y"],
            bounds["x"] + bounds["width"],
            bounds["y"] + bounds["height"],
        )
    ).convert("L")
    low, high = ImageStat.Stat(crop).extrema[0]
    contrast_score = (high - low) / 255
    return round(min(0.95, 0.55 + contrast_score * 0.4), 2)


def edge_components(image: Image.Image) -> list[dict[str, int]]:
    edges = image.convert("L").filter(ImageFilter.FIND_EDGES)
    pixels = edges.load()
    width, height = edges.size
    visited: set[tuple[int, int]] = set()
    components: list[dict[str, int]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in visited or pixels[x, y] < 24:
                continue
            stack = [(x, y)]
            visited.add((x, y))
            min_x = max_x = x
            min_y = max_y = y
            count = 0

            while stack:
                current_x, current_y = stack.pop()
                count += 1
                min_x = min(min_x, current_x)
                max_x = max(max_x, current_x)
                min_y = min(min_y, current_y)
                max_y = max(max_y, current_y)

                for next_x, next_y in (
                    (current_x - 1, current_y),
                    (current_x + 1, current_y),
                    (current_x, current_y - 1),
                    (current_x, current_y + 1),
                ):
                    if (
                        next_x < 0
                        or next_y < 0
                        or next_x >= width
                        or next_y >= height
                        or (next_x, next_y) in visited
                        or pixels[next_x, next_y] < 24
                    ):
                        continue
                    visited.add((next_x, next_y))
                    stack.append((next_x, next_y))

            box_width = max_x - min_x + 1
            box_height = max_y - min_y + 1
            if count >= 24 and box_width >= 20 and box_height >= 20:
                components.append({"x": min_x, "y": min_y, "width": box_width, "height": box_height})

    return components


def classify_candidate(bounds: dict[str, int], source_width: int, source_height: int) -> str | None:
    width = bounds["width"]
    height = bounds["height"]
    x = bounds["x"]
    y = bounds["y"]
    aspect = width / height
    squareish = 0.72 <= aspect <= 1.35

    if width > source_width * 0.35 and height > source_height * 0.28:
        return "frame_candidate"
    if aspect >= 4.0 and height <= source_height * 0.1:
        return "input_candidate"
    if 2.0 <= aspect < 4.0 and y > source_height * 0.55:
        return "button_candidate"
    if 2.0 <= aspect < 4.0 and y < source_height * 0.25:
        return "tab_candidate"
    if squareish and x > source_width * 0.55:
        return "icon_candidate"
    if squareish and x <= source_width * 0.55:
        return "slot_candidate"
    return None


def detected_candidate_bounds(image: Image.Image) -> dict[str, dict[str, int]]:
    source_width, source_height = image.size
    classified: dict[str, dict[str, int]] = {}
    components = sorted(
        edge_components(image),
        key=lambda item: item["width"] * item["height"],
        reverse=True,
    )

    for bounds in components:
        candidate_type = classify_candidate(bounds, source_width, source_height)
        if candidate_type is None or candidate_type in classified:
            continue
        classified[candidate_type] = bounds

    return classified


def detect_component_candidates(image: Image.Image, candidate_dir: Path) -> list[dict[str, Any]]:
    candidate_dir.mkdir(parents=True, exist_ok=True)
    source_width, source_height = image.size
    counters: dict[str, int] = {}
    candidates: list[dict[str, Any]] = []
    detected_bounds = detected_candidate_bounds(image)

    for candidate_type, x_ratio, y_ratio, width_ratio, height_ratio in CANDIDATE_RULES:
        counters[candidate_type] = counters.get(candidate_type, 0) + 1
        candidate_id = f"{candidate_type}_{counters[candidate_type]:02d}"
        bounds = detected_bounds.get(
            candidate_type,
            candidate_bounds(source_width, source_height, x_ratio, y_ratio, width_ratio, height_ratio),
        )
        file_name = f"{candidate_id}.png"
        image.crop(
            (
                bounds["x"],
                bounds["y"],
                bounds["x"] + bounds["width"],
                bounds["y"] + bounds["height"],
            )
        ).save(candidate_dir / file_name, format="PNG")
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_type": candidate_type,
                "resource_category": RESOURCE_CATEGORY_BY_CANDIDATE_TYPE.get(candidate_type, "unknown_asset"),
                "bounds": bounds,
                "confidence": candidate_confidence(image, bounds),
                "image_path": f"candidates/{file_name}",
                "transparent": transparent_metadata(candidate_type.replace("_candidate", "")),
                "review_status": "pending",
            }
        )

    return candidates


def process_ui_preview_components(
    *,
    database: StudioDatabase,
    upload_root: Path,
    ui_preview: Asset,
) -> dict[str, str | list[str]]:
    source_path = Path(ui_preview.file_path)
    if not source_path.exists():
        raise FileNotFoundError("UI preview file does not exist")

    output_root = upload_root / "996-ready" / (ui_preview.generation_job_id or ui_preview.id)
    component_dir = output_root / "components"
    candidate_dir = output_root / "candidates"
    component_dir.mkdir(parents=True, exist_ok=True)

    copied_preview = output_root / "ui_preview.png"
    shutil.copyfile(source_path, copied_preview)

    component_assets: list[Asset] = []
    manifest_components: list[dict[str, Any]] = []
    annotation_components: list[dict[str, Any]] = []
    candidate_components: list[dict[str, Any]] = []
    asset_mode = asset_mode_from_preview(ui_preview)
    screen_type = screen_type_from_preview(ui_preview)

    with Image.open(source_path).convert("RGBA") as image:
        source_width, source_height = image.size
        for component_type, x_ratio, y_ratio, width_ratio, height_ratio in COMPONENT_RULES:
            schema_component_type = COMPONENT_TYPE_BY_ID[component_type]
            component_name_zh = COMPONENT_NAME_ZH[component_type]
            note_zh = f"{component_name_zh}：模板化组件标注，后续可由智能识别增强。"
            x = round(source_width * x_ratio)
            y = round(source_height * y_ratio)
            width = max(1, round(source_width * width_ratio))
            height = max(1, round(source_height * height_ratio))
            width = min(width, source_width - x)
            height = min(height, source_height - y)
            component_id = component_type
            file_name = f"{component_type}.png"
            component_path = component_dir / file_name
            image.crop((x, y, x + width, y + height)).save(component_path, format="PNG")
            component_file = f"components/{file_name}"
            bounds = {"x": x, "y": y, "width": width, "height": height}
            transparent = transparent_metadata(schema_component_type)

            manifest_components.append(
                {
                    "component_id": component_id,
                    "component_type": schema_component_type,
                    "asset_mode": asset_mode,
                    "resource_category": resource_category(schema_component_type),
                    "production_usage": production_usage(schema_component_type),
                    "resource_group": "main",
                    "file": component_file,
                    "bounds": bounds,
                    "transparent": transparent,
                    "transparent_png_required": bool(transparent["required"]),
                    "transparent_png_verified": bool(transparent["verified"]),
                    "type": component_type,
                    "component_name_zh": component_name_zh,
                    "中文组件名称": component_name_zh,
                    "中文说明": note_zh,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "file_name": file_name,
                }
            )
            annotation_components.append(
                {
                    "component_id": component_id,
                    "component_type": schema_component_type,
                    "组件名称": component_name_zh,
                    "组件类型": component_name_zh,
                    "x": x,
                    "X坐标": x,
                    "y": y,
                    "Y坐标": y,
                    "width": width,
                    "宽度": width,
                    "height": height,
                    "高度": height,
                    "font_family": "Microsoft YaHei",
                    "字体": "Microsoft YaHei",
                    "font_size": 16,
                    "字号": 16,
                    "font_color": "#F5D78E",
                    "字体颜色": "#F5D78E",
                    "notes": "Template-based Sprint 8A annotation",
                    "说明": note_zh,
                }
            )
            annotation_components[-1].update(
                {
                    "component_name_zh": component_name_zh,
                    "asset_mode": asset_mode,
                    "resource_category": resource_category(schema_component_type),
                    "production_usage": production_usage(schema_component_type),
                    "resource_group": "main",
                    "bounds": bounds,
                    "style": {
                        "font_family": "Microsoft YaHei",
                        "font_size": 16,
                        "font_color": "#F5D78E",
                    },
                    "image": {
                        "file": component_file,
                        "format": "png",
                        "color_mode": "RGBA",
                        "alpha": "optional",
                        "transparent_background": False,
                    },
                    "transparent": transparent,
                    "recognition": {
                        "method": "template",
                        "confidence": None,
                    },
                    "requires_manual_review": True,
                    "review_status": "pending",
                }
            )
            component_assets.append(
                database.create_asset(
                    AssetCreate(
                        project_id=ui_preview.project_id,
                        asset_type="sliced_component",
                        device_type=ui_preview.device_type,
                        width=width,
                        height=height,
                        file_path=str(component_path),
                        original_filename=file_name,
                        metadata_json=json.dumps(
                            {
                                "component_id": component_id,
                                "component_type": schema_component_type,
                                "template_component_id": component_id,
                                "source_asset_id": ui_preview.id,
                                "template": screen_type,
                            },
                            ensure_ascii=False,
                        ),
                        source="component_processing",
                        generation_job_id=ui_preview.generation_job_id,
                        thumbnail_path="",
                    )
                )
            )
        candidate_components = detect_component_candidates(image, candidate_dir)
        component_quality_report = build_component_quality_report(
            source_width=source_width,
            source_height=source_height,
            manifest_components=manifest_components,
            candidate_components=candidate_components,
        )

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_type": PACKAGE_TYPE,
        "template": screen_type,
        "asset_mode": asset_mode,
        "source_asset_id": ui_preview.id,
        "generation_job_id": ui_preview.generation_job_id or ui_preview.id,
        "device_type": normalize_device_type(ui_preview.device_type),
        "resolution": {
            "width": source_width,
            "height": source_height,
        },
        "ui_preview": "ui_preview.png",
        "components_dir": "components",
        "transparent_policy": transparent_policy(),
        "resource_summary": {
            "mode": asset_mode,
            "classification": "template_and_candidate",
            "transparent_metadata": "included",
        },
        "components": manifest_components,
    }
    annotation = {
        "schema_version": SCHEMA_VERSION,
        "template": screen_type,
        "asset_mode": asset_mode,
        "source_asset_id": ui_preview.id,
        "device_type": normalize_device_type(ui_preview.device_type),
        "coordinate_space": COORDINATE_SPACE,
        "transparent_policy": transparent_policy(),
        "components": annotation_components,
    }
    candidate_manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_type": PACKAGE_TYPE,
        "template": screen_type,
        "asset_mode": asset_mode,
        "detection_method": "rule_and_image_feature",
        "source_asset_id": ui_preview.id,
        "generation_job_id": ui_preview.generation_job_id or ui_preview.id,
        "ui_preview": "ui_preview.png",
        "candidates_dir": "candidates",
        "coordinate_space": COORDINATE_SPACE,
        "transparent_policy": transparent_policy(),
        "candidates": candidate_components,
    }

    manifest_path = output_root / "manifest.json"
    annotation_path = output_root / "annotation.json"
    preview_html_path = output_root / "preview.html"
    candidate_manifest_path = output_root / "candidate_manifest.json"
    candidate_preview_html_path = output_root / "candidate_preview.html"
    component_quality_report_path = output_root / "component_quality_report.json"
    component_quality_report_html_path = output_root / "component_quality_report.html"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    annotation_path.write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    preview_html_path.write_text(render_preview_html(manifest_components), encoding="utf-8")
    candidate_manifest_path.write_text(
        json.dumps(candidate_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    candidate_preview_html_path.write_text(
        render_candidate_preview_html(candidate_components, source_width, source_height),
        encoding="utf-8",
    )
    component_quality_report_path.write_text(
        json.dumps(component_quality_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    component_quality_report_html_path.write_text(
        render_component_quality_report_html(component_quality_report),
        encoding="utf-8",
    )

    return {
        "manifest_path": str(manifest_path),
        "annotation_path": str(annotation_path),
        "preview_html_path": str(preview_html_path),
        "candidate_manifest_path": str(candidate_manifest_path),
        "candidate_preview_html_path": str(candidate_preview_html_path),
        "component_quality_report_path": str(component_quality_report_path),
        "component_quality_report_html_path": str(component_quality_report_html_path),
        "component_asset_ids": [asset.id for asset in component_assets],
    }


def render_preview_html(components: list[dict[str, Any]]) -> str:
    items = "\n".join(
        f"<li><code>{html.escape(component['file_name'])}</code> "
        f"{html.escape(component['component_name_zh'])} "
        f"<span>{html.escape(component['中文说明'])}</span> "
        f"({component['x']}, {component['y']}, {component['width']}x{component['height']})</li>"
        for component in components
    )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996-ready 组件预览</title></head><body>"
        "<h1>996-ready 组件预览</h1>"
        "<p>模板化组件标注</p>"
        f"<ul>{items}</ul>"
        "</body></html>"
    )


def render_candidate_preview_html(
    candidates: list[dict[str, Any]],
    source_width: int,
    source_height: int,
) -> str:
    boxes = "\n".join(
        (
            f"<div class=\"box {html.escape(candidate['candidate_type'])}\" "
            f"style=\"left:{candidate['bounds']['x']}px;top:{candidate['bounds']['y']}px;"
            f"width:{candidate['bounds']['width']}px;height:{candidate['bounds']['height']}px\">"
            f"<span>{html.escape(candidate['candidate_id'])} "
            f"{html.escape(candidate['candidate_type'])} "
            f"{candidate['confidence']}</span></div>"
        )
        for candidate in candidates
    )
    rows = "\n".join(
        (
            f"<tr><td>{html.escape(candidate['candidate_id'])}</td>"
            f"<td>{html.escape(candidate['candidate_type'])}</td>"
            f"<td>{candidate['confidence']}</td>"
            f"<td><code>{html.escape(candidate['image_path'])}</code></td>"
            f"<td>{html.escape(candidate['review_status'])}</td></tr>"
        )
        for candidate in candidates
    )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996-ready candidate preview</title>"
        "<style>"
        "body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#151923;color:#f4ead4;}"
        ".stage{position:relative;display:inline-block;line-height:0;border:1px solid #544a38;}"
        f".stage{{width:{source_width}px;height:{source_height}px;}}"
        ".stage img{width:100%;height:100%;display:block;}"
        ".box{position:absolute;box-sizing:border-box;border:3px solid #ffcf5a;background:rgba(255,207,90,.12);}"
        ".box span{position:absolute;left:0;top:-24px;line-height:18px;background:#111827;"
        "color:#ffe8a3;padding:2px 6px;font-size:12px;white-space:nowrap;}"
        ".button_candidate{border-color:#ffcf5a}.icon_candidate{border-color:#67e8f9}"
        ".input_candidate{border-color:#a7f3d0}.frame_candidate{border-color:#fca5a5}"
        ".tab_candidate{border-color:#c4b5fd}.slot_candidate{border-color:#fdba74}"
        "table{border-collapse:collapse;margin-top:20px;min-width:760px;}"
        "td,th{border:1px solid #544a38;padding:8px 10px;}th{background:#202636;}"
        "code{color:#bde0fe;}"
        "</style></head><body>"
        "<h1>996-ready candidate preview</h1>"
        "<div class=\"stage\"><img src=\"ui_preview.png\" alt=\"ui preview\">"
        f"{boxes}</div>"
        "<table><thead><tr><th>candidate_id</th><th>candidate_type</th>"
        "<th>confidence</th><th>image_path</th><th>review_status</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        "</body></html>"
    )


def render_component_quality_report_html(report: dict[str, Any]) -> str:
    counts = report["category_counts"]
    areas = report["category_area"]
    coverage = report["coverage"]
    rows = "\n".join(
        (
            f"<tr><td>{html.escape(component_type)}</td>"
            f"<td>{counts[component_type]}</td>"
            f"<td>{areas[component_type]}</td></tr>"
        )
        for component_type in QUALITY_COMPONENT_TYPES
    )
    missing_rows = "\n".join(
        (
            f"<tr><td>{html.escape(region['region_id'])}</td>"
            f"<td>{region['bounds']['x']}, {region['bounds']['y']}, "
            f"{region['bounds']['width']}x{region['bounds']['height']}</td>"
            f"<td>{region['uncovered_area']}</td>"
            f"<td>{region['uncovered_ratio']}</td>"
            f"<td>{html.escape(region['review_status'])}</td></tr>"
        )
        for region in report["suspected_missing_regions"]
    )
    if not missing_rows:
        missing_rows = "<tr><td colspan=\"5\">No large low-coverage grid regions detected.</td></tr>"

    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996-ready component quality report</title>"
        "<style>"
        "body{font-family:Arial,'Microsoft YaHei',sans-serif;margin:24px;background:#f8fafc;color:#172033;}"
        "h1,h2{margin:0 0 12px;}section{margin-top:24px;}"
        ".summary{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;max-width:960px;}"
        ".metric{border:1px solid #d9e2ef;border-radius:6px;background:white;padding:12px;}"
        ".metric strong{display:block;font-size:20px;margin-top:4px;}table{border-collapse:collapse;min-width:720px;background:white;}"
        "td,th{border:1px solid #d9e2ef;padding:8px 10px;text-align:left;}th{background:#e8eef7;}"
        "</style></head><body>"
        "<h1>996-ready component quality report</h1>"
        "<div class=\"summary\">"
        f"<div class=\"metric\">Total components<strong>{report['total_components']}</strong></div>"
        f"<div class=\"metric\">Covered area<strong>{coverage['covered_area']}</strong></div>"
        f"<div class=\"metric\">Uncovered area<strong>{coverage['uncovered_area']}</strong></div>"
        f"<div class=\"metric\">Covered ratio<strong>{coverage['covered_ratio']}</strong></div>"
        "</div>"
        "<section><h2>Category statistics</h2>"
        "<table><thead><tr><th>category</th><th>count</th><th>raw area</th></tr></thead>"
        f"<tbody>{rows}</tbody></table></section>"
        "<section><h2>Suspected missing regions</h2>"
        "<table><thead><tr><th>region</th><th>bounds</th><th>uncovered area</th>"
        "<th>uncovered ratio</th><th>review</th></tr></thead>"
        f"<tbody>{missing_rows}</tbody></table></section>"
        "</body></html>"
    )
