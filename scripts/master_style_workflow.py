from __future__ import annotations

import argparse
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
from scripts.create_style_code import create_style_code
from scripts.generate_screen_with_style import (
    DEFAULT_DEVICE_TYPE,
    DEVICE_TYPES,
    copy_package_to_style_dir,
    device_prompt_line,
    ensure_real_provider_ready,
    generation_dimensions,
    image_dimensions,
    normalize_generation_device_type,
    target_package_dir,
    write_delivery_report,
)
from scripts.validate_996_export import validate_package


SCREEN_GENERATION_MODES = {"auto_generate", "reference_guided"}
MASTER_SCREEN_TYPES = {"main_ui", "role_ui", "bag_ui", "shop_ui", "activity_ui"}

MAIN_UI_CORE_ELEMENTS = [
    "avatar",
    "name",
    "level",
    "health bar",
    "mana bar",
    "bag",
    "role",
    "skills",
    "shop",
    "activity",
    "settings",
    "skill bar",
    "shortcut bar",
    "chat area",
    "map entry",
    "right-side function menu",
]


def build_master_main_ui_prompt(
    *,
    screen_generation_mode: str,
    style_name: str,
    screen_type: str = "main_ui",
    reference_image_path: str | Path | None = None,
    user_prompt: str = "",
    device_type: str = DEFAULT_DEVICE_TYPE,
) -> str:
    if screen_generation_mode not in SCREEN_GENERATION_MODES:
        raise ValueError(f"screen_generation_mode must be one of {sorted(SCREEN_GENERATION_MODES)}")
    if screen_type != "main_ui":
        raise ValueError("Master style creation must start from main_ui")
    if screen_generation_mode == "reference_guided" and not reference_image_path:
        raise ValueError("reference_guided mode requires reference_image_path")
    normalized_device_type = normalize_generation_device_type(device_type)
    target_width, target_height = generation_dimensions(normalized_device_type)

    mode_line = (
        "Auto generate a new main UI from the style brief."
        if screen_generation_mode == "auto_generate"
        else f"Reference image path: {Path(reference_image_path)}. keep the reference layout structure, but do not copy the reference image directly."
    )
    parts = [
        "Generate one 996 legend game main_ui screen as the master style source.",
        f"screen_generation_mode: {screen_generation_mode}",
        f"style_name: {style_name}",
        f"device_type: {normalized_device_type}",
        device_prompt_line(normalized_device_type),
        f"Target canvas is {target_width}x{target_height} pixels.",
        mode_line,
        "The layout may be adjusted, but the basic operation logic must not be broken.",
        "Required main UI elements:",
        ", ".join(MAIN_UI_CORE_ELEMENTS),
        "do not remove core entries.",
        "Do not hide core entries.",
        "Do not block chat area, skill bar, shortcut bar, or player info.",
        "Buttons must remain visually clickable and separated for later slicing.",
        "Allowed variation: color, ornament, borders, buttons, icons, font, and texture.",
        "Output a single game UI screen only, suitable for annotation, component slicing, and candidate detection.",
    ]
    if user_prompt:
        parts.append(f"User prompt: {user_prompt}")
    return "\n".join(parts)


def save_master_style_artifacts(
    *,
    style: dict[str, Any],
    package_dir: str | Path,
    style_root: str | Path,
) -> Path:
    style_code = str(style.get("style_code") or "")
    if not style_code:
        raise ValueError("style.style_code is required")
    package_path = Path(package_dir)
    style_dir = Path(style_root) / style_code
    style_dir.mkdir(parents=True, exist_ok=True)

    style_json_path = style_dir / "style.json"
    if not style_json_path.exists():
        style_json_path.write_text(json.dumps(style, ensure_ascii=False, indent=2), encoding="utf-8")

    if not (package_path / "delivery_report.json").exists() or not (package_path / "delivery_report.html").exists():
        manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
        write_delivery_report(
            package_dir=package_path,
            style_code=style_code,
            screen_type="main_ui",
            generation_job_id=str(manifest.get("generation_job_id") or package_path.name),
            screen_generation_mode="master_style_snapshot",
            prompt="",
            device_type=manifest.get("device_type"),
        )

    for name in [
        "ui_preview.png",
        "annotation.json",
        "manifest.json",
        "delivery_report.json",
        "delivery_report.html",
    ]:
        source = package_path / name
        target = style_dir / name
        if target.exists():
            raise RuntimeError(f"Style artifact already exists and will not be overwritten: {target}")
        if not source.exists():
            raise FileNotFoundError(f"Missing master style artifact source: {source}")
        shutil.copyfile(source, target)
    return style_dir


def create_master_style_from_package(
    *,
    package_dir: str | Path,
    style_root: str | Path = "style_codes",
    upload_root: str | Path = "assets/uploads",
    style_name: str | None = None,
    screen_generation_mode: str = "auto_generate",
    screen_type: str = "main_ui",
    prompt: str = "",
    reference_image_path: str | Path | None = None,
    device_type: str = DEFAULT_DEVICE_TYPE,
) -> dict[str, Any]:
    if screen_type != "main_ui":
        raise ValueError("Master style package creation must use main_ui")
    if screen_generation_mode not in SCREEN_GENERATION_MODES:
        raise ValueError(f"screen_generation_mode must be one of {sorted(SCREEN_GENERATION_MODES)}")
    normalized_device_type = normalize_generation_device_type(device_type)

    source_package = Path(package_dir)
    style = create_style_code(package_dir=source_package, style_root=style_root, style_name=style_name)
    style_code = str(style["style_code"])
    generation_job_id = str(style["source_job_id"])
    final_package = target_package_dir(
        upload_root=upload_root,
        style_code=style_code,
        screen_type=screen_type,
        generation_job_id=generation_job_id,
    )
    copy_package_to_style_dir(source_package, final_package)
    delivery_report = write_delivery_report(
        package_dir=final_package,
        style_code=style_code,
        screen_type=screen_type,
        generation_job_id=generation_job_id,
        screen_generation_mode=screen_generation_mode,
        prompt=prompt,
        device_type=normalized_device_type,
        reference_image_path=reference_image_path,
    )
    style_dir = save_master_style_artifacts(style=style, package_dir=final_package, style_root=style_root)
    validation = validate_package(final_package)
    if not validation["ok"]:
        raise RuntimeError(f"Final 996-ready package validation failed: {validation['errors']}")
    return {
        "style_code": style_code,
        "style_dir": str(style_dir),
        "screen_type": screen_type,
        "device_type": normalized_device_type,
        "generation_job_id": generation_job_id,
        "package_dir": str(final_package),
        "delivery_report": delivery_report,
        "validation": validation,
    }


def run_master_style_workflow(
    *,
    screen_generation_mode: str,
    style_name: str,
    prompt: str = "",
    reference_image: str | Path | None = None,
    style_root: str | Path = "style_codes",
    database_path: str | Path = "backend/data/studio.db",
    upload_root: str | Path = "assets/uploads",
    project_id: str | None = None,
    provider_id: str | None = None,
    device_type: str = DEFAULT_DEVICE_TYPE,
) -> dict[str, Any]:
    normalized_device_type = normalize_generation_device_type(device_type)
    target_width, target_height = generation_dimensions(normalized_device_type)
    reference_path = Path(reference_image) if reference_image else None
    if reference_path is not None and not reference_path.exists():
        raise FileNotFoundError(f"Reference image does not exist: {reference_path}")
    master_prompt = build_master_main_ui_prompt(
        screen_generation_mode=screen_generation_mode,
        style_name=style_name,
        screen_type="main_ui",
        reference_image_path=reference_path,
        user_prompt=prompt,
        device_type=normalized_device_type,
    )

    database = StudioDatabase(Path(database_path))
    database.initialize()
    selected_provider_id = ensure_real_provider_ready(database, provider_id)
    if project_id is None:
        project = database.create_project(
            ProjectCreate(name=f"Master Style {style_name}", description="Master style main_ui", status="active")
        )
        project_id = project.id

    reference_asset_id = None
    if reference_path is not None:
        width, height = image_dimensions(reference_path)
        reference_asset = database.create_asset(
            AssetCreate(
                project_id=project_id,
                asset_type="reference_image",
                device_type=normalized_device_type,
                width=width,
                height=height,
                file_path=str(reference_path),
                original_filename=reference_path.name,
                metadata_json=json.dumps({"screen_generation_mode": screen_generation_mode}, ensure_ascii=False),
                source="uploaded",
                generation_job_id=None,
                thumbnail_path="",
            )
        )
        reference_asset_id = reference_asset.id

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
                    "prompt": master_prompt,
                    "screen_generation_mode": screen_generation_mode,
                    "screen_type": "main_ui",
                    "style_name": style_name,
                    "reference_image_id": reference_asset_id,
                    "reference_image_path": str(reference_path) if reference_path else None,
                    "device_type": normalized_device_type,
                    "width": target_width,
                    "height": target_height,
                },
                ensure_ascii=False,
            ),
            output_json="",
            error_message="",
            logs="master style main_ui queued",
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

    return create_master_style_from_package(
        package_dir=Path(manifest_path).parent,
        style_root=style_root,
        upload_root=upload_root,
        style_name=style_name,
        screen_generation_mode=screen_generation_mode,
        screen_type="main_ui",
        prompt=master_prompt,
        reference_image_path=reference_path,
        device_type=normalized_device_type,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a master STYLE_CODE from a generated main_ui.")
    parser.add_argument("--screen-generation-mode", required=True, choices=sorted(SCREEN_GENERATION_MODES))
    parser.add_argument("--style-name", required=True)
    parser.add_argument("--prompt", default="")
    parser.add_argument("--reference-image")
    parser.add_argument("--style-root", default="style_codes")
    parser.add_argument("--database-path", default="backend/data/studio.db")
    parser.add_argument("--upload-root", default="assets/uploads")
    parser.add_argument("--project-id")
    parser.add_argument("--provider-id")
    parser.add_argument("--device-type", choices=sorted(DEVICE_TYPES), default=DEFAULT_DEVICE_TYPE)
    args = parser.parse_args()

    try:
        result = run_master_style_workflow(
            screen_generation_mode=args.screen_generation_mode,
            style_name=args.style_name,
            prompt=args.prompt,
            reference_image=args.reference_image,
            style_root=args.style_root,
            database_path=args.database_path,
            upload_root=args.upload_root,
            project_id=args.project_id,
            provider_id=args.provider_id,
            device_type=args.device_type,
        )
    except Exception as exc:
        print(f"Failed to run master style workflow: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
