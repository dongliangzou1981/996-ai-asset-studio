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


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_job_id(prefix: str = "ui-production") -> str:
    return datetime.now(timezone.utc).strftime(f"{prefix}-%Y%m%d-%H%M%S")


def bounds(width: int, height: int, x: float, y: float, w: float, h: float) -> dict[str, int]:
    left = max(0, min(width - 1, round(width * x)))
    top = max(0, min(height - 1, round(height * y)))
    box_width = max(1, min(width - left, round(width * w)))
    box_height = max(1, min(height - top, round(height * h)))
    return {"x": left, "y": top, "width": box_width, "height": box_height}


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
        ("screen_main_ui", "\u5b8c\u6574\u4e3b\u754c\u9762", "screen", 0.0, 0.0, 1.0, 1.0, True),
        ("top_player_info", "\u9876\u90e8\u89d2\u8272\u72b6\u6001\u533a", "hud_bar", 0.03, 0.01, 0.19, 0.20, True),
        ("task_panel", "\u5de6\u4fa7\u4efb\u52a1\u533a", "panel", 0.0, 0.01, 0.21, 0.47, True),
        ("status_panel", "\u5de6\u4fa7\u72b6\u6001\u533a", "panel", 0.0, 0.31, 0.21, 0.18, True),
        ("left_joystick", "\u5de6\u4e0b\u6447\u6746", "joystick", 0.03, 0.66, 0.14, 0.26, True),
        ("bottom_hud", "\u5e95\u90e8\u4e3b HUD", "hud_bar", 0.18, 0.74, 0.55, 0.22, True),
        ("skill_01", "\u6280\u80fd\u6309\u94ae 1", "skill_button", 0.72, 0.62, 0.08, 0.14, True),
        ("skill_02", "\u6280\u80fd\u6309\u94ae 2", "skill_button", 0.80, 0.56, 0.08, 0.14, True),
        ("skill_03", "\u6280\u80fd\u6309\u94ae 3", "skill_button", 0.87, 0.65, 0.08, 0.14, True),
        ("skill_04", "\u6280\u80fd\u6309\u94ae 4", "skill_button", 0.77, 0.76, 0.08, 0.14, True),
        ("bag_entry", "\u80cc\u5305\u5165\u53e3", "system_entry_icon", 0.78, 0.08, 0.055, 0.095, True),
        ("role_entry", "\u89d2\u8272\u5165\u53e3", "system_entry_icon", 0.84, 0.08, 0.055, 0.095, True),
        ("shop_entry", "\u5546\u57ce\u5165\u53e3", "system_entry_icon", 0.90, 0.08, 0.055, 0.095, True),
        ("activity_entry", "\u6d3b\u52a8\u5165\u53e3", "system_entry_icon", 0.77, 0.0, 0.08, 0.12, True),
        ("mini_map", "\u53f3\u4e0a\u5c0f\u5730\u56fe", "map", 0.85, 0.01, 0.15, 0.23, True),
        ("chat_panel", "\u804a\u5929\u533a", "chat", 0.39, 0.82, 0.22, 0.16, True),
        ("currency", "\u8d27\u5e01\u56fe\u6807", "currency_icon", 0.28, 0.96, 0.035, 0.035, True),
        ("dynamic_text", "\u52a8\u6001\u6570\u503c\u6587\u5b57", "dynamic_content", 0.39, 0.03, 0.16, 0.06, False),
    ]
    candidates = []
    for index, (component_id, name, component_type, x, y, w, h, confirmed) in enumerate(specs, 1):
        level = classify_level(component_type)
        candidates.append(
            {
                "candidate_id": component_id,
                "component_id": component_id,
                "component_name": name,
                "component_type": component_type,
                "number": index,
                "bounds": bounds(width, height, x, y, w, h),
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
        )
    return candidates


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
    local_copy = upload_root / "sprint20b-source" / "p5_main_ui.jpg"
    if local_copy.exists():
        return local_copy
    return P5_MAIN_UI_SOURCE


def write_base_package_files(
    package_dir: Path,
    *,
    screen_type: str,
    requirement: str,
    style_reference_strength: str,
    source_note: dict[str, Any],
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
    if P5_MARKED_REFERENCE.exists():
        shutil.copyfile(P5_MARKED_REFERENCE, reference_dir / "p5_marked_reference.png")
    doc_path = Path(template_doc) if template_doc else Path.home() / "Desktop" / "\u4e3b\u754c\u9762\u6a21\u7248.doc"
    write_base_package_files(
        package_dir,
        screen_type=screen_type,
        requirement=requirement,
        style_reference_strength=style_reference_strength,
        source_note={
            "source_image": str(source),
            "p5_marked_reference": str(P5_MARKED_REFERENCE) if P5_MARKED_REFERENCE.exists() else "",
            "template_summary": read_template_summary(doc_path),
        },
    )
    return {"package_dir": str(package_dir), "main_ui": "main_ui.jpg"}


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
            "candidates": candidates,
            "updated_at": utc_now(),
        },
    )
    acceptance = read_json(package_path / "manual_acceptance.json")
    acceptance["components"] = [
        {
            "component_id": item["component_id"],
            "component_type": item["component_type"],
            "number": item["number"],
            "confirmed": item["confirmed"],
            "review_status": "pending",
            "remarks": "",
        }
        for item in candidates
    ]
    acceptance["updated_at"] = utc_now()
    write_json(package_path / "manual_acceptance.json", acceptance)
    return {"package_dir": str(package_path), "candidates_count": len(candidates)}


def load_candidate_manifest(package_dir: Path) -> dict[str, Any]:
    return read_json(package_dir / "candidate_manifest.json")


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
