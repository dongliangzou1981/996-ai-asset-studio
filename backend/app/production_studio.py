from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.schemas import (
    ProductionStudioRequest,
    ProductionStudioResponse,
    ProductionStudioScreenResult,
    ProductionStudioStyleCode,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_screen_with_style import generate_screen_with_style
from scripts.master_style_workflow import run_master_style_workflow
from scripts.validate_996_export import validate_package


SEMANTIC_ICON_IDS = {
    "bag",
    "role",
    "skill",
    "shop",
    "activity",
    "settings",
    "close",
    "back",
    "confirm",
    "cancel",
}


def list_style_codes(style_root: str | Path | None = None) -> list[ProductionStudioStyleCode]:
    root = Path(style_root) if style_root else ROOT / "style_codes"
    if not root.exists():
        return []

    items: list[ProductionStudioStyleCode] = []
    for style_dir in sorted(path for path in root.iterdir() if path.is_dir() and path.name.startswith("STYLE_")):
        style_json = style_dir / "style.json"
        data: dict[str, Any] = {}
        if style_json.exists():
            try:
                parsed = json.loads(style_json.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    data = parsed
            except json.JSONDecodeError:
                data = {}
        items.append(
            ProductionStudioStyleCode(
                style_code=str(data.get("style_code") or style_dir.name),
                style_name=str(data.get("style_name") or style_dir.name),
                source_job_id=str(data.get("source_job_id") or ""),
                device_type=str(data.get("device_type") or ""),
            )
        )
    return items


def package_file_url(package_dir: Path, upload_root: Path, filename: str) -> str:
    try:
        relative_package = package_dir.resolve().relative_to(upload_root.resolve())
    except ValueError:
        relative_package = Path(package_dir.as_posix())
    return "/production-studio/files/" + (relative_package / filename).as_posix()


def has_semantic_icons(manifest: dict[str, Any], candidate_manifest: dict[str, Any]) -> bool:
    names: set[str] = set()
    for component in manifest.get("components") or []:
        if isinstance(component, dict):
            names.add(str(component.get("component_id") or "").lower())
            names.add(str(component.get("component_name_zh") or "").lower())
    for candidate in candidate_manifest.get("candidates") or []:
        if isinstance(candidate, dict):
            names.add(str(candidate.get("candidate_id") or "").lower())
            names.add(str(candidate.get("candidate_type") or "").lower())
    return all(any(icon in name for name in names) for icon in SEMANTIC_ICON_IDS)


def summarize_package(package_dir: str | Path, upload_root: str | Path, screen_type: str) -> ProductionStudioScreenResult:
    package_path = Path(package_dir)
    if not package_path.is_absolute():
        package_path = ROOT / package_path
    upload_path = Path(upload_root)
    if not upload_path.is_absolute():
        upload_path = ROOT / upload_path

    manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
    candidate_manifest = json.loads((package_path / "candidate_manifest.json").read_text(encoding="utf-8"))
    validation = validate_package(package_path)
    semantic_icons_ready = has_semantic_icons(manifest, candidate_manifest)
    return ProductionStudioScreenResult(
        screen_type=screen_type,  # type: ignore[arg-type]
        generation_job_id=str(manifest.get("generation_job_id") or package_path.name),
        status="completed" if validation["ok"] else "failed",
        package_dir=str(package_path.relative_to(ROOT) if package_path.is_relative_to(ROOT) else package_path).replace("\\", "/"),
        ui_preview_url=package_file_url(package_path, upload_path, "ui_preview.png"),
        delivery_report_url=package_file_url(package_path, upload_path, "delivery_report.html"),
        candidate_preview_url=package_file_url(package_path, upload_path, "candidate_preview.html"),
        component_quality_report_url=package_file_url(package_path, upload_path, "component_quality_report.html"),
        components_count=len(manifest.get("components") or []),
        candidates_count=len(candidate_manifest.get("candidates") or []),
        validator_ok=bool(validation["ok"]),
        missing_semantic_icons=not semantic_icons_ready,
        common_icons_note=(
            "common_icons semantic naming is complete"
            if semantic_icons_ready
            else "common_icons semantic naming still needs improvement; current slices are generic candidates."
        ),
    )


def run_production_studio(
    *,
    payload: ProductionStudioRequest,
    database_path: str | Path,
    upload_root: str | Path,
    style_root: str | Path | None = None,
) -> ProductionStudioResponse:
    style_root_path = Path(style_root) if style_root else ROOT / "style_codes"
    upload_path = Path(upload_root)
    if not upload_path.is_absolute():
        upload_path = ROOT / upload_path
    database_path_value = Path(database_path)
    if not database_path_value.is_absolute():
        database_path_value = ROOT / database_path_value

    results: list[ProductionStudioScreenResult] = []
    style_code = payload.style_code or ""
    generated_screen_types: set[str] = set()

    if payload.style_source == "new_style":
        master = run_master_style_workflow(
            screen_generation_mode="auto_generate",
            style_name=payload.style_name,
            prompt=payload.prompt,
            style_root=style_root_path,
            database_path=database_path_value,
            upload_root=upload_path,
            device_type=payload.device_type,
            asset_mode=payload.asset_mode,
        )
        style_code = str(master["style_code"])
        results.append(summarize_package(master["package_dir"], upload_path, "main_ui"))
        generated_screen_types.add("main_ui")

    for screen_type in payload.screen_types:
        if screen_type in generated_screen_types:
            continue
        generated = generate_screen_with_style(
            style_code=style_code,
            screen_type=screen_type,
            user_prompt=payload.prompt,
            style_root=style_root_path,
            database_path=database_path_value,
            upload_root=upload_path,
            device_type=payload.device_type,
            asset_mode=payload.asset_mode,
        )
        results.append(summarize_package(generated["package_dir"], upload_path, screen_type))

    return ProductionStudioResponse(
        style_code=style_code,
        device_type=payload.device_type,
        asset_mode=payload.asset_mode,
        style_source=payload.style_source,
        results=results,
    )
