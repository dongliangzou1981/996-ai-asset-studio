from __future__ import annotations

import argparse
import html
import json
import os
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
from scripts.validate_996_export import validate_package


SUPPORTED_SCREEN_TYPES = {"main_ui", "role_ui", "bag_ui", "shop_ui", "activity_ui"}
REAL_PROVIDER_TYPES = {"openai", "ofox"}
DEVICE_TYPES = {"mobile_landscape", "pc_landscape"}
DEFAULT_DEVICE_TYPE = "mobile_landscape"
ASSET_MODES = {"ui_package", "resource_production"}
DEFAULT_ASSET_MODE = "ui_package"

DEVICE_PROFILES = {
    "mobile_landscape": {
        "width": 1536,
        "height": 864,
        "prompt": (
            "Device target: mobile_landscape. Use a strict 16:9 landscape horizontal mobile game UI, "
            "large touch-friendly buttons, and mobile-adapted skill bar, chat area, right menu, and minimap."
        ),
    },
    "pc_landscape": {
        "width": 1536,
        "height": 1024,
        "prompt": (
            "Device target: pc_landscape. Use a PC landscape UI for mouse clicking, "
            "with a denser information area and desktop-oriented interaction spacing."
        ),
    },
}

SCREEN_TYPE_GOALS = {
    "main_ui": "main game HUD with player info, core entries, chat, map, skill bar, and shortcut bar",
    "role_ui": "role panel with character preview, equipment slots, combat power, and attribute list",
    "bag_ui": "bag inventory with item grid, tabs, item detail area, and action buttons",
    "shop_ui": "shop interface with category tabs, product cards, price labels, and purchase buttons",
    "activity_ui": "activity interface with event list, reward preview, progress, and claim buttons",
}


def load_style(style_code: str, style_root: str | Path = "style_codes") -> dict[str, Any]:
    path = Path(style_root) / style_code / "style.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Style code not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Style JSON is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("style.json must contain a JSON object")
    return data


def normalize_generation_device_type(device_type: str | None = None) -> str:
    if not device_type:
        return DEFAULT_DEVICE_TYPE
    if device_type == "mobile":
        return "mobile_landscape"
    if device_type in {"pc", "desktop"}:
        return "pc_landscape"
    if device_type not in DEVICE_TYPES:
        raise ValueError(f"device_type must be one of {sorted(DEVICE_TYPES)}")
    return device_type


def generation_dimensions(device_type: str) -> tuple[int, int]:
    normalized = normalize_generation_device_type(device_type)
    profile = DEVICE_PROFILES[normalized]
    return int(profile["width"]), int(profile["height"])


def device_prompt_line(device_type: str) -> str:
    normalized = normalize_generation_device_type(device_type)
    return str(DEVICE_PROFILES[normalized]["prompt"])


def normalize_asset_mode(asset_mode: str | None = None) -> str:
    if not asset_mode:
        return DEFAULT_ASSET_MODE
    if asset_mode not in ASSET_MODES:
        raise ValueError(f"asset_mode must be one of {sorted(ASSET_MODES)}")
    return asset_mode


def asset_mode_prompt_line(asset_mode: str) -> str:
    normalized = normalize_asset_mode(asset_mode)
    if normalized == "resource_production":
        return (
            "asset_mode: resource_production. Prioritize reusable 996 production resources: "
            "clear separable buttons, icons, frames, inputs, tabs, slots, transparent-background-ready parts, "
            "and clean component boundaries for later editing."
        )
    return "asset_mode: ui_package. Generate a complete 996-ready UI package with preview, annotation, slices, and candidates."


def build_reference_guided_prompt(
    *,
    style: dict[str, Any],
    screen_type: str,
    reference_image_path: str | Path | None = None,
    user_prompt: str = "",
    device_type: str = DEFAULT_DEVICE_TYPE,
    asset_mode: str = DEFAULT_ASSET_MODE,
) -> str:
    if screen_type not in SUPPORTED_SCREEN_TYPES:
        raise ValueError(f"screen_type must be one of {sorted(SUPPORTED_SCREEN_TYPES)}")
    normalized_device_type = normalize_generation_device_type(device_type)
    normalized_asset_mode = normalize_asset_mode(asset_mode)
    target_width, target_height = generation_dimensions(normalized_device_type)
    style_code = str(style.get("style_code") or "")
    style_name = str(style.get("style_name") or style_code)
    palette = style.get("color_palette") or []
    palette_text = ", ".join(str(color) for color in palette) if isinstance(palette, list) else str(palette)
    reference_line = (
        f"Reference image path: {Path(reference_image_path)}. Keep the reference layout structure, main area ratios, information hierarchy, and UI rhythm."
        if reference_image_path
        else "No reference image supplied. Inherit the master style and use a conventional 996 legend game layout for this screen type."
    )
    parts = [
        "Generate one 996 legend game UI screen.",
        f"style_code: {style_code}",
        f"style_name: {style_name}",
        f"screen_type: {screen_type}",
        f"screen_goal: {SCREEN_TYPE_GOALS[screen_type]}",
        reference_line,
        "Do not copy the reference image directly, and do not reuse its exact artwork, text, characters, or trademarks.",
        "Use the specified style_code as the master visual style for color, typography, border, button, icon, and texture decisions.",
        f"style_summary: {style.get('style_summary', '')}",
        f"color_palette: {palette_text}",
        f"font_style: {style.get('font_style', '')}",
        f"border_style: {style.get('border_style', '')}",
        f"button_style: {style.get('button_style', '')}",
        f"icon_style: {style.get('icon_style', '')}",
        f"texture_style: {style.get('texture_style', '')}",
        f"device_type: {normalized_device_type}",
        device_prompt_line(normalized_device_type),
        asset_mode_prompt_line(normalized_asset_mode),
        f"Target canvas is {target_width}x{target_height} pixels.",
        "Output a single screen only. Do not create a collage, tutorial page, or multi-screen sheet.",
        "Make it suitable for later slicing and annotation: buttons, icons, inputs, frames, tabs, and inventory slots should have clear boundaries.",
    ]
    if user_prompt:
        parts.append(f"User prompt: {user_prompt}")
    return "\n".join(parts)


def target_package_dir(
    *,
    upload_root: str | Path,
    style_code: str,
    screen_type: str,
    generation_job_id: str,
) -> Path:
    return Path(upload_root) / "996-ready" / style_code / screen_type / generation_job_id


def image_dimensions(path: Path) -> tuple[int, int]:
    from PIL import Image

    with Image.open(path) as image:
        return image.size


def ensure_real_provider_ready(database: StudioDatabase, provider_id: str | None = None) -> str:
    providers = database.list_ai_providers()
    if provider_id:
        providers = [provider for provider in providers if provider.id == provider_id]
    providers = [provider for provider in providers if provider.enabled and provider.type in REAL_PROVIDER_TYPES]
    if not providers:
        raise RuntimeError("No enabled real provider found. Configure an enabled openai or ofox provider first.")
    provider = providers[0]
    config = parse_json_object(provider.config_json, "provider config_json")
    api_key_env = str(config.get("api_key_env") or "")
    if not api_key_env:
        raise RuntimeError(f"{provider.type} provider requires config_json.api_key_env")
    if not os.getenv(api_key_env):
        raise RuntimeError(f"Environment variable {api_key_env} is not set")
    return provider.id


def copy_package_to_style_dir(source_package: Path, target_package: Path) -> None:
    target_package.parent.mkdir(parents=True, exist_ok=True)
    if target_package.exists():
        raise RuntimeError(f"Target package already exists: {target_package}")
    shutil.copytree(source_package, target_package)


def write_delivery_report(
    *,
    package_dir: str | Path,
    style_code: str,
    screen_type: str,
    generation_job_id: str,
    screen_generation_mode: str,
    prompt: str,
    device_type: str | None = None,
    asset_mode: str | None = None,
    reference_image_path: str | Path | None = None,
) -> dict[str, Any]:
    package_path = Path(package_dir)
    report = {
        "style_code": style_code,
        "screen_type": screen_type,
        "generation_job_id": generation_job_id,
        "screen_generation_mode": screen_generation_mode,
        "device_type": normalize_generation_device_type(device_type),
        "asset_mode": normalize_asset_mode(asset_mode),
        "reference_image_path": str(reference_image_path) if reference_image_path else None,
        "prompt": prompt,
        "outputs": {
            "ui_preview": "ui_preview.png",
            "manifest": "manifest.json",
            "annotation": "annotation.json",
            "preview": "preview.html",
            "candidate_manifest": "candidate_manifest.json",
            "candidate_preview": "candidate_preview.html",
            "components_dir": "components",
            "candidates_dir": "candidates",
        },
    }
    json_path = package_path / "delivery_report.json"
    html_path = package_path / "delivery_report.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996 delivery report</title></head><body>"
        "<h1>996 delivery report</h1>"
        f"<p>style_code: <code>{html.escape(style_code)}</code></p>"
        f"<p>screen_type: <code>{html.escape(screen_type)}</code></p>"
        f"<p>generation_job_id: <code>{html.escape(generation_job_id)}</code></p>"
        f"<p>screen_generation_mode: <code>{html.escape(screen_generation_mode)}</code></p>"
        "<h2>outputs</h2><ul>"
        + "".join(f"<li><code>{html.escape(str(path))}</code></li>" for path in report["outputs"].values())
        + "</ul></body></html>",
        encoding="utf-8",
    )
    return report


def generate_screen_with_style(
    *,
    style_code: str,
    screen_type: str,
    reference_image: str | Path | None = None,
    user_prompt: str = "",
    style_root: str | Path = "style_codes",
    database_path: str | Path = "backend/data/studio.db",
    upload_root: str | Path = "assets/uploads",
    project_id: str | None = None,
    provider_id: str | None = None,
    device_type: str = DEFAULT_DEVICE_TYPE,
    asset_mode: str = DEFAULT_ASSET_MODE,
) -> dict[str, Any]:
    if screen_type not in SUPPORTED_SCREEN_TYPES:
        raise ValueError(f"screen_type must be one of {sorted(SUPPORTED_SCREEN_TYPES)}")
    normalized_device_type = normalize_generation_device_type(device_type)
    normalized_asset_mode = normalize_asset_mode(asset_mode)
    target_width, target_height = generation_dimensions(normalized_device_type)
    reference_path = Path(reference_image) if reference_image else None
    if reference_path is not None and not reference_path.exists():
        raise FileNotFoundError(f"Reference image does not exist: {reference_path}")

    style = load_style(style_code, style_root)
    prompt = build_reference_guided_prompt(
        style=style,
        screen_type=screen_type,
        reference_image_path=reference_path,
        user_prompt=user_prompt,
        device_type=normalized_device_type,
        asset_mode=normalized_asset_mode,
    )

    database = StudioDatabase(Path(database_path))
    database.initialize()
    selected_provider_id = ensure_real_provider_ready(database, provider_id)
    if project_id is None:
        project = database.create_project(
            ProjectCreate(name=f"{style_code} {screen_type}", description="Style-guided single screen", status="active")
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
                metadata_json=json.dumps({"style_code": style_code, "screen_type": screen_type}, ensure_ascii=False),
                source="uploaded",
                generation_job_id=None,
                thumbnail_path="",
            )
        )
        reference_asset_id = reference_asset.id

    screen_generation_mode = "reference_guided" if reference_path else "style_inheritance"
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
                    "screen_generation_mode": screen_generation_mode,
                    "asset_mode": normalized_asset_mode,
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
            logs="style-guided screen queued",
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

    source_package = Path(manifest_path).parent
    final_package = target_package_dir(
        upload_root=upload_root,
        style_code=style_code,
        screen_type=screen_type,
        generation_job_id=completed.id,
    )
    copy_package_to_style_dir(source_package, final_package)
    write_delivery_report(
        package_dir=final_package,
        style_code=style_code,
        screen_type=screen_type,
        generation_job_id=completed.id,
        screen_generation_mode=screen_generation_mode,
        prompt=prompt,
        device_type=normalized_device_type,
        asset_mode=normalized_asset_mode,
        reference_image_path=reference_path,
    )
    report = validate_package(final_package)
    if not report["ok"]:
        raise RuntimeError(f"Final 996-ready package validation failed: {report['errors']}")

    return {
        "style_code": style_code,
        "screen_type": screen_type,
        "device_type": normalized_device_type,
        "asset_mode": normalized_asset_mode,
        "generation_job_id": completed.id,
        "reference_asset_id": reference_asset_id,
        "prompt": prompt,
        "source_package_dir": str(source_package),
        "package_dir": str(final_package),
        "validation": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one 996 UI screen from a style code and optional reference image.")
    parser.add_argument("--style-code", required=True)
    parser.add_argument("--screen-type", required=True, choices=sorted(SUPPORTED_SCREEN_TYPES))
    parser.add_argument("--reference-image")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--style-root", default="style_codes")
    parser.add_argument("--database-path", default="backend/data/studio.db")
    parser.add_argument("--upload-root", default="assets/uploads")
    parser.add_argument("--project-id")
    parser.add_argument("--provider-id")
    parser.add_argument("--device-type", choices=sorted(DEVICE_TYPES), default=DEFAULT_DEVICE_TYPE)
    parser.add_argument("--asset-mode", choices=sorted(ASSET_MODES), default=DEFAULT_ASSET_MODE)
    args = parser.parse_args()

    try:
        result = generate_screen_with_style(
            style_code=args.style_code,
            screen_type=args.screen_type,
            reference_image=args.reference_image,
            user_prompt=args.prompt,
            style_root=args.style_root,
            database_path=args.database_path,
            upload_root=args.upload_root,
            project_id=args.project_id,
            provider_id=args.provider_id,
            device_type=args.device_type,
            asset_mode=args.asset_mode,
        )
    except Exception as exc:
        print(f"Failed to generate style-guided screen: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
