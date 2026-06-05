from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import StudioDatabase
from app.job_runner import JobRunnerService, parse_json_object
from app.schemas import AssetCreate, GenerationJobCreate, ProjectCreate
from scripts.generate_screen_with_style import (
    SUPPORTED_SCREEN_TYPES,
    copy_package_to_style_dir,
    ensure_real_provider_ready,
    image_dimensions,
    load_style,
    write_delivery_report,
)
from scripts.validate_996_export import validate_package


EDIT_MODE = "prompt_fallback"


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def load_source_package_context(source_package: str | Path) -> dict[str, Any]:
    package = Path(source_package)
    if not package.exists():
        raise FileNotFoundError(f"Source package does not exist: {package}")
    context = {
        "manifest": load_json_if_exists(package / "manifest.json"),
        "annotation": load_json_if_exists(package / "annotation.json"),
        "candidate_manifest": load_json_if_exists(package / "candidate_manifest.json"),
    }
    if not context["manifest"]:
        raise FileNotFoundError(f"Source package manifest.json is required: {package}")
    if not context["annotation"]:
        raise FileNotFoundError(f"Source package annotation.json is required: {package}")
    return context


def parent_generation_job_id(source_package: Path, context: dict[str, Any]) -> str:
    manifest = context.get("manifest")
    if isinstance(manifest, dict) and manifest.get("generation_job_id"):
        return str(manifest["generation_job_id"])
    return source_package.name


def summarize_components(context: dict[str, Any]) -> str:
    annotation = context.get("annotation")
    if not isinstance(annotation, dict):
        return "No annotation summary available."
    components = annotation.get("components")
    if not isinstance(components, list):
        return "No annotation component list available."
    summary: list[str] = []
    for component in components[:12]:
        if not isinstance(component, dict):
            continue
        component_id = str(component.get("component_id") or "unknown")
        component_type = str(component.get("component_type") or "unknown")
        bounds = component.get("bounds")
        summary.append(f"{component_id}:{component_type}:{bounds}")
    return "; ".join(summary) if summary else "No component summary available."


def summarize_candidates(context: dict[str, Any]) -> str:
    candidate_manifest = context.get("candidate_manifest")
    if not isinstance(candidate_manifest, dict):
        return "No candidate manifest available."
    candidates = candidate_manifest.get("candidates")
    if not isinstance(candidates, list):
        return "No candidate list available."
    summary: list[str] = []
    for candidate in candidates[:12]:
        if not isinstance(candidate, dict):
            continue
        candidate_type = str(candidate.get("candidate_type") or "unknown")
        bounds = candidate.get("bounds")
        summary.append(f"{candidate_type}:{bounds}")
    return "; ".join(summary) if summary else "No candidate summary available."


def build_style_edit_prompt(
    *,
    style: dict[str, Any],
    screen_type: str,
    source_package: str | Path,
    context: dict[str, Any],
    edit_request: str,
    source_preview_path: str | Path,
) -> str:
    if screen_type not in SUPPORTED_SCREEN_TYPES:
        raise ValueError(f"screen_type must be one of {sorted(SUPPORTED_SCREEN_TYPES)}")
    style_code = str(style.get("style_code") or "")
    style_name = str(style.get("style_name") or style_code)
    palette = style.get("color_palette") or []
    palette_text = ", ".join(str(color) for color in palette) if isinstance(palette, list) else str(palette)
    parent_job_id = parent_generation_job_id(Path(source_package), context)

    return "\n".join(
        [
            "Edit one existing 996 legend game UI screen and output a new full-screen version.",
            f"style_code: {style_code}",
            f"style_name: {style_name}",
            f"screen_type: {screen_type}",
            f"parent_generation_job_id: {parent_job_id}",
            f"source_package: {Path(source_package)}",
            f"source_preview_path: {Path(source_preview_path)}",
            f"edit_request: {edit_request}",
            "Keep the original layout structure, information hierarchy, and operation flow.",
            "Only change the requested visual area or visual emphasis.",
            "Do not remove core controls, hide buttons, cover chat, cover skill bars, or cover player information.",
            "You must preserve the STYLE_CODE visual style and keep the new version visually consistent with the original style.",
            f"style_summary: {style.get('style_summary', '')}",
            f"color_palette: {palette_text}",
            f"font_style: {style.get('font_style', '')}",
            f"border_style: {style.get('border_style', '')}",
            f"button_style: {style.get('button_style', '')}",
            f"icon_style: {style.get('icon_style', '')}",
            f"texture_style: {style.get('texture_style', '')}",
            f"annotation_summary: {summarize_components(context)}",
            f"candidate_summary: {summarize_candidates(context)}",
            "Canvas ratio must remain 4:3.",
            "Output a single revised UI screen only, suitable for Component Processing, annotation, candidate detection, and 996-ready delivery.",
        ]
    )


def edit_target_package_dir(
    *,
    upload_root: str | Path,
    style_code: str,
    screen_type: str,
    new_generation_job_id: str,
) -> Path:
    return Path(upload_root) / "996-ready" / style_code / screen_type / new_generation_job_id


def write_edit_metadata_report(
    *,
    package_dir: str | Path,
    style_code: str,
    screen_type: str,
    new_generation_job_id: str,
    parent_generation_job_id: str,
    edit_request: str,
    edit_mode: str,
    source_preview_path: str | Path,
    prompt: str,
) -> dict[str, Any]:
    report = write_delivery_report(
        package_dir=package_dir,
        style_code=style_code,
        screen_type=screen_type,
        generation_job_id=new_generation_job_id,
        screen_generation_mode="screen_edit",
        prompt=prompt,
        reference_image_path=source_preview_path,
    )
    report["edit_metadata"] = {
        "parent_generation_job_id": parent_generation_job_id,
        "edit_request": edit_request,
        "edit_mode": edit_mode,
        "style_code": style_code,
        "source_preview_path": str(source_preview_path),
    }
    package_path = Path(package_dir)
    (package_path / "delivery_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (package_path / "delivery_report.html").write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996 screen edit report</title></head><body>"
        "<h1>996 screen edit report</h1>"
        f"<p>style_code: <code>{html.escape(style_code)}</code></p>"
        f"<p>screen_type: <code>{html.escape(screen_type)}</code></p>"
        f"<p>new_generation_job_id: <code>{html.escape(new_generation_job_id)}</code></p>"
        f"<p>parent_generation_job_id: <code>{html.escape(parent_generation_job_id)}</code></p>"
        f"<p>edit_mode: <code>{html.escape(edit_mode)}</code></p>"
        f"<p>edit_request: {html.escape(edit_request)}</p>"
        "</body></html>",
        encoding="utf-8",
    )
    return report


def finalize_edit_package(
    *,
    generated_package: str | Path,
    target_package: str | Path,
    style_code: str,
    screen_type: str,
    new_generation_job_id: str,
    parent_generation_job_id: str,
    edit_request: str,
    edit_mode: str,
    source_preview_path: str | Path,
    prompt: str,
) -> dict[str, Any]:
    generated_path = Path(generated_package)
    target_path = Path(target_package)
    copy_package_to_style_dir(generated_path, target_path)
    delivery_report = write_edit_metadata_report(
        package_dir=target_path,
        style_code=style_code,
        screen_type=screen_type,
        new_generation_job_id=new_generation_job_id,
        parent_generation_job_id=parent_generation_job_id,
        edit_request=edit_request,
        edit_mode=edit_mode,
        source_preview_path=source_preview_path,
        prompt=prompt,
    )
    validation = validate_package(target_path)
    if not validation["ok"]:
        raise RuntimeError(f"Edited 996-ready package validation failed: {validation['errors']}")
    return {
        "style_code": style_code,
        "screen_type": screen_type,
        "generation_job_id": new_generation_job_id,
        "parent_generation_job_id": parent_generation_job_id,
        "package_dir": str(target_path),
        "delivery_report": delivery_report,
        "validation": validation,
    }


def edit_screen_with_style(
    *,
    style_code: str,
    screen_type: str,
    source_package: str | Path,
    edit_prompt: str,
    reference_image: str | Path | None = None,
    style_root: str | Path = "style_codes",
    database_path: str | Path = "backend/data/studio.db",
    upload_root: str | Path = "assets/uploads",
    project_id: str | None = None,
    provider_id: str | None = None,
) -> dict[str, Any]:
    source_package_path = Path(source_package)
    context = load_source_package_context(source_package_path)
    style = load_style(style_code, style_root)
    source_preview_path = Path(reference_image) if reference_image else source_package_path / "ui_preview.png"
    if not source_preview_path.exists():
        raise FileNotFoundError(f"Source preview image does not exist: {source_preview_path}")
    prompt = build_style_edit_prompt(
        style=style,
        screen_type=screen_type,
        source_package=source_package_path,
        context=context,
        edit_request=edit_prompt,
        source_preview_path=source_preview_path,
    )

    database = StudioDatabase(Path(database_path))
    database.initialize()
    selected_provider_id = ensure_real_provider_ready(database, provider_id)
    if project_id is None:
        project = database.create_project(
            ProjectCreate(name=f"{style_code} {screen_type} edit", description="Style-preserving screen edit", status="active")
        )
        project_id = project.id

    width, height = image_dimensions(source_preview_path)
    reference_asset = database.create_asset(
        AssetCreate(
            project_id=project_id,
            asset_type="reference_image",
            device_type="pc",
            width=width,
            height=height,
            file_path=str(source_preview_path),
            original_filename=source_preview_path.name,
            metadata_json=json.dumps(
                {
                    "style_code": style_code,
                    "screen_type": screen_type,
                    "source_package": str(source_package_path),
                    "edit_mode": EDIT_MODE,
                },
                ensure_ascii=False,
            ),
            source="uploaded",
            generation_job_id=None,
            thumbnail_path="",
        )
    )
    parent_job_id = parent_generation_job_id(source_package_path, context)
    job = database.create_generation_job(
        GenerationJobCreate(
            project_id=project_id,
            provider_id=selected_provider_id,
            job_type="real_ui_generation",
            status="pending",
            progress=0,
            input_json=json.dumps(
                {
                    "project_id": project_id,
                    "prompt": prompt,
                    "style_code": style_code,
                    "screen_type": screen_type,
                    "screen_generation_mode": "screen_edit",
                    "parent_generation_job_id": parent_job_id,
                    "edit_request": edit_prompt,
                    "edit_mode": EDIT_MODE,
                    "source_preview_path": str(source_preview_path),
                    "reference_image_id": reference_asset.id,
                    "reference_image_path": str(source_preview_path),
                    "device_type": "pc",
                    "width": 1024,
                    "height": 768,
                },
                ensure_ascii=False,
            ),
            output_json="",
            error_message="",
            logs="style-preserving screen edit queued",
        )
    )

    completed = JobRunnerService(database, Path(upload_root)).run(job.id)
    if completed is None:
        raise RuntimeError("Generation job could not be loaded after run")
    if completed.status != "completed":
        raise RuntimeError(f"Generation job failed: {completed.error_message}")
    output = parse_json_object(completed.output_json, "output_json")
    component_processing = output.get("component_processing")
    if not isinstance(component_processing, dict):
        raise RuntimeError("Generation job did not produce component_processing output")
    manifest_path = component_processing.get("manifest_path")
    if not isinstance(manifest_path, str) or not manifest_path:
        raise RuntimeError("component_processing output did not include manifest_path")

    target_package = edit_target_package_dir(
        upload_root=upload_root,
        style_code=style_code,
        screen_type=screen_type,
        new_generation_job_id=completed.id,
    )
    return finalize_edit_package(
        generated_package=Path(manifest_path).parent,
        target_package=target_package,
        style_code=style_code,
        screen_type=screen_type,
        new_generation_job_id=completed.id,
        parent_generation_job_id=parent_job_id,
        edit_request=edit_prompt,
        edit_mode=EDIT_MODE,
        source_preview_path=source_preview_path,
        prompt=prompt,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Edit one generated 996 UI screen while preserving STYLE_CODE.")
    parser.add_argument("--style-code", required=True)
    parser.add_argument("--screen-type", required=True, choices=sorted(SUPPORTED_SCREEN_TYPES))
    parser.add_argument("--source-package", required=True)
    parser.add_argument("--edit-prompt", required=True)
    parser.add_argument("--reference-image")
    parser.add_argument("--style-root", default="style_codes")
    parser.add_argument("--database-path", default="backend/data/studio.db")
    parser.add_argument("--upload-root", default="assets/uploads")
    parser.add_argument("--project-id")
    parser.add_argument("--provider-id")
    args = parser.parse_args()

    try:
        result = edit_screen_with_style(
            style_code=args.style_code,
            screen_type=args.screen_type,
            source_package=args.source_package,
            edit_prompt=args.edit_prompt,
            reference_image=args.reference_image,
            style_root=args.style_root,
            database_path=args.database_path,
            upload_root=args.upload_root,
            project_id=args.project_id,
            provider_id=args.provider_id,
        )
    except Exception as exc:
        print(f"Failed to edit style-guided screen: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
