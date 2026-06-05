from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.create_style_code import create_style_code


def create_package(package_dir: Path, *, job_id: str, asset_id: str) -> None:
    package_dir.mkdir(parents=True)
    Image.new("RGBA", (1024, 768), color=(42, 31, 24, 255)).save(package_dir / "ui_preview.png")
    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "package_type": "996-ready",
                "source_asset_id": asset_id,
                "generation_job_id": job_id,
                "device_type": "pc",
                "resolution": {"width": 1024, "height": 768},
                "ui_preview": "ui_preview.png",
                "components_dir": "components",
                "components": [],
            }
        ),
        encoding="utf-8",
    )


def test_create_style_code_from_996_ready_package(tmp_path: Path) -> None:
    package_dir = tmp_path / "996-ready" / "job-001"
    create_package(package_dir, job_id="job-001", asset_id="asset-001")

    style = create_style_code(
        package_dir=package_dir,
        style_root=tmp_path / "style_codes",
        style_name="Dark Gold Dragon",
    )

    style_path = tmp_path / "style_codes" / "STYLE_0001" / "style.json"
    assert style_path.exists()
    saved = json.loads(style_path.read_text(encoding="utf-8"))
    assert style == saved
    assert saved["style_code"] == "STYLE_0001"
    assert saved["style_name"] == "Dark Gold Dragon"
    assert saved["source_job_id"] == "job-001"
    assert saved["source_asset_id"] == "asset-001"
    assert saved["original_ui_preview"].endswith("ui_preview.png")
    assert saved["style_summary"]
    assert saved["color_palette"]
    assert saved["font_style"]
    assert saved["border_style"]
    assert saved["button_style"]
    assert saved["icon_style"]
    assert saved["texture_style"]
    assert saved["created_at"] == saved["updated_at"]


def test_create_style_code_allocates_next_code(tmp_path: Path) -> None:
    first_package = tmp_path / "first"
    second_package = tmp_path / "second"
    create_package(first_package, job_id="job-001", asset_id="asset-001")
    create_package(second_package, job_id="job-002", asset_id="asset-002")

    first = create_style_code(package_dir=first_package, style_root=tmp_path / "style_codes")
    second = create_style_code(package_dir=second_package, style_root=tmp_path / "style_codes")

    assert first["style_code"] == "STYLE_0001"
    assert second["style_code"] == "STYLE_0002"
