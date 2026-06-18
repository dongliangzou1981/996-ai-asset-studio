from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_production_package import analyze_package


P5_MAIN_UI_SOURCE = Path("\\\\192.168.0.173\\tools\\ps\\P5\\Z\u4e3b\u754c\u9762\\\u65b0\u4e3b\u754c\u97621.jpg")
P5_MARKED_REFERENCE = Path("\\\\192.168.0.173\\tools\\ps\\P5\\Z\u4e3b\u754c\u9762\\\u65b0\u4e3b\u754c\u97621\u6807\u6ce8.png")

LEVEL_A_TYPES = {
    "button",
    "icon",
    "tab",
    "input",
    "skill_icon",
    "skill_button",
    "equipment_slot",
    "close_button",
    "currency_icon",
    "joystick",
    "system_entry_icon",
}
JPG_TYPES = {"screen", "background", "panel", "hud_bar", "chat", "map", "skill_bar"}

MAIN_TASK_PANEL_SPEC: dict[str, Any] = {
    "module_id": "main_task_panel",
    "name": "主界面左上任务追踪模块",
    "canvas": {"width": 1728, "height": 972},
    "fixed_rect": {"x": 24, "y": 40, "width": 286, "height": 330},
    "max_width": 302,
    "transparent_required": True,
    "text_allowed": False,
    "forbidden_elements": [
        "complete_game_screen",
        "map",
        "character",
        "monster",
        "scene_background",
        "chinese_text",
        "other_hud_regions",
    ],
    "internal_structure": [
        "task_panel_background",
        "title_bar_base",
        "task_item_rows",
        "divider_lines",
        "fold_button_base",
        "subtle_ornamental_frame",
    ],
}

MAIN_TASK_PANEL_PROMPT = """生成一个 996 传奇手游横屏主界面左上任务追踪 HUD 模块皮肤。

画布尺寸：286×330 px。
透明背景。
正视图。
只生成该任务模块，不要生成完整游戏界面。

模块内容：
- 暗金色半透明任务面板底板
- 顶部小标题栏底板
- 3 到 5 条任务列表底板
- 细金属边框
- 轻微传奇风装饰纹理
- 一个小型折叠按钮底板

禁止：
- 不要中文文字
- 不要人物
- 不要怪物
- 不要地图
- 不要场景背景
- 不要其他 UI 区域
- 不要超出画布边界

风格：
暗金、金属、复古传奇、手游 HUD、边界清晰、适合叠加在游戏画面上。"""

MAIN_TASK_PANEL_PRODUCTION_STATUS: dict[str, Any] = {
    "requested_generation_mode": "mock",
    "generation_mode": "mock",
    "generation_provider": "",
    "generation_job_id": "",
    "production_ready": False,
    "visual_quality_status": "not_started",
    "fallback_used": False,
    "fallback_reason": "",
    "usage_note": "Engineering loop validation only; not a production-ready AI visual asset.",
    "transparent_requested": True,
    "transparent_guaranteed": False,
}

MAIN_TASK_PANEL_STATUS_KEYS = tuple(MAIN_TASK_PANEL_PRODUCTION_STATUS.keys())
MAIN_TASK_PANEL_GENERATION_MODES = {"mock", "ai"}
MainTaskPanelAiCandidateGenerator = Callable[[Path, int, dict[str, Any]], dict[str, Any] | None]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_job_id(prefix: str = "ui-production") -> str:
    return datetime.now(timezone.utc).strftime(f"{prefix}-%Y%m%d-%H%M%S-%f")


def bounds(width: int, height: int, x: float, y: float, w: float, h: float) -> dict[str, int]:
    left = max(0, min(width - 1, round(width * x)))
    top = max(0, min(height - 1, round(height * y)))
    box_width = max(1, min(width - left, round(width * w)))
    box_height = max(1, min(height - top, round(height * h)))
    return {"x": left, "y": top, "width": box_width, "height": box_height}


def rect_outline(box: dict[str, int]) -> list[dict[str, int]]:
    x = int(box["x"])
    y = int(box["y"])
    right = x + int(box["width"])
    bottom = y + int(box["height"])
    return [{"x": x, "y": y}, {"x": right, "y": y}, {"x": right, "y": bottom}, {"x": x, "y": bottom}]


def circle_outline(box: dict[str, int], segments: int = 16) -> list[dict[str, int]]:
    import math

    x = int(box["x"])
    y = int(box["y"])
    width = int(box["width"])
    height = int(box["height"])
    cx = x + width / 2
    cy = y + height / 2
    rx = width / 2
    ry = height / 2
    return [
        {
            "x": round(cx + math.cos(2 * math.pi * index / segments) * rx),
            "y": round(cy + math.sin(2 * math.pi * index / segments) * ry),
        }
        for index in range(segments)
    ]


def composite_outline(box: dict[str, int]) -> list[dict[str, int]]:
    x = int(box["x"])
    y = int(box["y"])
    width = int(box["width"])
    height = int(box["height"])
    inset_x = max(4, round(width * 0.06))
    inset_y = max(4, round(height * 0.08))
    return [
        {"x": x + inset_x, "y": y},
        {"x": x + width - inset_x, "y": y},
        {"x": x + width, "y": y + inset_y},
        {"x": x + width, "y": y + height - inset_y},
        {"x": x + width - inset_x, "y": y + height},
        {"x": x + inset_x, "y": y + height},
        {"x": x, "y": y + height - inset_y},
        {"x": x, "y": y + inset_y},
    ]


def outline_for_shape(box: dict[str, int], shape_type: str) -> list[dict[str, int]]:
    if shape_type == "circle":
        return circle_outline(box)
    if shape_type == "composite":
        return composite_outline(box)
    return rect_outline(box)


def candidate_record(
    *,
    width: int,
    height: int,
    index: int,
    component_id: str,
    name: str,
    component_type: str,
    layout_zone: str,
    shape_type: str,
    x: float,
    y: float,
    w: float,
    h: float,
    confirmed: bool,
) -> dict[str, Any]:
    box = bounds(width, height, x, y, w, h)
    level = classify_level(component_type)
    return {
        "candidate_id": component_id,
        "component_id": component_id,
        "component_name": name,
        "component_type": component_type,
        "layer_name": component_id,
        "layer_group": layout_zone,
        "layer_order": index,
        "slice_layer": {
            "name": component_id,
            "group": layout_zone,
            "order": index,
            "component_type": component_type,
        },
        "number": index,
        "bounds": box,
        "bbox": box,
        "outline_points": outline_for_shape(box, shape_type),
        "shape_type": shape_type,
        "layout_zone": layout_zone,
        "level": level,
        "production_category": production_category(component_type, level),
        "recommended_action": recommended_action(level),
        "confirmed": confirmed,
        "output_format": output_format(component_type, level),
        "output_name": output_name(component_id, component_type),
        "transparent_required": level == "A",
        "transparent_warning": "",
        "image_path": "",
    }


def classify_level(component_type: str) -> str:
    if component_type in LEVEL_A_TYPES:
        return "A"
    if component_type in JPG_TYPES:
        return "B"
    return "C"


def production_category(component_type: str, level: str) -> str:
    if component_type == "screen":
        return "Screen"
    if component_type in {"panel", "hud_bar", "chat", "map", "skill_bar"}:
        return "Panel"
    if level == "A":
        return "Atomic"
    if component_type in {"effect", "decoration"}:
        return "Effect"
    return "Ignore"


def output_name(component_id: str, component_type: str) -> str:
    if component_type == "screen":
        return "screen_main_ui.jpg"
    if component_type in {"panel", "hud_bar", "chat", "map", "skill_bar"}:
        return f"panel_{component_id}.jpg"
    if component_type == "equipment_slot":
        return f"slot_{component_id}.png"
    if component_type in {"icon", "skill_icon", "currency_icon", "system_entry_icon"}:
        return f"icon_{component_id}.png"
    return f"btn_{component_id}.png"


def output_format(component_type: str, level: str) -> str:
    if component_type in JPG_TYPES or level == "B":
        return "jpg"
    return "png"


def recommended_action(level: str) -> str:
    if level == "A":
        return "\u786e\u8ba4\u5207\u56fe"
    if level == "B":
        return "\u786e\u8ba4\u5207\u56fe\u6216\u4eba\u5de5\u590d\u6838"
    return "\u9ed8\u8ba4\u4e0d\u5207"


def main_ui_candidates(width: int, height: int) -> list[dict[str, Any]]:
    specs = [
        ("screen_main_ui", "\u5b8c\u6574\u4e3b\u754c\u9762", "screen", "full_screen", "rect", 0.0, 0.0, 1.0, 1.0, True),
        ("top_player_info", "\u9876\u90e8\u89d2\u8272\u72b6\u6001\u533a", "hud_bar", "top_info", "composite", 0.03, 0.01, 0.19, 0.20, True),
        ("task_panel", "\u5de6\u4fa7\u4efb\u52a1\u680f", "panel", "left_task", "rect", 0.0, 0.01, 0.22, 0.47, True),
        ("task_tab", "\u4efb\u52a1\u9875\u7b7e", "button", "left_task", "rect", 0.0, 0.02, 0.035, 0.10, True),
        ("team_tab", "\u7ec4\u961f\u9875\u7b7e", "button", "left_task", "rect", 0.0, 0.26, 0.035, 0.12, True),
        ("status_panel", "\u5de6\u4fa7\u72b6\u6001\u533a", "panel", "left_status", "rect", 0.0, 0.31, 0.21, 0.18, True),
        ("health_bar", "\u536b\u58eb\u8840\u91cf\u6761", "hud_bar", "left_status", "rect", 0.05, 0.43, 0.12, 0.03, True),
        ("left_joystick", "\u5de6\u4e0b\u6447\u6746", "joystick", "bottom_left_joystick", "circle", 0.06, 0.69, 0.10, 0.18, True),
        ("run_button", "\u8dd1\u6b65\u6309\u94ae", "button", "bottom_left_joystick", "circle", 0.16, 0.63, 0.055, 0.09, True),
        ("walk_button", "\u884c\u8d70\u6309\u94ae", "button", "bottom_left_joystick", "circle", 0.08, 0.80, 0.055, 0.09, True),
        ("bottom_hud", "\u5e95\u90e8\u4e3b HUD", "hud_bar", "bottom_status", "composite", 0.23, 0.72, 0.56, 0.26, True),
        ("hp_orb", "\u8840\u91cf\u7403", "icon", "bottom_status", "circle", 0.28, 0.76, 0.09, 0.16, True),
        ("mp_orb", "\u9b54\u6cd5\u7403", "icon", "bottom_status", "circle", 0.35, 0.76, 0.09, 0.16, True),
        ("dragon_frame", "\u9f99\u7eb9\u72b6\u6001\u6846", "decoration", "bottom_status", "composite", 0.26, 0.68, 0.20, 0.30, False),
        ("item_slot_01", "\u7269\u54c1\u683c 1", "equipment_slot", "bottom_status", "rect", 0.52, 0.75, 0.045, 0.10, True),
        ("item_slot_02", "\u7269\u54c1\u683c 2", "equipment_slot", "bottom_status", "rect", 0.565, 0.75, 0.045, 0.10, True),
        ("item_slot_03", "\u7269\u54c1\u683c 3", "equipment_slot", "bottom_status", "rect", 0.61, 0.75, 0.045, 0.10, True),
        ("item_slot_04", "\u7269\u54c1\u683c 4", "equipment_slot", "bottom_status", "rect", 0.655, 0.75, 0.045, 0.10, True),
        ("chat_panel", "\u804a\u5929/\u7cfb\u7edf\u4fe1\u606f", "chat", "chat", "rect", 0.48, 0.80, 0.25, 0.16, True),
        ("skill_01", "\u6280\u80fd\u6309\u94ae 1", "skill_button", "right_skill", "circle", 0.85, 0.73, 0.08, 0.14, True),
        ("skill_02", "\u6280\u80fd\u6309\u94ae 2", "skill_button", "right_skill", "circle", 0.92, 0.78, 0.07, 0.12, True),
        ("skill_03", "\u6280\u80fd\u6309\u94ae 3", "skill_button", "right_skill", "circle", 0.91, 0.63, 0.07, 0.12, True),
        ("auto_button", "\u81ea\u52a8\u6309\u94ae", "button", "right_system_entry", "circle", 0.90, 0.45, 0.06, 0.10, True),
        ("role_entry", "\u89d2\u8272\u5165\u53e3", "system_entry_icon", "right_system_entry", "circle", 0.86, 0.31, 0.055, 0.095, True),
        ("bag_entry", "\u80cc\u5305\u5165\u53e3", "system_entry_icon", "right_system_entry", "circle", 0.93, 0.31, 0.055, 0.095, True),
        ("shop_entry", "\u5546\u57ce\u5165\u53e3", "system_entry_icon", "right_system_entry", "circle", 0.77, 0.80, 0.065, 0.12, True),
        ("activity_entry", "\u6d3b\u52a8\u5165\u53e3", "system_entry_icon", "right_system_entry", "circle", 0.96, 0.45, 0.035, 0.065, True),
        ("mini_map", "\u53f3\u4e0a\u5c0f\u5730\u56fe", "map", "right_top_map", "rect", 0.86, 0.02, 0.14, 0.25, True),
        ("map_zoom", "\u5730\u56fe\u7f29\u8fdb\u56fe\u6807", "system_entry_icon", "right_top_map", "rect", 0.83, 0.02, 0.035, 0.19, True),
        ("currency", "\u8d27\u5e01\u56fe\u6807", "currency_icon", "bottom_status", "circle", 0.76, 0.89, 0.035, 0.055, True),
        ("dynamic_text", "\u52a8\u6001\u6570\u503c\u6587\u5b57", "dynamic_content", "top_info", "rect", 0.39, 0.03, 0.16, 0.06, False),
    ]
    return [
        candidate_record(
            width=width,
            height=height,
            index=index,
            component_id=component_id,
            name=name,
            component_type=component_type,
            layout_zone=layout_zone,
            shape_type=shape_type,
            x=x,
            y=y,
            w=w,
            h=h,
            confirmed=confirmed,
        )
        for index, (component_id, name, component_type, layout_zone, shape_type, x, y, w, h, confirmed) in enumerate(specs, 1)
    ]


def load_badge_font(size: int) -> ImageFont.ImageFont:
    for font_path in [Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\arial.ttf")]:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def draw_candidate_preview(source: Path, target: Path, candidates: list[dict[str, Any]]) -> None:
    with Image.open(source) as image:
        preview = image.convert("RGB")
    draw = ImageDraw.Draw(preview)
    font = load_badge_font(max(16, preview.width // 60))
    for candidate in candidates:
        box = candidate["bounds"]
        x = int(box["x"])
        y = int(box["y"])
        width = int(box["width"])
        height = int(box["height"])
        color = "#00e5ff" if candidate["level"] == "A" else "#ffd447" if candidate["level"] == "B" else "#9ca3af"
        line_width = max(2, preview.width // 512)
        shape_type = str(candidate.get("shape_type") or "rect")
        if shape_type == "circle":
            draw.ellipse([x, y, x + width, y + height], outline=color, width=line_width)
        elif shape_type == "composite":
            points = [(int(point["x"]), int(point["y"])) for point in candidate.get("outline_points", []) if isinstance(point, dict)]
            if len(points) >= 3:
                draw.line(points + [points[0]], fill=color, width=line_width)
            else:
                draw.rectangle([x, y, x + width, y + height], outline=color, width=line_width)
        else:
            draw.rectangle([x, y, x + width, y + height], outline=color, width=line_width)
        radius = max(14, preview.width // 80)
        cx = min(preview.width - radius - 2, x + radius + 4)
        cy = max(radius + 2, y - radius // 2)
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill="#111827", outline="#ffffff", width=2)
        label = str(candidate["number"])
        bbox = draw.textbbox((0, 0), label, font=font)
        draw.text((cx - (bbox[2] - bbox[0]) / 2, cy - (bbox[3] - bbox[1]) / 2), label, fill="#ffffff", font=font)
    preview.save(target, "JPEG", quality=92)


def read_template_summary(template_doc: Path | None) -> dict[str, Any]:
    if template_doc is None or not template_doc.exists():
        return {"template_doc_found": False, "template_doc": "", "notes": []}
    notes: list[str] = []
    try:
        sample = template_doc.read_bytes()[:4_000_000]
        text = sample.decode("utf-16le", errors="ignore")
        for keyword in ["\u4e3b\u754c\u9762", "\u80cc\u5305", "\u89d2\u8272", "\u5546\u57ce", "\u6d3b\u52a8", "\u6280\u80fd", "\u6447\u6746", "\u6309\u94ae"]:
            if keyword in text:
                notes.append(keyword)
    except OSError as exc:
        return {"template_doc_found": True, "template_doc": str(template_doc), "notes": [], "read_warning": str(exc)}
    return {"template_doc_found": True, "template_doc": str(template_doc), "notes": sorted(set(notes))}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def image_has_transparent_pixels(path: Path) -> bool:
    with Image.open(path) as image:
        alpha = image.convert("RGBA").getchannel("A")
        minimum, _ = alpha.getextrema()
        return minimum < 255


def default_source_image(upload_root: Path) -> Path:
    fallback = upload_root / "sprint20i-fallback" / "mock_main_ui.jpg"
    if not fallback.exists():
        create_fallback_main_ui_source(fallback)
    if fallback.exists():
        return fallback
    return P5_MAIN_UI_SOURCE


def create_fallback_main_ui_source(target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), (28, 31, 36))
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, height), fill=(34, 37, 43))
    draw.rectangle((0, 0, width, 92), fill=(56, 48, 39), outline=(190, 146, 70), width=3)
    draw.rectangle((18, 16, 290, 132), fill=(45, 51, 64), outline=(224, 178, 82), width=4)
    draw.rectangle((0, 20, 285, 352), fill=(38, 43, 52), outline=(166, 129, 67), width=4)
    draw.rectangle((20, 250, 270, 380), fill=(44, 54, 57), outline=(158, 129, 74), width=3)
    draw.rectangle((650, 572, 965, 690), fill=(30, 38, 46), outline=(126, 109, 78), width=3)
    draw.rectangle((300, 585, 1015, 705), fill=(50, 43, 38), outline=(202, 156, 76), width=5)
    draw.rectangle((326, 674, 974, 692), fill=(81, 31, 28), outline=(231, 180, 87), width=2)
    draw.rectangle((1075, 18, 1265, 190), fill=(35, 52, 49), outline=(212, 169, 83), width=5)

    for index, center in enumerate([(90, 610), (180, 575), (115, 655)], 1):
        radius = 52 if index == 1 else 34
        draw.ellipse(
            (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
            fill=(55, 61, 67),
            outline=(215, 170, 86),
            width=4,
        )

    skill_centers = [(1110, 610), (1190, 655), (1200, 535), (1045, 665), (1048, 548)]
    for index, center in enumerate(skill_centers):
        radius = 58 if index == 0 else 40
        draw.ellipse(
            (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
            fill=(68, 48, 44),
            outline=(236, 182, 83),
            width=5,
        )

    for x in [675, 735, 795, 855]:
        draw.rectangle((x, 560, x + 46, 626), fill=(42, 43, 51), outline=(196, 154, 78), width=3)

    for x, y in [(1095, 250), (1180, 250), (990, 610), (1220, 340)]:
        draw.ellipse((x, y, x + 58, y + 58), fill=(44, 55, 69), outline=(210, 168, 84), width=3)

    font = load_badge_font(28)
    draw.text((44, 42), "Fallback Main UI", fill=(242, 220, 164), font=font)
    draw.text((672, 646), "EXP", fill=(242, 220, 164), font=font)
    draw.text((676, 598), "CHAT", fill=(242, 220, 164), font=font)
    image.save(target, "JPEG", quality=92)
    return target


def style_reference_note(style_reference_strength: str) -> str:
    labels = {
        "none": "\u4e0d\u53c2\u8003\u98ce\u683c",
        "30": "30%\u53c2\u8003",
        "60": "60%\u53c2\u8003",
        "90": "90%\u53c2\u8003",
        "copy": "\u9ad8\u590d\u523b",
    }
    label = labels.get(style_reference_strength, style_reference_strength or "\u4e0d\u53c2\u8003\u98ce\u683c")
    return f"{label}\uff1a\u5df2\u5199\u5165\u63d0\u793a\u8bcd/生成参数；当前模型不保证精确百分比控制"


def create_candidate_options(package_dir: Path, source: Path) -> list[dict[str, str]]:
    options_dir = package_dir / "candidate_options"
    options_dir.mkdir(exist_ok=True)
    with Image.open(source) as image:
        base = image.convert("RGB")
        variants = [
            ("candidate_1", "\u5019\u9009 1\uff1a\u539f\u59cb\u53c2\u8003\u5e03\u5c40", base),
            ("candidate_2", "\u5019\u9009 2\uff1a\u589e\u5f3a\u5bf9\u6bd4\u5ea6", ImageEnhance.Contrast(base).enhance(1.08)),
            ("candidate_3", "\u5019\u9009 3\uff1a\u589e\u5f3a\u8fb9\u7f18\u6e05\u6670\u5ea6", ImageEnhance.Sharpness(base).enhance(1.18)),
        ]
        options = []
        for candidate_id, label, variant in variants:
            filename = f"candidate_options/{candidate_id}.jpg"
            variant.save(package_dir / filename, "JPEG", quality=92)
            options.append({"candidate_id": candidate_id, "label": label, "file": filename})
    return options


def write_base_package_files(
    package_dir: Path,
    *,
    screen_type: str,
    requirement: str,
    style_reference_strength: str,
    source_note: dict[str, Any],
    candidate_options: list[dict[str, str]],
    reference_influence_percent: int | None = None,
    adjustment_note: str = "",
    adjustment_image_path: str = "",
) -> None:
    generated_at = utc_now()
    base = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "template": screen_type,
        "generation_job_id": package_dir.name,
        "ui_preview": "ui_preview.png",
        "main_ui": "main_ui.jpg",
        "components_dir": "confirmed_components",
    }
    write_json(package_dir / "manifest.json", {**base, "components": []})
    write_json(
        package_dir / "annotation.json",
        {"schema_version": "1.0", "template": screen_type, "coordinate_space": "main_ui_pixels", "components": []},
    )
    write_json(
        package_dir / "manual_acceptance.json",
        {
            "schema_version": "1.0",
            "review_status": "pending",
            "reviewer": "",
            "remarks": "",
            "updated_at": generated_at,
            "accepted_at": None,
            "accepted_by": "",
            "components": [],
        },
    )
    write_json(
        package_dir / "delivery_report.json",
        {
            "screen_type": screen_type,
            "generation_job_id": package_dir.name,
            "workflow": "sprint20c_ui_production_pipeline",
            "requirement": requirement,
            "style_reference_strength": style_reference_strength,
            "style_reference_note": style_reference_note(style_reference_strength),
            "generation_parameters": {
                "style_reference_strength": style_reference_strength,
                "reference_influence_percent": reference_influence_percent,
                "style_reference_note": style_reference_note(style_reference_strength),
                "model_supports_exact_style_strength": False,
            },
            "reference_influence_percent": reference_influence_percent,
            "final_prompt": f"{requirement}\n\u98ce\u683c\u53c2\u8003\uff1a{style_reference_note(style_reference_strength)}".strip(),
            "candidate_options": candidate_options,
            "selected_candidate_id": "candidate_1",
            "adjustments": [
                {
                    "note": adjustment_note,
                    "image_path": adjustment_image_path,
                    "created_at": generated_at,
                }
            ]
            if adjustment_note or adjustment_image_path
            else [],
            "generated_at": generated_at,
            "source_note": source_note,
        },
    )


def create_ui_package(
    upload_root: str | Path,
    *,
    screen_type: str = "main_ui",
    source_image: str | Path | None = None,
    template_doc: str | Path | None = None,
    job_id: str | None = None,
    requirement: str = "",
    style_reference_strength: str = "none",
    reference_influence_percent: int | None = None,
    adjustment_note: str = "",
    adjustment_image_path: str = "",
) -> dict[str, Any]:
    if screen_type != "main_ui":
        raise ValueError(f"{screen_type} is a placeholder flow and is not implemented yet")
    upload_path = Path(upload_root)
    source = Path(source_image) if source_image else default_source_image(upload_path)
    if not source.exists():
        raise FileNotFoundError(f"Main UI source image not found: {source}")
    package_dir = upload_path / "996-ready" / "SPRINT20C_UI_PRODUCTION" / screen_type / (job_id or safe_job_id("main-ui"))
    package_dir.mkdir(parents=True, exist_ok=True)
    reference_dir = package_dir / "reference"
    reference_dir.mkdir(exist_ok=True)

    main_ui_path = package_dir / "main_ui.jpg"
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        rgb.save(main_ui_path, "JPEG", quality=92)
        rgb.save(package_dir / "ui_preview.png", "PNG")
    candidate_options = create_candidate_options(package_dir, main_ui_path)
    if P5_MARKED_REFERENCE.exists():
        shutil.copyfile(P5_MARKED_REFERENCE, reference_dir / "p5_marked_reference.png")
    doc_path = Path(template_doc) if template_doc else Path.home() / "Desktop" / "\u4e3b\u754c\u9762\u6a21\u7248.doc"
    write_base_package_files(
        package_dir,
        screen_type=screen_type,
        requirement=requirement,
        style_reference_strength=style_reference_strength,
        candidate_options=candidate_options,
        reference_influence_percent=reference_influence_percent,
        adjustment_note=adjustment_note,
        adjustment_image_path=adjustment_image_path,
        source_note={
            "source_image": str(source),
            "p5_marked_reference": str(P5_MARKED_REFERENCE) if P5_MARKED_REFERENCE.exists() else "",
            "template_summary": read_template_summary(doc_path),
        },
    )
    return {"package_dir": str(package_dir), "main_ui": "main_ui.jpg", "candidate_options": candidate_options}


def select_candidate_option(package_dir: str | Path, candidate_id: str) -> dict[str, Any]:
    package_path = Path(package_dir)
    delivery_path = package_path / "delivery_report.json"
    delivery = read_json(delivery_path)
    options = [item for item in delivery.get("candidate_options", []) if isinstance(item, dict)]
    selected = next((item for item in options if item.get("candidate_id") == candidate_id), None)
    if not selected:
        raise ValueError(f"Candidate option not found: {candidate_id}")
    source = package_path / str(selected["file"])
    if not source.exists():
        raise FileNotFoundError(f"Candidate option image not found: {source}")
    shutil.copyfile(source, package_path / "main_ui.jpg")
    with Image.open(source) as image:
        image.convert("RGB").save(package_path / "ui_preview.png", "PNG")
    delivery["selected_candidate_id"] = candidate_id
    delivery["selected_candidate_file"] = selected["file"]
    delivery["updated_at"] = utc_now()
    write_json(delivery_path, delivery)
    candidate_manifest = package_path / "candidate_manifest.json"
    if candidate_manifest.exists():
        mark_candidate_components(package_path)
    return {"package_dir": str(package_path), "selected_candidate_id": candidate_id}


def mark_candidate_components(package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    main_ui_path = package_path / "main_ui.jpg"
    with Image.open(main_ui_path) as image:
        width, height = image.size
    candidates = main_ui_candidates(width, height)
    draw_candidate_preview(main_ui_path, package_path / "candidate_preview.jpg", candidates)
    write_json(
        package_path / "candidate_manifest.json",
        {
            "schema_version": "1.0",
            "package_type": "996-ready",
            "source_asset_id": "sprint20c-ui-production",
            "generation_job_id": package_path.name,
            "coordinate_space": "main_ui_pixels",
            "candidate_preview": "candidate_preview.jpg",
            "fixed_layout_zones": [
                "bottom_left_joystick",
                "right_skill",
                "right_top_map",
                "top_info",
                "bottom_status",
                "chat",
                "right_system_entry",
                "left_task",
                "left_status",
            ],
            "candidates": candidates,
            "updated_at": utc_now(),
        },
    )
    acceptance = read_json(package_path / "manual_acceptance.json")
    acceptance["updated_at"] = utc_now()
    write_json(package_path / "manual_acceptance.json", acceptance)
    write_manual_acceptance_components(package_path, candidates)
    return {"package_dir": str(package_path), "candidates_count": len(candidates)}


def load_candidate_manifest(package_dir: Path) -> dict[str, Any]:
    return read_json(package_dir / "candidate_manifest.json")


def save_candidate_manifest(package_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    write_json(package_dir / "candidate_manifest.json", manifest)


def write_manual_acceptance_components(package_dir: Path, candidates: list[dict[str, Any]]) -> None:
    acceptance_path = package_dir / "manual_acceptance.json"
    existing = read_json(acceptance_path) if acceptance_path.exists() else {}
    existing_components = {
        str(item.get("component_id")): item
        for item in existing.get("components", [])
        if isinstance(item, dict) and item.get("component_id")
    }
    components = []
    for candidate in candidates:
        component_id = str(candidate.get("component_id") or candidate.get("candidate_id") or "")
        previous = existing_components.get(component_id, {})
        components.append(
            {
                "component_id": component_id,
                "candidate_id": candidate.get("candidate_id") or component_id,
                "component_type": candidate.get("component_type"),
                "number": candidate.get("number"),
                "confirmed": bool(candidate.get("confirmed")),
                "level": candidate.get("level"),
                "production_category": candidate.get("production_category"),
                "layout_zone": candidate.get("layout_zone"),
                "shape_type": candidate.get("shape_type"),
                "layer_name": candidate.get("layer_name"),
                "layer_group": candidate.get("layer_group"),
                "layer_order": candidate.get("layer_order"),
                "slice_layer": candidate.get("slice_layer"),
                "bbox": candidate.get("bbox") or candidate.get("bounds"),
                "outline_points": candidate.get("outline_points", []),
                "output_file": candidate.get("image_path") or "",
                "transparent_warning": candidate.get("transparent_warning") or "",
                "review_status": previous.get("review_status", "pending"),
                "remarks": previous.get("remarks", ""),
            }
        )
    payload = {
        "schema_version": "1.0",
        "review_status": str(existing.get("review_status") or "pending"),
        "reviewer": str(existing.get("reviewer") or ""),
        "remarks": str(existing.get("remarks") or ""),
        "updated_at": utc_now(),
        "accepted_at": existing.get("accepted_at"),
        "accepted_by": str(existing.get("accepted_by") or ""),
        "components": components,
    }
    write_json(acceptance_path, payload)


def write_training_samples(package_dir: Path, candidates: list[dict[str, Any]]) -> Path:
    delivery = read_json(package_dir / "delivery_report.json")
    training_dir = package_dir / "training_samples" / "main_ui"
    training_dir.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    samples = [
        {
            "source_image": str(package_dir / "main_ui.jpg"),
            "source_image_file": "main_ui.jpg",
            "candidate_id": candidate.get("candidate_id") or candidate.get("component_id"),
            "component_id": candidate.get("component_id"),
            "confirmation_status": "confirmed" if candidate.get("confirmed") else "rejected",
            "user_confirmed": bool(candidate.get("confirmed")),
            "accepted": bool(candidate.get("confirmed")),
            "rejected_reason": "" if candidate.get("confirmed") else "not_confirmed_for_slicing",
            "component_type": candidate.get("component_type"),
            "type_changed": False,
            "level": candidate.get("level"),
            "layout_zone": candidate.get("layout_zone"),
            "shape_type": candidate.get("shape_type"),
            "layer_name": candidate.get("layer_name"),
            "layer_group": candidate.get("layer_group"),
            "layer_order": candidate.get("layer_order"),
            "slice_layer": candidate.get("slice_layer"),
            "bbox": candidate.get("bbox") or candidate.get("bounds"),
            "bbox_delta": {"x": 0, "y": 0, "width": 0, "height": 0},
            "outline_points": candidate.get("outline_points", []),
            "output_file": candidate.get("image_path") or "",
            "output_exists": bool(candidate.get("image_path") and (package_dir / str(candidate.get("image_path"))).exists()),
            "transparent_warning": candidate.get("transparent_warning") or "",
            "style_reference_strength": delivery.get("style_reference_strength", ""),
            "selected_candidate_id": delivery.get("selected_candidate_id", ""),
            "created_at": created_at,
        }
        for candidate in candidates
    ]
    payload = {
        "schema_version": "1.0",
        "screen_type": "main_ui",
        "package_dir": str(package_dir),
        "samples": samples,
        "created_at": created_at,
    }
    target = training_dir / "candidate_samples.json"
    write_json(target, payload)
    return target


def update_candidate_confirmation(package_dir: str | Path, candidate_id: str, confirmed: bool) -> dict[str, Any]:
    package_path = Path(package_dir)
    manifest = load_candidate_manifest(package_path)
    for candidate in manifest.get("candidates", []):
        if candidate.get("candidate_id") == candidate_id or candidate.get("component_id") == candidate_id:
            candidate["confirmed"] = confirmed
            save_candidate_manifest(package_path, manifest)
            candidates = [item for item in manifest.get("candidates", []) if isinstance(item, dict)]
            write_manual_acceptance_components(package_path, candidates)
            return candidate
    raise ValueError(f"Candidate not found: {candidate_id}")


def export_confirmed_components(package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    components_dir = package_path / "confirmed_components"
    components_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_candidate_manifest(package_path)
    candidates = [item for item in manifest.get("candidates", []) if isinstance(item, dict)]
    source_path = package_path / "main_ui.jpg"
    with Image.open(source_path) as source:
        source_rgba = source.convert("RGBA")
        source_rgb = source.convert("RGB")

    screen_output = components_dir / "screen_main_ui.jpg"
    source_rgb.save(screen_output, "JPEG", quality=92)

    exported: list[dict[str, Any]] = []
    manifest_components: list[dict[str, Any]] = []
    annotation_components: list[dict[str, Any]] = []
    for candidate in candidates:
        if not candidate.get("confirmed") or candidate.get("level") == "C":
            candidate["image_path"] = ""
            candidate["transparent_warning"] = ""
            continue
        box = candidate["bounds"]
        crop_box = (
            int(box["x"]),
            int(box["y"]),
            int(box["x"]) + int(box["width"]),
            int(box["y"]) + int(box["height"]),
        )
        fmt = str(candidate.get("output_format") or "png").lower()
        target_name = str(candidate.get("output_name") or output_name(candidate["component_id"], candidate["component_type"]))
        target = components_dir / target_name
        if fmt == "jpg":
            source_rgb.crop(crop_box).save(target, "JPEG", quality=92)
        else:
            source_rgba.crop(crop_box).save(target, "PNG")
        relative_file = f"confirmed_components/{target_name}"
        candidate["image_path"] = relative_file
        has_transparent = target.suffix.lower() == ".png" and image_has_transparent_pixels(target)
        warning = ""
        if candidate.get("transparent_required"):
            if target.suffix.lower() != ".png":
                warning = "A\u7ea7\u7ec4\u4ef6\u672a\u8f93\u51fa PNG"
            elif not has_transparent:
                warning = "\u6e90\u56fe\u65e0\u900f\u660e\u50cf\u7d20\uff0c\u5df2\u8f93\u51fa PNG \u4f46\u9700\u8981\u4eba\u5de5\u62a0\u900f\u660e\u80cc\u666f"
        candidate["transparent_warning"] = warning
        candidate["has_transparent_pixels"] = has_transparent
        item = {
            "component_id": candidate["component_id"],
            "component_type": candidate["component_type"],
            "component_name_zh": candidate.get("component_name", ""),
            "file": relative_file,
            "bounds": candidate["bounds"],
            "bbox": candidate.get("bbox") or candidate["bounds"],
            "layout_zone": candidate.get("layout_zone", ""),
            "shape_type": candidate.get("shape_type", "rect"),
            "layer_name": candidate.get("layer_name") or candidate["component_id"],
            "layer_group": candidate.get("layer_group") or candidate.get("layout_zone", ""),
            "layer_order": candidate.get("layer_order") or candidate.get("number"),
            "slice_layer": candidate.get("slice_layer")
            or {
                "name": candidate["component_id"],
                "group": candidate.get("layout_zone", ""),
                "order": candidate.get("number"),
                "component_type": candidate.get("component_type", ""),
            },
            "outline_points": candidate.get("outline_points", []),
            "transparent_png_required": bool(candidate.get("transparent_required")),
            "transparent_warning": warning,
        }
        manifest_components.append(item)
        annotation_components.append(
            {
                **item,
                "image": {
                    "file": relative_file,
                    "format": fmt,
                    "alpha": "required" if candidate.get("transparent_required") else "optional",
                    "transparent_background": bool(candidate.get("transparent_required") and not warning),
                },
                "review_status": "pending",
            }
        )
        exported.append(
            {
                "component_id": candidate["component_id"],
                "component_type": candidate["component_type"],
                "file": relative_file,
                "format": fmt,
                "has_transparent_pixels": has_transparent,
                "transparent_warning": warning,
            }
        )

    package_manifest = read_json(package_path / "manifest.json")
    package_manifest["components"] = manifest_components
    write_json(package_path / "manifest.json", package_manifest)
    annotation = read_json(package_path / "annotation.json")
    annotation["components"] = annotation_components
    write_json(package_path / "annotation.json", annotation)
    save_candidate_manifest(package_path, manifest)
    training_samples_path = write_training_samples(package_path, candidates)

    try:
        analyze_package(package_path)
    except (FileNotFoundError, ValueError) as exc:
        write_json(
            package_path / "production_review.json",
            {
                "schema_version": "1.0",
                "screen_type": "main_ui",
                "production_ready": False,
                "blockers": [str(exc)],
                "warnings": [],
                "generated_at": utc_now(),
            },
        )
    write_manual_acceptance_components(package_path, candidates)
    return {
        "package_dir": str(package_path),
        "exported": exported,
        "screen_file": "confirmed_components/screen_main_ui.jpg",
        "training_samples": str(training_samples_path),
    }


def create_main_ui_package(
    upload_root: str | Path,
    *,
    source_image: str | Path | None = None,
    template_doc: str | Path | None = None,
    job_id: str | None = None,
    auto_export: bool = True,
) -> dict[str, Any]:
    result = create_ui_package(
        upload_root,
        screen_type="main_ui",
        source_image=source_image,
        template_doc=template_doc,
        job_id=job_id,
    )
    mark_result = mark_candidate_components(result["package_dir"])
    export_result = export_confirmed_components(result["package_dir"]) if auto_export else {"exported": []}
    return {
        **result,
        "candidate_preview": "candidate_preview.jpg",
        "candidates_count": mark_result["candidates_count"],
        "exported_count": len(export_result["exported"]),
        "exported": export_result["exported"],
    }


def main_task_panel_rect() -> dict[str, int]:
    rect = MAIN_TASK_PANEL_SPEC["fixed_rect"]
    return {
        "x": int(rect["x"]),
        "y": int(rect["y"]),
        "width": int(rect["width"]),
        "height": int(rect["height"]),
    }


def main_task_panel_canvas() -> dict[str, int]:
    canvas = MAIN_TASK_PANEL_SPEC["canvas"]
    return {"width": int(canvas["width"]), "height": int(canvas["height"])}


def main_task_panel_production_status(
    *,
    generation_mode: str = "mock",
    requested_generation_mode: str | None = None,
    generation_provider: str = "",
    generation_job_id: str = "",
    production_ready: bool = False,
    visual_quality_status: str | None = None,
    fallback_used: bool = False,
    fallback_reason: str = "",
) -> dict[str, Any]:
    mode = generation_mode.strip().lower() or "mock"
    requested_mode = (requested_generation_mode or mode).strip().lower() or mode
    return {
        **MAIN_TASK_PANEL_PRODUCTION_STATUS,
        "requested_generation_mode": requested_mode,
        "generation_mode": mode,
        "generation_provider": generation_provider,
        "generation_job_id": generation_job_id,
        "production_ready": production_ready,
        "visual_quality_status": visual_quality_status or ("pending_review" if mode == "ai" and not fallback_used else "not_started"),
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
    }


def main_task_panel_status_from_sources(*sources: dict[str, Any]) -> dict[str, Any]:
    status = main_task_panel_production_status()
    for source in sources:
        for key in MAIN_TASK_PANEL_STATUS_KEYS:
            if key in source:
                status[key] = source[key]
    return status


def main_task_panel_ai_context(candidate_id: str, variant_index: int) -> dict[str, Any]:
    rect = main_task_panel_rect()
    canvas = main_task_panel_canvas()
    return {
        "candidate_id": candidate_id,
        "variant_index": variant_index,
        "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
        "name": MAIN_TASK_PANEL_SPEC["name"],
        "prompt": MAIN_TASK_PANEL_PROMPT,
        "prompt_template": MAIN_TASK_PANEL_PROMPT,
        "width": rect["width"],
        "height": rect["height"],
        "canvas_width": canvas["width"],
        "canvas_height": canvas["height"],
        "fixed_rect": rect,
        "transparent_required": bool(MAIN_TASK_PANEL_SPEC["transparent_required"]),
        "transparent_requested": True,
        "text_allowed": bool(MAIN_TASK_PANEL_SPEC["text_allowed"]),
        "forbidden_elements": list(MAIN_TASK_PANEL_SPEC["forbidden_elements"]),
        "negative_prompt": ", ".join(MAIN_TASK_PANEL_SPEC["forbidden_elements"]),
        "internal_structure": list(MAIN_TASK_PANEL_SPEC["internal_structure"]),
    }


def normalize_main_task_panel_candidate_image(path: Path) -> None:
    rect = main_task_panel_rect()
    with Image.open(path) as image:
        normalized = ImageOps.fit(
            image.convert("RGBA"),
            (rect["width"], rect["height"]),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        normalized.save(path, "PNG")


def draw_main_task_panel_placeholder(target: Path, variant_index: int) -> None:
    rect = main_task_panel_rect()
    width = rect["width"]
    height = rect["height"]
    palettes = [
        {"panel": (42, 31, 20, 188), "edge": (214, 166, 82, 235), "inner": (105, 77, 42, 145)},
        {"panel": (27, 29, 31, 196), "edge": (190, 139, 67, 235), "inner": (86, 72, 51, 150)},
        {"panel": (48, 36, 29, 184), "edge": (230, 183, 96, 235), "inner": (122, 86, 48, 138)},
    ]
    palette = palettes[(variant_index - 1) % len(palettes)]
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rounded_rectangle((6, 8, width - 7, height - 8), radius=14, fill=palette["panel"], outline=palette["edge"], width=3)
    draw.rounded_rectangle((14, 18, width - 15, 54), radius=8, fill=(78, 55, 32, 185), outline=palette["edge"], width=2)
    draw.line((26, 61, width - 26, 61), fill=(230, 184, 91, 150), width=1)

    row_top = 76
    row_gap = 48 if variant_index != 3 else 42
    rows = 4 if variant_index != 2 else 5
    for row in range(rows):
        y = row_top + row * row_gap
        if y + 30 > height - 56:
            break
        alpha = 118 if row % 2 == 0 else 92
        draw.rounded_rectangle((20, y, width - 22, y + 32), radius=6, fill=(*palette["inner"][:3], alpha), outline=(176, 132, 70, 95), width=1)
        draw.rectangle((32, y + 10, width - 54, y + 14), fill=(214, 172, 96, 84))
        draw.rectangle((32, y + 20, width - 86, y + 23), fill=(132, 106, 72, 70))
        if row:
            draw.line((24, y - 10, width - 24, y - 10), fill=(218, 170, 82, 58), width=1)

    fold_x = width - 51
    fold_y = height - 43
    draw.rounded_rectangle((fold_x, fold_y, fold_x + 31, fold_y + 24), radius=5, fill=(44, 37, 31, 210), outline=palette["edge"], width=2)
    draw.polygon(
        [(fold_x + 10, fold_y + 9), (fold_x + 22, fold_y + 9), (fold_x + 16, fold_y + 16)],
        fill=(223, 179, 95, 185),
    )

    for offset in (0, 1):
        draw.arc((12 + offset, 13 + offset, 70 + offset, 70 + offset), 180, 270, fill=(232, 190, 105, 115), width=2)
        draw.arc(
            (width - 70 - offset, 13 + offset, width - 12 - offset, 70 + offset),
            270,
            360,
            fill=(232, 190, 105, 115),
            width=2,
        )
        draw.arc(
            (12 + offset, height - 70 - offset, 70 + offset, height - 12 - offset),
            90,
            180,
            fill=(232, 190, 105, 115),
            width=2,
        )
        draw.arc(
            (width - 70 - offset, height - 70 - offset, width - 12 - offset, height - 12 - offset),
            0,
            90,
            fill=(232, 190, 105, 115),
            width=2,
        )

    for x in range(18, width - 18, 34):
        draw.line((x, 16, x + 12, 16), fill=(247, 207, 118, 72), width=1)
    image.save(target, "PNG")


def main_task_panel_candidate_record(
    candidate_id: str,
    image_path: str,
    variant_index: int,
    *,
    status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rect = main_task_panel_rect()
    canvas = main_task_panel_canvas()
    production_status = status or main_task_panel_production_status()
    return {
        "candidate_id": candidate_id,
        "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
        "name": MAIN_TASK_PANEL_SPEC["name"],
        "width": rect["width"],
        "height": rect["height"],
        "target_x": rect["x"],
        "target_y": rect["y"],
        "canvas_width": canvas["width"],
        "canvas_height": canvas["height"],
        "fixed_rect": rect,
        "prompt": MAIN_TASK_PANEL_PROMPT,
        "image_path": image_path,
        "preview_path": image_path,
        "selected": False,
        "accepted": False,
        **production_status,
        "variant_index": variant_index,
        "transparent_required": bool(MAIN_TASK_PANEL_SPEC["transparent_required"]),
        "text_allowed": bool(MAIN_TASK_PANEL_SPEC["text_allowed"]),
        "forbidden_elements": list(MAIN_TASK_PANEL_SPEC["forbidden_elements"]),
        "internal_structure": list(MAIN_TASK_PANEL_SPEC["internal_structure"]),
    }


def main_task_panel_package_response(package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    candidate_path = package_path / "candidate_manifest.json"
    delivery_path = package_path / "delivery_report.json"
    candidate_manifest = read_json(candidate_path) if candidate_path.exists() else {"candidates": []}
    delivery = read_json(delivery_path) if delivery_path.exists() else {}
    candidates = [item for item in candidate_manifest.get("candidates", []) if isinstance(item, dict)]
    selected_candidate_id = str(delivery.get("selected_candidate_id") or "")
    canvas_preview_path = str(delivery.get("canvas_preview_path") or "")
    component_file = str(delivery.get("component_file") or "")
    production_status = main_task_panel_status_from_sources(candidate_manifest, delivery)
    manifest_path = "manifest.json" if (package_path / "manifest.json").exists() else ""
    component_record_path = "component_record.json" if (package_path / "component_record.json").exists() else ""
    export_dir = package_path / "components"
    return {
        "package_dir": str(package_path),
        "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
        "name": MAIN_TASK_PANEL_SPEC["name"],
        **production_status,
        "canvas": main_task_panel_canvas(),
        "fixed_rect": main_task_panel_rect(),
        "max_width": MAIN_TASK_PANEL_SPEC["max_width"],
        "transparent_required": MAIN_TASK_PANEL_SPEC["transparent_required"],
        "text_allowed": MAIN_TASK_PANEL_SPEC["text_allowed"],
        "forbidden_elements": list(MAIN_TASK_PANEL_SPEC["forbidden_elements"]),
        "internal_structure": list(MAIN_TASK_PANEL_SPEC["internal_structure"]),
        "prompt": MAIN_TASK_PANEL_PROMPT,
        "candidates": candidates,
        "selected_candidate_id": selected_candidate_id,
        "accepted": bool(delivery.get("accepted", False)),
        "export_dir": export_dir.as_posix() if export_dir.exists() else "",
        "canvas_preview_path": canvas_preview_path,
        "canvas_preview_file_path": (package_path / canvas_preview_path).as_posix()
        if canvas_preview_path and (package_path / canvas_preview_path).exists()
        else "",
        "component_file": component_file,
        "component_path": (package_path / component_file).as_posix() if component_file and (package_path / component_file).exists() else "",
        "manifest_path": manifest_path,
        "manifest_file_path": (package_path / manifest_path).as_posix() if manifest_path else "",
        "component_record_path": component_record_path,
        "component_record_file_path": (package_path / component_record_path).as_posix() if component_record_path else "",
        "updated_at": str(delivery.get("updated_at") or ""),
    }


def create_main_task_panel_package(
    upload_root: str | Path,
    *,
    job_id: str | None = None,
    generation_mode: str = "mock",
    ai_candidate_generator: MainTaskPanelAiCandidateGenerator | None = None,
) -> dict[str, Any]:
    upload_path = Path(upload_root)
    package_dir = upload_path / "996-ready" / "HUD_MODULES" / "main_task_panel" / (job_id or safe_job_id("main-task-panel"))
    package_dir.mkdir(parents=True, exist_ok=True)
    candidates_dir = package_dir / "candidates"
    candidates_dir.mkdir(exist_ok=True)

    requested_generation_mode = generation_mode.strip().lower() or "mock"
    if requested_generation_mode not in MAIN_TASK_PANEL_GENERATION_MODES:
        raise ValueError("generation_mode must be mock or ai")

    candidates: list[dict[str, Any]] = []
    production_status = main_task_panel_production_status(requested_generation_mode=requested_generation_mode)

    if requested_generation_mode == "ai":
        generated_items: list[tuple[str, str, int, dict[str, Any]]] = []
        try:
            if ai_candidate_generator is None:
                raise RuntimeError("AI generation provider is not configured for main_task_panel")
            for index in range(1, 4):
                candidate_id = f"main_task_panel_candidate_{index}"
                image_path = f"candidates/{candidate_id}.png"
                target = package_dir / image_path
                metadata = ai_candidate_generator(target, index, main_task_panel_ai_context(candidate_id, index)) or {}
                if not target.exists():
                    raise RuntimeError(f"AI generator did not create candidate image: {image_path}")
                normalize_main_task_panel_candidate_image(target)
                generated_items.append((candidate_id, image_path, index, metadata))

            provider = next((str(item[3].get("generation_provider") or "") for item in generated_items if item[3].get("generation_provider")), "")
            job_ids = [str(item[3].get("generation_job_id") or "") for item in generated_items if item[3].get("generation_job_id")]
            production_status = main_task_panel_production_status(
                generation_mode="ai",
                requested_generation_mode="ai",
                generation_provider=provider or "existing_project_provider_name",
                generation_job_id=",".join(job_ids),
                visual_quality_status="pending_review",
            )
            for candidate_id, image_path, index, _metadata in generated_items:
                candidates.append(main_task_panel_candidate_record(candidate_id, image_path, index, status=production_status))
        except Exception as exc:
            production_status = main_task_panel_production_status(
                generation_mode="mock",
                requested_generation_mode="ai",
                fallback_used=True,
                fallback_reason=f"AI generation failed: {exc}",
                visual_quality_status="not_started",
            )
            candidates = []
            for index in range(1, 4):
                candidate_id = f"main_task_panel_candidate_{index}"
                image_path = f"candidates/{candidate_id}.png"
                draw_main_task_panel_placeholder(package_dir / image_path, index)
                candidates.append(main_task_panel_candidate_record(candidate_id, image_path, index, status=production_status))
    else:
        for index in range(1, 4):
            candidate_id = f"main_task_panel_candidate_{index}"
            image_path = f"candidates/{candidate_id}.png"
            draw_main_task_panel_placeholder(package_dir / image_path, index)
            candidates.append(main_task_panel_candidate_record(candidate_id, image_path, index, status=production_status))

    generated_at = utc_now()
    write_json(
        package_dir / "candidate_manifest.json",
        {
            "schema_version": "1.0",
            "package_type": "996-hud-module-candidates",
            "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
            "name": MAIN_TASK_PANEL_SPEC["name"],
            "canvas": main_task_panel_canvas(),
            "fixed_rect": main_task_panel_rect(),
            "prompt": MAIN_TASK_PANEL_PROMPT,
            **production_status,
            "candidates": candidates,
            "created_at": generated_at,
            "updated_at": generated_at,
        },
    )
    write_json(
        package_dir / "delivery_report.json",
        {
            "schema_version": "1.0",
            "workflow": "main_task_panel_hud_module_loop",
            "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
            **production_status,
            "selected_candidate_id": "",
            "canvas_preview_path": "",
            "component_file": "",
            "accepted": False,
            "created_at": generated_at,
            "updated_at": generated_at,
        },
    )
    write_json(
        package_dir / "manifest.json",
        {
            "schema_version": "1.0",
            "package_type": "996-hud-module",
            "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
            "name": MAIN_TASK_PANEL_SPEC["name"],
            **production_status,
            "canvas": main_task_panel_canvas(),
            "components": [],
            "created_at": generated_at,
            "updated_at": generated_at,
        },
    )
    return main_task_panel_package_response(package_dir)


def selected_main_task_panel_candidate(package_dir: Path) -> dict[str, Any]:
    response = main_task_panel_package_response(package_dir)
    selected_candidate_id = response["selected_candidate_id"]
    if not selected_candidate_id:
        raise ValueError("No main_task_panel candidate selected")
    for candidate in response["candidates"]:
        if candidate.get("candidate_id") == selected_candidate_id:
            image_path = package_dir / str(candidate.get("image_path") or "")
            if not image_path.exists():
                raise FileNotFoundError(f"Selected candidate image not found: {image_path}")
            return candidate
    raise ValueError(f"Selected candidate not found: {selected_candidate_id}")


def select_main_task_panel_candidate(package_dir: str | Path, candidate_id: str) -> dict[str, Any]:
    package_path = Path(package_dir)
    manifest = read_json(package_path / "candidate_manifest.json")
    candidates = [item for item in manifest.get("candidates", []) if isinstance(item, dict)]
    if not any(candidate.get("candidate_id") == candidate_id for candidate in candidates):
        raise ValueError(f"Candidate not found: {candidate_id}")
    for candidate in candidates:
        selected = candidate.get("candidate_id") == candidate_id
        candidate["selected"] = selected
        candidate["accepted"] = False
    manifest["candidates"] = candidates
    write_json(package_path / "candidate_manifest.json", {**manifest, "updated_at": utc_now()})

    delivery = read_json(package_path / "delivery_report.json")
    delivery.update({"selected_candidate_id": candidate_id, "accepted": False, "updated_at": utc_now()})
    write_json(package_path / "delivery_report.json", delivery)
    return main_task_panel_package_response(package_path)


def preview_main_task_panel_on_canvas(package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    candidate = selected_main_task_panel_candidate(package_path)
    rect = main_task_panel_rect()
    canvas = main_task_panel_canvas()
    source_path = package_path / str(candidate["image_path"])

    preview = Image.new("RGBA", (canvas["width"], canvas["height"]), (16, 18, 22, 255))
    draw = ImageDraw.Draw(preview, "RGBA")
    for y in range(0, canvas["height"], 72):
        draw.line((0, y, canvas["width"], y), fill=(255, 255, 255, 12), width=1)
    for x in range(0, canvas["width"], 96):
        draw.line((x, 0, x, canvas["height"]), fill=(255, 255, 255, 9), width=1)
    with Image.open(source_path) as source:
        module_image = source.convert("RGBA").resize((rect["width"], rect["height"]))
    preview.alpha_composite(module_image, (rect["x"], rect["y"]))
    preview_path = "canvas_preview.png"
    preview.save(package_path / preview_path, "PNG")

    delivery = read_json(package_path / "delivery_report.json")
    delivery.update({"canvas_preview_path": preview_path, "updated_at": utc_now()})
    write_json(package_path / "delivery_report.json", delivery)
    return {
        **main_task_panel_package_response(package_path),
        "canvas_preview_path": preview_path,
        "canvas_width": canvas["width"],
        "canvas_height": canvas["height"],
        "target_rect": rect,
    }


def accept_main_task_panel_candidate(package_dir: str | Path) -> dict[str, Any]:
    package_path = Path(package_dir)
    candidate = selected_main_task_panel_candidate(package_path)
    preview_main_task_panel_on_canvas(package_path)
    candidate_manifest = read_json(package_path / "candidate_manifest.json")
    delivery_report = read_json(package_path / "delivery_report.json")
    production_status = main_task_panel_status_from_sources(candidate_manifest, delivery_report, candidate)

    components_dir = package_path / "components"
    components_dir.mkdir(exist_ok=True)
    component_file = "components/main_task_panel.png"
    source_path = package_path / str(candidate["image_path"])
    with Image.open(source_path) as source:
        source.convert("RGBA").save(package_path / component_file, "PNG")

    rect = main_task_panel_rect()
    canvas = main_task_panel_canvas()
    generated_at = utc_now()
    component_record = {
        "schema_version": "1.0",
        "component_id": "main_task_panel",
        "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
        "name": MAIN_TASK_PANEL_SPEC["name"],
        "selected_candidate_id": candidate["candidate_id"],
        "file": component_file,
        "bounds": rect,
        "width": rect["width"],
        "height": rect["height"],
        "target_x": rect["x"],
        "target_y": rect["y"],
        "canvas_width": canvas["width"],
        "canvas_height": canvas["height"],
        "transparent_required": True,
        "prompt": MAIN_TASK_PANEL_PROMPT,
        "accepted": True,
        **production_status,
        "updated_at": generated_at,
    }
    write_json(package_path / "component_record.json", component_record)
    write_json(
        package_path / "manifest.json",
        {
            "schema_version": "1.0",
            "package_type": "996-hud-module",
            "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
            "name": MAIN_TASK_PANEL_SPEC["name"],
            **production_status,
            "canvas": canvas,
            "fixed_rect": rect,
            "components": [
                {
                    "component_id": "main_task_panel",
                    "module_id": MAIN_TASK_PANEL_SPEC["module_id"],
                    "name": MAIN_TASK_PANEL_SPEC["name"],
                    "file": component_file,
                    "bounds": rect,
                    "width": rect["width"],
                    "height": rect["height"],
                    "target_x": rect["x"],
                    "target_y": rect["y"],
                    "canvas_width": canvas["width"],
                    "canvas_height": canvas["height"],
                    "transparent_png_required": True,
                    **production_status,
                    "source_candidate_id": candidate["candidate_id"],
                }
            ],
            "updated_at": generated_at,
        },
    )

    manifest = candidate_manifest
    for item in manifest.get("candidates", []):
        if isinstance(item, dict):
            item["accepted"] = item.get("candidate_id") == candidate["candidate_id"]
    write_json(package_path / "candidate_manifest.json", {**manifest, "updated_at": generated_at})

    delivery = delivery_report
    delivery.update({**production_status, "component_file": component_file, "accepted": True, "updated_at": generated_at})
    write_json(package_path / "delivery_report.json", delivery)
    return {**main_task_panel_package_response(package_path), "component_file": component_file}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sprint20C UI production chain.")
    parser.add_argument("upload_root")
    parser.add_argument("--source-image", default="")
    parser.add_argument("--template-doc", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--no-export", action="store_true")
    args = parser.parse_args()
    result = create_main_ui_package(
        args.upload_root,
        source_image=args.source_image or None,
        template_doc=args.template_doc or None,
        job_id=args.job_id or None,
        auto_export=not args.no_export,
    )
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
