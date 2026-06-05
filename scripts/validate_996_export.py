from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
PACKAGE_TYPE = "996-ready"
COORDINATE_SPACE = "ui_preview_pixels"

DEVICE_TYPES = {"mobile", "pc", "mobile_landscape", "pc_landscape"}
ASSET_MODES = {"ui_package", "resource_production"}
RESOURCE_CATEGORIES = {
    "layout_bar",
    "panel_region",
    "button_asset",
    "icon_asset",
    "frame_asset",
    "input_asset",
    "slot_asset",
    "tab_asset",
    "background_asset",
    "unknown_asset",
}
COMPONENT_TYPES = {
    "panel",
    "bar",
    "button",
    "icon",
    "frame",
    "slot",
    "tab",
    "badge",
    "progress",
    "input",
    "border",
    "background",
    "text",
    "decoration",
    "unknown",
}
RESOURCE_GROUPS = {
    "main",
    "bag_ui",
    "shop",
    "activity",
    "player_main_layer_ui",
    "public",
    "item",
    "skill_icon",
    "skill_icon_c",
    "unknown",
}
RECOGNITION_METHODS = {"template", "fixture", "manual"}
REVIEW_STATUSES = {"pending", "reviewed", "approved", "rejected"}
IMAGE_ALPHA_VALUES = {"required", "optional", "none"}
TRANSPARENT_REQUIRED_TYPES = {"button", "icon", "frame", "input"}
TRANSPARENT_OPTIONAL_TYPES = {"panel", "background"}
TRANSPARENT_STATUSES = {"not_required", "unverified", "verified"}

REQUIRED_FILES = {
    "manifest": "manifest.json",
    "annotation": "annotation.json",
    "preview": "preview.html",
}


def detect_package_layout(root: Path) -> dict[str, str | None]:
    parts = root.parts
    for index, part in enumerate(parts):
        if part != "996-ready":
            continue
        remaining = parts[index + 1 :]
        if len(remaining) >= 3 and remaining[0].startswith("STYLE_"):
            return {
                "mode": "style_guided",
                "style_code": remaining[0],
                "screen_type": remaining[1],
                "generation_job_id": remaining[2],
            }
        if remaining:
            return {
                "mode": "direct",
                "style_code": None,
                "screen_type": None,
                "generation_job_id": remaining[0],
            }
    return {
        "mode": "unknown",
        "style_code": None,
        "screen_type": None,
        "generation_job_id": root.name,
    }


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"Missing file: {path.name}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path.name}: {exc}")
        return {}
    if not isinstance(data, dict):
        errors.append(f"{path.name} must contain a JSON object")
        return {}
    return data


def safe_relative_path(value: str, label: str, errors: list[str]) -> Path | None:
    if not value:
        errors.append(f"Missing path for {label}")
        return None
    candidate = Path(value)
    if candidate.is_absolute():
        errors.append(f"{label} must be a relative path: {value}")
        return None
    if any(part == ".." for part in candidate.parts):
        errors.append(f"{label} must not traverse outside package: {value}")
        return None
    if "\\" in value:
        errors.append(f"{label} must use forward slashes: {value}")
        return None
    return candidate


def component_file_path(component: dict[str, Any], components_dir: str) -> str:
    file_value = component.get("file")
    if isinstance(file_value, str) and file_value:
        return file_value
    file_name = component.get("file_name")
    if isinstance(file_name, str) and file_name:
        return str(Path(components_dir) / file_name)
    return ""


def require_field(data: dict[str, Any], field: str, label: str, errors: list[str]) -> bool:
    if field not in data:
        errors.append(f"{label}.{field} is required")
        return False
    return True


def expect_string(data: dict[str, Any], field: str, label: str, errors: list[str], *, non_empty: bool = True) -> bool:
    value = data.get(field)
    if not isinstance(value, str) or (non_empty and not value):
        errors.append(f"{label}.{field} must be a string")
        return False
    return True


def expect_bool(data: dict[str, Any], field: str, label: str, errors: list[str]) -> bool:
    if not isinstance(data.get(field), bool):
        errors.append(f"{label}.{field} must be a boolean")
        return False
    return True


def expect_positive_int(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        errors.append(f"{label} must be a positive integer")
        return False
    return True


def expect_non_negative_int(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        errors.append(f"{label} must be a non-negative integer")
        return False
    return True


def expect_bounds(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    ok = True
    ok = expect_non_negative_int(value.get("x"), f"{label}.x", errors) and ok
    ok = expect_non_negative_int(value.get("y"), f"{label}.y", errors) and ok
    ok = expect_positive_int(value.get("width"), f"{label}.width", errors) and ok
    ok = expect_positive_int(value.get("height"), f"{label}.height", errors) and ok
    return ok


def expect_hex_color(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        errors.append(f"{label} must be a #RRGGBB color")
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        errors.append(f"{label} must be a #RRGGBB color")
        return False
    return True


def expect_enum(value: Any, allowed: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{label} must be one of Schema V1 component types" if label.endswith("component_type") else f"{label} must be one of {sorted(allowed)}")
        return False
    return True


def validate_device_resolution(device_type: Any, resolution: Any, errors: list[str]) -> bool:
    if device_type not in {"mobile_landscape", "pc_landscape"}:
        return True
    if not isinstance(resolution, dict):
        return False
    width = resolution.get("width")
    height = resolution.get("height")
    if not isinstance(width, int) or isinstance(width, bool) or not isinstance(height, int) or isinstance(height, bool):
        return False
    if width <= 0 or height <= 0:
        return False
    if width <= height:
        errors.append(f"manifest.resolution must be landscape for {device_type}")
        return False

    ratio = width / height
    if device_type == "mobile_landscape" and abs(ratio - (16 / 9)) > 0.02:
        errors.append("manifest.resolution must be 16:9 landscape for mobile_landscape")
        return False
    if device_type == "pc_landscape":
        allowed = any(abs(ratio - expected) <= 0.08 for expected in (4 / 3, 3 / 2, 16 / 9))
        if not allowed:
            errors.append("manifest.resolution must be PC landscape, typically 4:3, 3:2, or 16:9, for pc_landscape")
            return False
    return True


def expect_confidence(value: Any, label: str, errors: list[str]) -> bool:
    if value is None:
        return True
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or value > 1:
        errors.append(f"{label} must be null or a number between 0 and 1")
        return False
    return True


def validate_transparent_field(
    value: Any,
    *,
    component_type: Any,
    label: str,
    errors: list[str],
    image: dict[str, Any] | None = None,
) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict):
        errors.append(f"{label}.transparent must be an object")
        return False

    ok = True
    ok = expect_bool(value, "required", f"{label}.transparent", errors) and ok
    ok = expect_bool(value, "verified", f"{label}.transparent", errors) and ok
    ok = expect_enum(value.get("status"), TRANSPARENT_STATUSES, f"{label}.transparent.status", errors) and ok
    required = value.get("required")
    verified = value.get("verified")
    status = value.get("status")

    if component_type in TRANSPARENT_REQUIRED_TYPES and required is not True:
        errors.append(f"{label}.transparent.required must be true for {component_type} components")
        ok = False
    if component_type in TRANSPARENT_OPTIONAL_TYPES and required is True:
        errors.append(f"{label}.transparent.required may be false for {component_type} components")
        ok = False
    if verified is True and status != "verified":
        errors.append(f"{label}.transparent.status must be verified when transparent.verified is true")
        ok = False
    if required is False and status == "verified":
        errors.append(f"{label}.transparent.status must not be verified when transparent.required is false")
        ok = False
    if required is True and status == "not_required":
        errors.append(f"{label}.transparent.status must not be not_required when transparent.required is true")
        ok = False
    if image is not None and required is True:
        if image.get("alpha") != "required":
            errors.append(f"{label}.image.alpha must be required when transparent.required is true")
            ok = False
        if image.get("transparent_background") is not True:
            errors.append(f"{label}.image.transparent_background must be true when transparent.required is true")
            ok = False
    return ok


def validate_transparent_policy(value: Any, label: str, errors: list[str]) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict):
        errors.append(f"{label}.transparent_policy must be an object")
        return False
    ok = True
    required_types = value.get("required_component_types")
    allowed_flat = value.get("allowed_flat_component_types")
    if not isinstance(required_types, list) or not all(isinstance(item, str) for item in required_types):
        errors.append(f"{label}.transparent_policy.required_component_types must be a string array")
        ok = False
    if not isinstance(allowed_flat, list) or not all(isinstance(item, str) for item in allowed_flat):
        errors.append(f"{label}.transparent_policy.allowed_flat_component_types must be a string array")
        ok = False
    verification = value.get("verification")
    if not isinstance(verification, str) or not verification:
        errors.append(f"{label}.transparent_policy.verification must be a string")
        ok = False
    return ok


def validate_manifest_schema(manifest: dict[str, Any], errors: list[str]) -> dict[str, bool]:
    checks = {
        "schema_v1": True,
        "manifest_required_fields": True,
        "field_types": True,
        "device_resolution": True,
        "component_classification": True,
        "transparent_fields": True,
        "resource_production_fields": True,
    }
    required = [
        "schema_version",
        "package_type",
        "source_asset_id",
        "generation_job_id",
        "device_type",
        "resolution",
        "ui_preview",
        "components_dir",
        "components",
    ]
    for field in required:
        checks["manifest_required_fields"] = require_field(manifest, field, "manifest", errors) and checks["manifest_required_fields"]

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("manifest.schema_version must be 1.0")
        checks["schema_v1"] = False
    if manifest.get("package_type") != PACKAGE_TYPE:
        errors.append("manifest.package_type must be 996-ready")
        checks["schema_v1"] = False

    checks["field_types"] = expect_string(manifest, "source_asset_id", "manifest", errors) and checks["field_types"]
    checks["field_types"] = expect_string(manifest, "generation_job_id", "manifest", errors) and checks["field_types"]
    checks["field_types"] = expect_enum(manifest.get("device_type"), DEVICE_TYPES, "manifest.device_type", errors) and checks["field_types"]
    checks["field_types"] = expect_string(manifest, "ui_preview", "manifest", errors) and checks["field_types"]
    checks["field_types"] = expect_string(manifest, "components_dir", "manifest", errors) and checks["field_types"]
    if "asset_mode" in manifest:
        checks["resource_production_fields"] = expect_enum(manifest.get("asset_mode"), ASSET_MODES, "manifest.asset_mode", errors) and checks["resource_production_fields"]
    checks["resource_production_fields"] = validate_transparent_policy(manifest.get("transparent_policy"), "manifest", errors) and checks["resource_production_fields"]

    resolution = manifest.get("resolution")
    if not isinstance(resolution, dict):
        errors.append("manifest.resolution must be an object")
        checks["field_types"] = False
    else:
        checks["field_types"] = expect_positive_int(resolution.get("width"), "manifest.resolution.width", errors) and checks["field_types"]
        checks["field_types"] = expect_positive_int(resolution.get("height"), "manifest.resolution.height", errors) and checks["field_types"]
        checks["device_resolution"] = validate_device_resolution(manifest.get("device_type"), resolution, errors)

    components = manifest.get("components")
    if not isinstance(components, list) or not components:
        errors.append("manifest.components must be a non-empty list")
        checks["field_types"] = False
        return checks

    seen_ids: set[str] = set()
    for index, component in enumerate(components):
        label = f"manifest.components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{label} must be an object")
            checks["field_types"] = False
            continue
        for field in [
            "component_id",
            "component_type",
            "component_name_zh",
            "resource_group",
            "file",
            "bounds",
            "transparent_png_required",
            "transparent_png_verified",
        ]:
            checks["manifest_required_fields"] = require_field(component, field, label, errors) and checks["manifest_required_fields"]
        checks["field_types"] = expect_string(component, "component_id", label, errors) and checks["field_types"]
        component_id = component.get("component_id")
        if isinstance(component_id, str):
            if component_id in seen_ids:
                errors.append(f"{label}.component_id must be unique")
                checks["field_types"] = False
            seen_ids.add(component_id)
        checks["component_classification"] = expect_enum(component.get("component_type"), COMPONENT_TYPES, f"{label}.component_type", errors) and checks["component_classification"]
        checks["component_classification"] = expect_enum(component.get("resource_group"), RESOURCE_GROUPS, f"{label}.resource_group", errors) and checks["component_classification"]
        if "asset_mode" in component:
            checks["resource_production_fields"] = expect_enum(component.get("asset_mode"), ASSET_MODES, f"{label}.asset_mode", errors) and checks["resource_production_fields"]
        if "resource_category" in component:
            checks["resource_production_fields"] = expect_enum(component.get("resource_category"), RESOURCE_CATEGORIES, f"{label}.resource_category", errors) and checks["resource_production_fields"]
        if "production_usage" in component:
            checks["resource_production_fields"] = expect_string(component, "production_usage", label, errors) and checks["resource_production_fields"]
        checks["field_types"] = expect_string(component, "component_name_zh", label, errors) and checks["field_types"]
        checks["field_types"] = expect_string(component, "file", label, errors) and checks["field_types"]
        checks["field_types"] = expect_bounds(component.get("bounds"), f"{label}.bounds", errors) and checks["field_types"]
        checks["transparent_fields"] = validate_transparent_field(
            component.get("transparent"),
            component_type=component.get("component_type"),
            label=label,
            errors=errors,
        ) and checks["transparent_fields"]
        checks["field_types"] = expect_bool(component, "transparent_png_required", label, errors) and checks["field_types"]
        checks["field_types"] = expect_bool(component, "transparent_png_verified", label, errors) and checks["field_types"]
    return checks


def validate_annotation_schema(annotation: dict[str, Any], errors: list[str]) -> dict[str, bool]:
    checks = {
        "schema_v1": True,
        "annotation_required_fields": True,
        "field_types": True,
        "component_classification": True,
        "transparent_fields": True,
        "resource_production_fields": True,
    }
    required = ["schema_version", "source_asset_id", "coordinate_space", "components"]
    for field in required:
        checks["annotation_required_fields"] = require_field(annotation, field, "annotation", errors) and checks["annotation_required_fields"]

    if annotation.get("schema_version") != SCHEMA_VERSION:
        errors.append("annotation.schema_version must be 1.0")
        checks["schema_v1"] = False
    if annotation.get("coordinate_space") != COORDINATE_SPACE:
        errors.append("annotation.coordinate_space must be ui_preview_pixels")
        checks["schema_v1"] = False

    checks["field_types"] = expect_string(annotation, "source_asset_id", "annotation", errors) and checks["field_types"]
    if "device_type" in annotation:
        checks["field_types"] = expect_enum(annotation.get("device_type"), DEVICE_TYPES, "annotation.device_type", errors) and checks["field_types"]
    if "asset_mode" in annotation:
        checks["resource_production_fields"] = expect_enum(annotation.get("asset_mode"), ASSET_MODES, "annotation.asset_mode", errors) and checks["resource_production_fields"]
    checks["resource_production_fields"] = validate_transparent_policy(annotation.get("transparent_policy"), "annotation", errors) and checks["resource_production_fields"]
    components = annotation.get("components")
    if not isinstance(components, list) or not components:
        errors.append("annotation.components must be a non-empty list")
        checks["field_types"] = False
        return checks

    for index, component in enumerate(components):
        label = f"annotation.components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{label} must be an object")
            checks["field_types"] = False
            continue
        for field in [
            "component_id",
            "component_type",
            "component_name_zh",
            "resource_group",
            "bounds",
            "style",
            "image",
            "recognition",
            "requires_manual_review",
            "review_status",
            "notes",
        ]:
            checks["annotation_required_fields"] = require_field(component, field, label, errors) and checks["annotation_required_fields"]
        checks["field_types"] = expect_string(component, "component_id", label, errors) and checks["field_types"]
        checks["component_classification"] = expect_enum(component.get("component_type"), COMPONENT_TYPES, f"{label}.component_type", errors) and checks["component_classification"]
        checks["component_classification"] = expect_enum(component.get("resource_group"), RESOURCE_GROUPS, f"{label}.resource_group", errors) and checks["component_classification"]
        if "asset_mode" in component:
            checks["resource_production_fields"] = expect_enum(component.get("asset_mode"), ASSET_MODES, f"{label}.asset_mode", errors) and checks["resource_production_fields"]
        if "resource_category" in component:
            checks["resource_production_fields"] = expect_enum(component.get("resource_category"), RESOURCE_CATEGORIES, f"{label}.resource_category", errors) and checks["resource_production_fields"]
        if "production_usage" in component:
            checks["resource_production_fields"] = expect_string(component, "production_usage", label, errors) and checks["resource_production_fields"]
        checks["field_types"] = expect_string(component, "component_name_zh", label, errors) and checks["field_types"]
        checks["field_types"] = expect_bounds(component.get("bounds"), f"{label}.bounds", errors) and checks["field_types"]
        checks["field_types"] = expect_bool(component, "requires_manual_review", label, errors) and checks["field_types"]
        checks["field_types"] = expect_enum(component.get("review_status"), REVIEW_STATUSES, f"{label}.review_status", errors) and checks["field_types"]
        checks["field_types"] = expect_string(component, "notes", label, errors, non_empty=False) and checks["field_types"]

        style = component.get("style")
        if not isinstance(style, dict):
            errors.append(f"{label}.style must be an object")
            checks["field_types"] = False
        else:
            checks["field_types"] = expect_string(style, "font_family", f"{label}.style", errors) and checks["field_types"]
            checks["field_types"] = expect_positive_int(style.get("font_size"), f"{label}.style.font_size", errors) and checks["field_types"]
            checks["field_types"] = expect_hex_color(style.get("font_color"), f"{label}.style.font_color", errors) and checks["field_types"]

        image = component.get("image")
        if not isinstance(image, dict):
            errors.append(f"{label}.image must be an object")
            checks["field_types"] = False
        else:
            checks["field_types"] = expect_string(image, "file", f"{label}.image", errors) and checks["field_types"]
            checks["field_types"] = expect_enum(image.get("format"), {"png"}, f"{label}.image.format", errors) and checks["field_types"]
            checks["field_types"] = expect_enum(image.get("color_mode"), {"RGBA"}, f"{label}.image.color_mode", errors) and checks["field_types"]
            checks["field_types"] = expect_enum(image.get("alpha"), IMAGE_ALPHA_VALUES, f"{label}.image.alpha", errors) and checks["field_types"]
            checks["field_types"] = expect_bool(image, "transparent_background", f"{label}.image", errors) and checks["field_types"]

        checks["transparent_fields"] = validate_transparent_field(
            component.get("transparent"),
            component_type=component.get("component_type"),
            label=label,
            errors=errors,
            image=image if isinstance(image, dict) else None,
        ) and checks["transparent_fields"]

        recognition = component.get("recognition")
        if not isinstance(recognition, dict):
            errors.append(f"{label}.recognition must be an object")
            checks["field_types"] = False
        else:
            checks["field_types"] = expect_enum(recognition.get("method"), RECOGNITION_METHODS, f"{label}.recognition.method", errors) and checks["field_types"]
            checks["field_types"] = expect_confidence(recognition.get("confidence"), f"{label}.recognition.confidence", errors) and checks["field_types"]
    return checks


def validate_package(package_dir: str | Path) -> dict[str, Any]:
    root = Path(package_dir)
    errors: list[str] = []
    warnings: list[str] = []

    manifest_path = root / REQUIRED_FILES["manifest"]
    annotation_path = root / REQUIRED_FILES["annotation"]
    preview_path = root / REQUIRED_FILES["preview"]

    checks: dict[str, bool] = {
        "package_dir_exists": root.exists() and root.is_dir(),
        "manifest_exists": manifest_path.exists(),
        "annotation_exists": annotation_path.exists(),
        "preview_exists": preview_path.exists(),
        "schema_v1": True,
        "manifest_required_fields": True,
        "annotation_required_fields": True,
        "field_types": True,
        "device_resolution": True,
        "component_classification": True,
        "transparent_fields": True,
        "resource_production_fields": True,
        "ui_preview_exists": False,
        "component_paths_relative": True,
        "component_files_exist": True,
        "annotation_component_files_exist": True,
    }

    if not checks["package_dir_exists"]:
        errors.append(f"Package directory does not exist: {root}")

    manifest = load_json(manifest_path, errors) if checks["manifest_exists"] else {}
    annotation = load_json(annotation_path, errors) if checks["annotation_exists"] else {}

    if not checks["manifest_exists"]:
        errors.append("Missing manifest.json")
    if not checks["annotation_exists"]:
        errors.append("Missing annotation.json")
    if not checks["preview_exists"]:
        errors.append("Missing preview.html")

    if manifest:
        manifest_checks = validate_manifest_schema(manifest, errors)
        for name, passed in manifest_checks.items():
            checks[name] = checks[name] and passed
    else:
        checks["schema_v1"] = False
        checks["manifest_required_fields"] = False

    if annotation:
        annotation_checks = validate_annotation_schema(annotation, errors)
        for name, passed in annotation_checks.items():
            checks[name] = checks[name] and passed
    else:
        checks["schema_v1"] = False
        checks["annotation_required_fields"] = False

    ui_preview_value = manifest.get("ui_preview") if isinstance(manifest.get("ui_preview"), str) else "ui_preview.png"
    ui_preview_rel = safe_relative_path(ui_preview_value, "ui_preview", errors)
    if ui_preview_rel is not None:
        checks["ui_preview_exists"] = (root / ui_preview_rel).exists()
        if not checks["ui_preview_exists"]:
            errors.append(f"Missing ui_preview file: {ui_preview_value}")

    components_dir = manifest.get("components_dir") if isinstance(manifest.get("components_dir"), str) else "components"
    components = manifest.get("components")
    if components is None:
        components = []
        warnings.append("manifest.json does not include components")
    if not isinstance(components, list):
        components = []
        errors.append("manifest.components must be a list")

    component_files: list[str] = []
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            errors.append(f"manifest.components[{index}] must be an object")
            checks["component_files_exist"] = False
            continue
        file_value = component_file_path(component, components_dir)
        component_id = component.get("component_id") or f"index {index}"
        rel = safe_relative_path(file_value, f"component {component_id}", errors)
        if rel is None:
            checks["component_paths_relative"] = False
            checks["component_files_exist"] = False
            continue
        component_files.append(str(rel).replace("\\", "/"))
        if not (root / rel).exists():
            checks["component_files_exist"] = False
            errors.append(f"Missing component file: {str(rel).replace('\\', '/')}")

    annotation_components = annotation.get("components")
    if annotation_components is not None and not isinstance(annotation_components, list):
        errors.append("annotation.components must be a list")
        annotation_components = []
    for index, component in enumerate(annotation_components or []):
        if not isinstance(component, dict):
            errors.append(f"annotation.components[{index}] must be an object")
            checks["annotation_component_files_exist"] = False
            continue
        image = component.get("image")
        if not isinstance(image, dict):
            continue
        file_value = image.get("file")
        if not isinstance(file_value, str) or not file_value:
            continue
        component_id = component.get("component_id") or f"index {index}"
        rel = safe_relative_path(file_value, f"annotation component {component_id}", errors)
        if rel is None:
            checks["component_paths_relative"] = False
            checks["annotation_component_files_exist"] = False
            continue
        if not (root / rel).exists():
            checks["annotation_component_files_exist"] = False
            errors.append(f"Missing annotation component file: {str(rel).replace('\\', '/')}")

    ok = all(checks.values()) and not errors
    return {
        "ok": ok,
        "schema_version": SCHEMA_VERSION if checks["schema_v1"] else None,
        "package_dir": str(root),
        "layout": detect_package_layout(root),
        "checks": checks,
        "files": {
            "manifest": str(manifest_path),
            "annotation": str(annotation_path),
            "preview": str(preview_path),
            "ui_preview": ui_preview_value,
            "components": component_files,
        },
        "warnings": warnings,
        "errors": errors,
    }


def format_text_report(report: dict[str, Any]) -> str:
    lines = [
        "996 export validation report",
        f"package_dir: {report['package_dir']}",
        f"status: {'PASS' if report['ok'] else 'FAIL'}",
        "",
        "checks:",
    ]
    for name, passed in report["checks"].items():
        lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
    if report["warnings"]:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"- {warning}" for warning in report["warnings"])
    if report["errors"]:
        lines.append("")
        lines.append("errors:")
        lines.extend(f"- {error}" for error in report["errors"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local 996-ready export package.")
    parser.add_argument("package_dir", help="Path to the 996-ready package directory.")
    parser.add_argument("--json", action="store_true", help="Print the validation report as JSON.")
    args = parser.parse_args()

    report = validate_package(args.package_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
