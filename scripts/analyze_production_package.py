from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


LEVEL_A_TYPES = {
    "button",
    "icon",
    "input",
    "tab",
    "skill_icon",
    "equipment_slot",
    "close_button",
    "currency_icon",
}
LEVEL_B_TYPES = {
    "panel",
    "chat",
    "map",
    "skill_bar",
    "hud_bar",
    "activity_panel",
    "inventory_panel",
    "role_panel",
    "shop_panel",
    "bar",
}
LEVEL_C_TYPES = {
    "text",
    "number",
    "red_dot",
    "dynamic_content",
    "effect",
    "decoration",
    "unknown",
    "background",
}

SCREEN_TYPES = {"screen", "background", "screen_background", "full_screen", "ui_preview"}
EFFECT_TYPES = {"effect", "decoration", "red_dot"}
IGNORE_TYPES = {"text", "number", "dynamic_content", "unknown"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, *, required: bool, warnings: list[str]) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required package file missing: {path.name}")
        warnings.append(f"Optional package file missing: {path.name}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        if required:
            raise ValueError(f"Invalid JSON in required package file: {path.name}") from exc
        warnings.append(f"Optional package file has invalid JSON: {path.name}")
        return {}
    return data if isinstance(data, dict) else {}


def normalize_type(value: Any) -> str:
    text = str(value or "unknown").strip().lower()
    if text.endswith("_candidate"):
        text = text.removesuffix("_candidate")
    return text or "unknown"


def classify_level(component_id: str, component_type: str) -> str:
    normalized_id = normalize_type(component_id)
    normalized_type = normalize_type(component_type)
    combined = f"{normalized_id} {normalized_type}"
    if normalized_type in LEVEL_A_TYPES or any(item in combined for item in LEVEL_A_TYPES):
        return "A"
    if normalized_type in LEVEL_B_TYPES or any(item in combined for item in LEVEL_B_TYPES):
        return "B"
    if normalized_type in LEVEL_C_TYPES or any(item in combined for item in LEVEL_C_TYPES):
        return "C"
    return "C"


def classify_production_category(component_id: str, component_type: str, level: str) -> str:
    normalized_id = normalize_type(component_id)
    normalized_type = normalize_type(component_type)
    combined = f"{normalized_id} {normalized_type}"
    if normalized_type in SCREEN_TYPES or any(item in combined for item in SCREEN_TYPES):
        return "Screen"
    if normalized_type in EFFECT_TYPES or any(item in combined for item in EFFECT_TYPES):
        return "Effect"
    if normalized_type in IGNORE_TYPES or any(item in combined for item in IGNORE_TYPES):
        return "Ignore"
    if level == "A":
        return "Atomic"
    if level == "B":
        return "Panel"
    return "Ignore"


def component_file(component: dict[str, Any]) -> str:
    image = component.get("image")
    if isinstance(image, dict) and image.get("file"):
        return str(image["file"])
    for key in ["file", "image_path", "path"]:
        if component.get(key):
            return str(component[key])
    return ""


def transparency_required(component: dict[str, Any], level: str) -> bool:
    if level == "A":
        return True
    transparent = component.get("transparent")
    if isinstance(transparent, dict) and "required" in transparent:
        return bool(transparent["required"])
    if "transparent_png_required" in component:
        return bool(component["transparent_png_required"])
    image = component.get("image")
    if isinstance(image, dict) and str(image.get("alpha") or "").lower() == "required":
        return True
    return False


def inspect_png(package_dir: Path, file_name: str, required: bool) -> dict[str, Any]:
    path = package_dir / file_name if file_name else package_dir / "__missing__"
    check: dict[str, Any] = {
        "file": file_name,
        "file_exists": path.exists() and path.is_file(),
        "is_png": False,
        "image_mode": "",
        "has_alpha_channel": False,
        "has_transparent_pixels": False,
        "is_fully_transparent": False,
        "is_fully_opaque": False,
        "required_transparency": required,
    }
    if not check["file_exists"]:
        return check
    try:
        with Image.open(path) as image:
            check["is_png"] = image.format == "PNG"
            check["image_mode"] = image.mode
            check["has_alpha_channel"] = image.mode in {"RGBA", "LA"} or "transparency" in image.info
            if check["has_alpha_channel"]:
                alpha = image.convert("RGBA").getchannel("A")
                minimum, maximum = alpha.getextrema()
                check["has_transparent_pixels"] = minimum < 255
                check["is_fully_transparent"] = maximum == 0
                check["is_fully_opaque"] = minimum == 255
            else:
                check["is_fully_opaque"] = True
    except (OSError, UnidentifiedImageError):
        check["is_png"] = False
    return check


def transparency_findings(component_id: str, check: dict[str, Any]) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    warnings: list[str] = []
    if not check["required_transparency"]:
        return blockers, warnings
    prefix = f"{component_id}: "
    if not check["file_exists"]:
        blockers.append(prefix + "required transparent PNG file is missing")
    elif not check["is_png"]:
        blockers.append(prefix + "required transparent asset is not a PNG")
    elif not check["has_alpha_channel"]:
        blockers.append(prefix + "required transparent PNG has no alpha channel")
    elif check["is_fully_opaque"]:
        blockers.append(prefix + "required transparent PNG is fully opaque")
    elif check["is_fully_transparent"]:
        warnings.append(prefix + "transparent PNG is fully transparent")
    return blockers, warnings


def manifest_components(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    components = manifest.get("components")
    return [item for item in components if isinstance(item, dict)] if isinstance(components, list) else []


def candidate_components(candidate_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = candidate_manifest.get("candidates")
    if not isinstance(candidates, list):
        return []
    normalized: list[dict[str, Any]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        normalized.append(
            {
                "component_id": candidate.get("candidate_id") or candidate.get("component_id") or "candidate",
                "component_type": candidate.get("candidate_type") or candidate.get("component_type") or "unknown",
                "file": candidate.get("image_path") or candidate.get("file") or "",
                "bounds": candidate.get("bounds") or {},
                "source": "candidate_manifest",
            }
        )
    return normalized


def build_review_items(package_dir: Path, components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for component in components:
        component_id = str(component.get("component_id") or component.get("candidate_id") or "component")
        component_type = normalize_type(component.get("component_type") or component.get("candidate_type"))
        level = classify_level(component_id, component_type)
        production_category = classify_production_category(component_id, component_type, level)
        required = transparency_required(component, level)
        file_name = component_file(component)
        transparent_check = inspect_png(package_dir, file_name, required)
        blockers, warnings = transparency_findings(component_id, transparent_check)
        items.append(
            {
                "component_id": component_id,
                "component_type": component_type,
                "component_name_zh": component.get("component_name_zh") or "",
                "source": component.get("source") or "manifest",
                "file": file_name,
                "bounds": component.get("bounds") or {},
                "level": level,
                "production_category": production_category,
                "required_transparency": required,
                "transparent_check": transparent_check,
                "blockers": blockers,
                "warnings": warnings,
            }
        )
    return items


def count_by(items: list[dict[str, Any]], key: str, value: str) -> int:
    return sum(1 for item in items if item.get(key) == value)


def default_manual_acceptance(existing: dict[str, Any], items: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    status = str(existing.get("review_status") or "pending")
    if status not in {"pending", "accepted", "rejected"}:
        status = "pending"
    return {
        "schema_version": "1.0",
        "review_status": status,
        "reviewer": str(existing.get("reviewer") or ""),
        "remarks": str(existing.get("remarks") or ""),
        "updated_at": str(existing.get("updated_at") or generated_at),
        "accepted_at": existing.get("accepted_at"),
        "accepted_by": str(existing.get("accepted_by") or ""),
        "components": [
            {
                "component_id": item["component_id"],
                "level": item["level"],
                "production_category": item["production_category"],
                "review_status": "pending",
                "remarks": "",
            }
            for item in items
        ],
    }


def write_html(package_dir: Path, review: dict[str, Any]) -> None:
    blockers = "".join(f"<li>{html.escape(item)}</li>" for item in review["blockers"])
    warnings = "".join(f"<li>{html.escape(item)}</li>" for item in review["warnings"])
    content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Production Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #172033; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
    .card {{ border: 1px solid #d8dee9; border-radius: 6px; padding: 12px; }}
    .ready {{ color: #0f7a3a; }}
    .blocked {{ color: #b42318; }}
  </style>
</head>
<body>
  <h1>Production Review</h1>
  <p>Package: <code>{html.escape(str(review["package_dir"]))}</code></p>
  <h2 class="{ "ready" if review["production_ready"] else "blocked" }">Score: {review["production_score"]}</h2>
  <div class="grid">
    <div class="card">A: {review["level_a_count"]}</div>
    <div class="card">B: {review["level_b_count"]}</div>
    <div class="card">C: {review["level_c_count"]}</div>
    <div class="card">Transparent issues: {review["transparent_issues"]}</div>
    <div class="card">Screen: {review["screen_count"]}</div>
    <div class="card">Panel: {review["panel_count"]}</div>
    <div class="card">Atomic: {review["atomic_count"]}</div>
    <div class="card">Effect: {review["effect_count"]}</div>
    <div class="card">Ignore: {review["ignore_count"]}</div>
    <div class="card">Blockers: {len(review["blockers"])}</div>
    <div class="card">Warnings: {len(review["warnings"])}</div>
  </div>
  <h2>Blockers</h2>
  <ul>{blockers}</ul>
  <h2>Warnings</h2>
  <ul>{warnings}</ul>
</body>
</html>
"""
    (package_dir / "production_review.html").write_text(content, encoding="utf-8")


def analyze_package(package_dir: str | Path) -> dict[str, str]:
    package_path = Path(package_dir)
    if not package_path.exists() or not package_path.is_dir():
        raise FileNotFoundError(f"996-ready package directory not found: {package_path}")

    warnings: list[str] = []
    manifest = read_json(package_path / "manifest.json", required=True, warnings=warnings)
    read_json(package_path / "annotation.json", required=True, warnings=warnings)
    candidate_manifest = read_json(package_path / "candidate_manifest.json", required=False, warnings=warnings)
    read_json(package_path / "component_quality_report.json", required=False, warnings=warnings)
    delivery_report = read_json(package_path / "delivery_report.json", required=False, warnings=warnings)

    generated_at = utc_now()
    components = manifest_components(manifest)
    candidates = candidate_components(candidate_manifest)
    items = build_review_items(package_path, components + candidates)
    blockers = [blocker for item in items for blocker in item["blockers"]]
    item_warnings = [warning for item in items for warning in item["warnings"]]
    all_warnings = warnings + item_warnings
    missing_files = [
        item["file"]
        for item in items
        if item.get("file") and not item["transparent_check"]["file_exists"]
    ]
    transparent_issues = sum(
        1
        for item in items
        if item["transparent_check"]["required_transparency"]
        and (
            not item["transparent_check"]["file_exists"]
            or not item["transparent_check"]["is_png"]
            or not item["transparent_check"]["has_alpha_channel"]
            or item["transparent_check"]["is_fully_opaque"]
        )
    )
    production_score = max(0, 100 - len(blockers) * 20 - transparent_issues * 10 - len(all_warnings) * 5)

    analysis = {
        "schema_version": "1.0",
        "package_dir": str(package_path),
        "generated_at": generated_at,
        "components": items,
        "summary": {
            "components_count": len(components),
            "candidates_count": len(candidates),
            "blockers_count": len(blockers),
            "warnings_count": len(all_warnings),
        },
    }
    review = {
        "schema_version": "1.0",
        "package_dir": str(package_path),
        "style_code": package_path.parts[-3] if len(package_path.parts) >= 3 else "",
        "screen_type": str(delivery_report.get("screen_type") or manifest.get("template") or package_path.parts[-2]),
        "generation_job_id": str(manifest.get("generation_job_id") or delivery_report.get("generation_job_id") or package_path.name),
        "production_score": production_score,
        "production_ready": not blockers,
        "components_count": len(components),
        "candidates_count": len(candidates),
        "level_a_count": count_by(items, "level", "A"),
        "level_b_count": count_by(items, "level", "B"),
        "level_c_count": count_by(items, "level", "C"),
        "screen_count": count_by(items, "production_category", "Screen"),
        "panel_count": count_by(items, "production_category", "Panel"),
        "atomic_count": count_by(items, "production_category", "Atomic"),
        "effect_count": count_by(items, "production_category", "Effect"),
        "ignore_count": count_by(items, "production_category", "Ignore"),
        "transparent_issues": transparent_issues,
        "blockers": blockers,
        "warnings": all_warnings,
        "missing_files": missing_files,
        "generated_at": generated_at,
    }

    existing_acceptance = read_json(package_path / "manual_acceptance.json", required=False, warnings=[])
    acceptance = default_manual_acceptance(existing_acceptance, items, generated_at)

    (package_path / "component_review_analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_path / "production_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_path / "manual_acceptance.json").write_text(json.dumps(acceptance, ensure_ascii=False, indent=2), encoding="utf-8")
    write_html(package_path, review)

    return {
        "component_review_analysis_path": str(package_path / "component_review_analysis.json"),
        "production_review_path": str(package_path / "production_review.json"),
        "manual_acceptance_path": str(package_path / "manual_acceptance.json"),
        "production_review_html_path": str(package_path / "production_review.html"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a 996-ready package for production review.")
    parser.add_argument("package_dir")
    args = parser.parse_args()
    result = analyze_package(args.package_dir)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
