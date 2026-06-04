from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "manifest": "manifest.json",
    "annotation": "annotation.json",
    "preview": "preview.html",
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
    return candidate


def component_file_path(component: dict[str, Any], components_dir: str) -> str:
    file_value = component.get("file")
    if isinstance(file_value, str) and file_value:
        return file_value
    file_name = component.get("file_name")
    if isinstance(file_name, str) and file_name:
        return str(Path(components_dir) / file_name)
    return ""


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
        "package_dir": str(root),
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
