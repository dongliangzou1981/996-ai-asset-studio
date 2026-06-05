from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.component_processing import process_ui_preview_components
from app.db import StudioDatabase
from app.schemas import AssetCreate, GenerationJobCreate, ProjectCreate
from scripts.generate_screen_with_style import build_reference_guided_prompt, write_delivery_report
from scripts.validate_996_export import validate_package


def create_preview(path: Path) -> None:
    Image.new("RGBA", (1280, 720), color=(32, 38, 48, 255)).save(path, format="PNG")


def test_resource_production_metadata_flows_into_996_ready_package(tmp_path: Path) -> None:
    database = StudioDatabase(tmp_path / "studio.db")
    database.initialize()
    project = database.create_project(ProjectCreate(name="Resource Production", status="active"))
    job = database.create_generation_job(
        GenerationJobCreate(
            project_id=project.id,
            job_type="real_ui_generation",
            input_json=json.dumps({"asset_mode": "resource_production"}),
            logs="queued",
        )
    )
    preview_path = tmp_path / "ui_preview.png"
    create_preview(preview_path)
    asset = database.create_asset(
        AssetCreate(
            project_id=project.id,
            asset_type="ui_preview",
            device_type="mobile_landscape",
            width=1280,
            height=720,
            file_path=str(preview_path),
            original_filename="ui_preview.png",
            metadata_json=json.dumps({"asset_mode": "resource_production"}, ensure_ascii=False),
            source="ai_generated",
            generation_job_id=job.id,
            thumbnail_path="",
        )
    )

    result = process_ui_preview_components(database=database, upload_root=tmp_path / "uploads", ui_preview=asset)
    package_dir = Path(str(result["manifest_path"])).parent
    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))
    annotation = json.loads((package_dir / "annotation.json").read_text(encoding="utf-8"))
    candidate_manifest = json.loads((package_dir / "candidate_manifest.json").read_text(encoding="utf-8"))

    assert validate_package(package_dir)["ok"] is True
    assert manifest["asset_mode"] == "resource_production"
    assert annotation["asset_mode"] == "resource_production"
    assert candidate_manifest["asset_mode"] == "resource_production"
    assert manifest["transparent_policy"]["required_component_types"] == ["button", "icon", "frame", "input"]
    assert manifest["resource_summary"]["classification"] == "template_and_candidate"
    assert manifest["components"][0]["resource_category"] == "layout_bar"
    assert manifest["components"][0]["production_usage"] == "layout_or_full_region"
    assert candidate_manifest["candidates"][0]["resource_category"].endswith("_asset")
    assert "transparent" in candidate_manifest["candidates"][0]


def test_resource_production_prompt_and_report_include_asset_mode(tmp_path: Path) -> None:
    style = {
        "style_code": "STYLE_0001",
        "style_name": "Dark Gold Dragon",
        "style_summary": "dark gold dragon master style",
        "color_palette": ["#1A120E", "#D9A441"],
        "font_style": "bold readable Chinese fantasy type",
        "border_style": "gold carved borders",
        "button_style": "dark glossy buttons",
        "icon_style": "high contrast icons",
        "texture_style": "aged metal texture",
    }
    prompt = build_reference_guided_prompt(
        style=style,
        screen_type="main_ui",
        asset_mode="resource_production",
    )
    report = write_delivery_report(
        package_dir=tmp_path,
        style_code="STYLE_0001",
        screen_type="main_ui",
        generation_job_id="job-001",
        screen_generation_mode="auto_generate",
        prompt=prompt,
        asset_mode="resource_production",
    )

    assert "asset_mode: resource_production" in prompt
    assert "transparent-background-ready parts" in prompt
    assert report["asset_mode"] == "resource_production"
    assert json.loads((tmp_path / "delivery_report.json").read_text(encoding="utf-8"))["asset_mode"] == "resource_production"
