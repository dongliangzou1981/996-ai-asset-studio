from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_production_package import analyze_package


P5_MAIN_UI_SOURCE = Path(r"\\192.168.0.173\tools\ps\P5\Z主界面\新主界面1.jpg")
P5_MARKED_REFERENCE = Path(r"\\192.168.0.173\tools\ps\P5\Z主界面\新主界面1标注.png")

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

PNG_TYPES = LEVEL_A_TYPES
JPG_TYPES = {"screen", "background", "panel", "hud_bar", "chat", "map", "skill_bar"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_job_id() -> str:
    return datetime.now(timezone.utc).strftime("main-ui-%Y%m%d-%H%M%S")


def bounds(width: int, height: int, x: float, y: float, w: float, h: float) -> dict[str, int]:
    left = max(0, min(width - 1, round(width * x)))
    top = max(0, min(height - 1, round(height * y)))
    box_width = max(1, min(width - left, round(width * w)))
    box_height = max(1, min(height - top, round(height * h)))
    return {"x": left, "y": top, "width": box_width, "height": box_height}


def classify_level(component_type: str) -> str:
    if component_type in LEVEL_A_TYPES:
        return "A"
    if component_type in {"panel", "hud_bar", "chat", "map", "skill_bar", "screen"}:
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
    if component_type in {"equipment_slot"}:
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
        return "确认切图"
    if level == "B":
        return "确认切图或人工复核"
    return "默认不切"


def default_candidates(width: int, height: int) -> list[dict[str, Any]]:
    specs = [
        ("screen_main_ui", "完整主界面", "screen", 0.0, 0.0, 1.0, 1.0, True),
        ("bottom_hud", "底部主 HUD", "hud_bar", 0.18, 0.74, 0.55, 0.22, True),
        ("left_joystick", "左侧摇杆", "joystick", 0.03, 0.66, 0.14, 0.26, True),
        ("skill_01", "技能按钮 1", "skill_button", 0.72, 0.62, 0.08, 0.14, True),
        ("skill_02", "技能按钮 2", "skill_button", 0.80, 0.56, 0.08, 0.14, True),
        ("skill_03", "技能按钮 3", "skill_button", 0.87, 0.65, 0.08, 0.14, True),
        ("skill_04", "技能按钮 4", "skill_button", 0.77, 0.76, 0.08, 0.14, True),
        ("bag_entry", "背包入口", "system_entry_icon", 0.78, 0.08, 0.055, 0.095, True),
        ("role_entry", "角色入口", "system_entry_icon", 0.84, 0.08, 0.055, 0.095, True),
        ("shop_entry", "商城入口", "system_entry_icon", 0.90, 0.08, 0.055, 0.095, True),
        ("mini_map", "小地图面板", "map", 0.02, 0.03, 0.22, 0.18, True),
        ("chat_panel", "聊天区域", "chat", 0.02, 0.45, 0.25, 0.18, True),
        ("currency", "货币图标", "currency_icon", 0.34, 0.03, 0.045, 0.075, True),
        ("dynamic_text", "动态数值文字", "dynamic_content", 0.39, 0.03, 0.16, 0.06, False),
    ]
    candidates = []
    for index, (component_id, name, component_type, x, y, w, h, confirmed) in enumerate(specs, 1):
        level = classify_level(component_type)
        category = production_category(component_type, level)
        fmt = output_format(component_type, level)
        candidates.append(
            {
                "candidate_id": component_id,
                "component_id": component_id,
                "component_name": name,
                "component_type": component_type,
                "number": index,
                "bounds": bounds(width, height, x, y, w, h),
                "level": level,
                "production_category": category,
                "recommended_action": recommended_action(level),
                "confirmed": confirmed,
                "output_format": fmt,
                "output_name": output_name(component_id, component_type),
                "transparent_required": level == "A",
                "transparent_warning": "",
                "image_path": "",
            }
        )
    return candidates


def load_badge_font(size: int) -> ImageFont.ImageFont:
    for font_path in [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ]:
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
        draw.rectangle([x, y, x + width, y + height], outline=color, width=max(2, preview.width // 512))
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
        data = template_doc.read_bytes()
        sample = data[: min(len(data), 4_000_000)]
        text = sample.decode("utf-16le", errors="ignore")
        for keyword in ["主界面", "背包", "角色", "商城", "活动", "技能", "摇杆", "按钮"]:
            if keyword in text:
                notes.append(keyword)
    except OSError as exc:
        return {"template_doc_found": True, "template_doc": str(template_doc), "notes": [], "read_warning": str(exc)}
    return {"template_doc_found": True, "template_doc": str(template_doc), "notes": sorted(set(notes))}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def image_has_transparent_pixels(path: Path) -> bool:
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        minimum, _ = alpha.getextrema()
        return minimum < 255


def write_base_package_files(package_dir: Path, candidates: list[dict[str, Any]], source_note: dict[str, Any]) -> None:
    generated_at = utc_now()
    manifest = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "template": "main_ui",
        "generation_job_id": package_dir.name,
        "ui_preview": "ui_preview.png",
        "main_ui": "main_ui.jpg",
        "components_dir": "confirmed_components",
        "components": [],
    }
    annotation = {
        "schema_version": "1.0",
        "template": "main_ui",
        "coordinate_space": "main_ui_pixels",
        "components": [],
    }
    candidate_manifest = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "source_asset_id": "sprint20b-main-ui",
        "generation_job_id": package_dir.name,
        "coordinate_space": "main_ui_pixels",
        "candidate_preview": "candidate_preview.jpg",
        "candidates": candidates,
        "updated_at": generated_at,
    }
    acceptance = {
        "schema_version": "1.0",
        "review_status": "pending",
        "reviewer": "",
        "remarks": "",
        "updated_at": generated_at,
        "accepted_at": None,
        "accepted_by": "",
        "components": [
            {
                "component_id": item["component_id"],
                "component_type": item["component_type"],
                "number": item["number"],
                "confirmed": item["confirmed"],
                "review_status": "pending",
                "remarks": "",
            }
            for item in candidates
        ],
    }
    delivery_report = {
        "screen_type": "main_ui",
        "generation_job_id": package_dir.name,
        "workflow": "sprint20b_main_ui_production_chain",
        "generated_at": generated_at,
        "source_note": source_note,
    }
    write_json(package_dir / "manifest.json", manifest)
    write_json(package_dir / "annotation.json", annotation)
    write_json(package_dir / "candidate_manifest.json", candidate_manifest)
    write_json(package_dir / "manual_acceptance.json", acceptance)
    write_json(package_dir / "delivery_report.json", delivery_report)


def load_candidate_manifest(package_dir: Path) -> dict[str, Any]:
    return json.loads((package_dir / "candidate_manifest.json").read_text(encoding="utf-8"))


def save_candidate_manifest(package_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    write_json(package_dir / "candidate_manifest.json", manifest)


def update_candidate_confirmation(package_dir: str | Path, candidate_id: str, confirmed: bool) -> dict[str, Any]:
    package_path = Path(package_dir)
    manifest = load_candidate_manifest(package_path)
    for candidate in manifest.get("candidates", []):
        if candidate.get("candidate_id") == candidate_id or candidate.get("component_id") == candidate_id:
            candidate["confirmed"] = confirmed
            save_candidate_manifest(package_path, manifest)
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
        if not candidate.get("confirmed"):
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
        warning = ""
        if candidate.get("transparent_required"):
            if target.suffix.lower() != ".png":
                warning = "A级组件未输出 PNG"
            elif not image_has_transparent_pixels(target):
                warning = "源图无透明像素，已输出 PNG 但需要人工抠透明背景"
        candidate["transparent_warning"] = warning
        item = {
            "component_id": candidate["component_id"],
            "component_type": candidate["component_type"],
            "component_name_zh": candidate.get("component_name", ""),
            "file": relative_file,
            "bounds": candidate["bounds"],
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
                "transparent_warning": warning,
            }
        )

    package_manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
    package_manifest["components"] = manifest_components
    write_json(package_path / "manifest.json", package_manifest)
    annotation = json.loads((package_path / "annotation.json").read_text(encoding="utf-8"))
    annotation["components"] = annotation_components
    write_json(package_path / "annotation.json", annotation)
    save_candidate_manifest(package_path, manifest)

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

    return {"package_dir": str(package_path), "exported": exported, "screen_file": "confirmed_components/screen_main_ui.jpg"}


def create_main_ui_package(
    upload_root: str | Path,
    *,
    source_image: str | Path | None = None,
    template_doc: str | Path | None = None,
    job_id: str | None = None,
    auto_export: bool = True,
) -> dict[str, Any]:
    upload_path = Path(upload_root)
    source = Path(source_image) if source_image else P5_MAIN_UI_SOURCE
    if not source.exists():
        raise FileNotFoundError(f"Main UI source image not found: {source}")
    doc_path = Path(template_doc) if template_doc else Path.home() / "Desktop" / "主界面模版.doc"
    package_dir = upload_path / "996-ready" / "SPRINT20B_MAIN_UI" / "main_ui" / (job_id or safe_job_id())
    package_dir.mkdir(parents=True, exist_ok=True)
    reference_dir = package_dir / "reference"
    reference_dir.mkdir(exist_ok=True)

    main_ui_path = package_dir / "main_ui.jpg"
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        rgb.save(main_ui_path, "JPEG", quality=92)
        rgb.save(package_dir / "ui_preview.png", "PNG")
        width, height = rgb.size
    if P5_MARKED_REFERENCE.exists():
        shutil.copyfile(P5_MARKED_REFERENCE, reference_dir / "p5_marked_reference.png")
    candidates = default_candidates(width, height)
    draw_candidate_preview(main_ui_path, package_dir / "candidate_preview.jpg", candidates)
    source_note = {
        "source_image": str(source),
        "p5_marked_reference": str(P5_MARKED_REFERENCE) if P5_MARKED_REFERENCE.exists() else "",
        "template_summary": read_template_summary(doc_path),
    }
    write_base_package_files(package_dir, candidates, source_note)
    export_result = export_confirmed_components(package_dir) if auto_export else {"exported": []}
    return {
        "package_dir": str(package_dir),
        "main_ui": "main_ui.jpg",
        "candidate_preview": "candidate_preview.jpg",
        "candidates_count": len(candidates),
        "exported_count": len(export_result["exported"]),
        "exported": export_result["exported"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Sprint20B main UI production chain.")
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
