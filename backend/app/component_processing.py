from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from app.db import StudioDatabase
from app.schemas import Asset, AssetCreate


COMPONENT_RULES = [
    ("main_bottom_bar", 0.0, 0.82, 1.0, 0.18),
    ("left_status_panel", 0.0, 0.0, 0.24, 0.22),
    ("right_menu_panel", 0.76, 0.0, 0.24, 0.35),
    ("minimap_area", 0.76, 0.36, 0.22, 0.24),
    ("chat_panel", 0.02, 0.58, 0.34, 0.22),
    ("skill_area", 0.56, 0.62, 0.42, 0.2),
]


def process_ui_preview_components(
    *,
    database: StudioDatabase,
    upload_root: Path,
    ui_preview: Asset,
) -> dict[str, str | list[str]]:
    source_path = Path(ui_preview.file_path)
    if not source_path.exists():
        raise FileNotFoundError("UI preview file does not exist")

    output_root = upload_root / "996-ready" / (ui_preview.generation_job_id or ui_preview.id)
    component_dir = output_root / "components"
    component_dir.mkdir(parents=True, exist_ok=True)

    copied_preview = output_root / "ui_preview.png"
    shutil.copyfile(source_path, copied_preview)

    component_assets: list[Asset] = []
    manifest_components: list[dict[str, Any]] = []
    annotation_components: list[dict[str, Any]] = []

    with Image.open(source_path).convert("RGBA") as image:
        source_width, source_height = image.size
        for component_type, x_ratio, y_ratio, width_ratio, height_ratio in COMPONENT_RULES:
            x = round(source_width * x_ratio)
            y = round(source_height * y_ratio)
            width = max(1, round(source_width * width_ratio))
            height = max(1, round(source_height * height_ratio))
            width = min(width, source_width - x)
            height = min(height, source_height - y)
            component_id = component_type
            file_name = f"{component_type}.png"
            component_path = component_dir / file_name
            image.crop((x, y, x + width, y + height)).save(component_path, format="PNG")

            manifest_components.append(
                {
                    "component_id": component_id,
                    "type": component_type,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "file_name": file_name,
                }
            )
            annotation_components.append(
                {
                    "component_id": component_id,
                    "component_type": component_type,
                    "x": x,
                    "y": y,
                    "width": width,
                    "height": height,
                    "font_family": "Microsoft YaHei",
                    "font_size": 16,
                    "font_color": "#F5D78E",
                    "notes": "Template-based Sprint 8A annotation",
                }
            )
            component_assets.append(
                database.create_asset(
                    AssetCreate(
                        project_id=ui_preview.project_id,
                        asset_type="sliced_component",
                        device_type=ui_preview.device_type,
                        width=width,
                        height=height,
                        file_path=str(component_path),
                        original_filename=file_name,
                        metadata_json=json.dumps(
                            {
                                "component_id": component_id,
                                "component_type": component_type,
                                "source_asset_id": ui_preview.id,
                                "template": "main_ui",
                            },
                            ensure_ascii=False,
                        ),
                        source="component_processing",
                        generation_job_id=ui_preview.generation_job_id,
                        thumbnail_path="",
                    )
                )
            )

    manifest = {
        "template": "main_ui",
        "source_asset_id": ui_preview.id,
        "ui_preview": str(copied_preview),
        "components_dir": str(component_dir),
        "components": manifest_components,
    }
    annotation = {
        "template": "main_ui",
        "source_asset_id": ui_preview.id,
        "components": annotation_components,
    }

    manifest_path = output_root / "manifest.json"
    annotation_path = output_root / "annotation.json"
    preview_html_path = output_root / "preview.html"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    annotation_path.write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")
    preview_html_path.write_text(render_preview_html(manifest_components), encoding="utf-8")

    return {
        "manifest_path": str(manifest_path),
        "annotation_path": str(annotation_path),
        "preview_html_path": str(preview_html_path),
        "component_asset_ids": [asset.id for asset in component_assets],
    }


def render_preview_html(components: list[dict[str, Any]]) -> str:
    items = "\n".join(
        f"<li><code>{html.escape(component['file_name'])}</code> "
        f"{html.escape(component['type'])} "
        f"({component['x']}, {component['y']}, {component['width']}x{component['height']})</li>"
        for component in components
    )
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>996-ready Preview</title></head><body>"
        "<h1>996-ready Component Preview</h1>"
        f"<ul>{items}</ul>"
        "</body></html>"
    )
