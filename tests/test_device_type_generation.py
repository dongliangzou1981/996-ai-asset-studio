from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from scripts.create_style_code import create_style_code
from scripts.generate_screen_with_style import (
    DEFAULT_DEVICE_TYPE,
    build_reference_guided_prompt,
    generation_dimensions,
    normalize_generation_device_type,
    write_delivery_report,
)
from scripts.master_style_workflow import build_master_main_ui_prompt
from scripts.validate_996_export import validate_package


def copy_demo_package(target: Path) -> None:
    source_package = Path(__file__).parent / "fixtures" / "996_ready_demo"
    shutil.copytree(source_package, target)


def update_device_package(package: Path, *, device_type: str, width: int, height: int) -> None:
    manifest_path = package / "manifest.json"
    annotation_path = package / "annotation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
    manifest["device_type"] = device_type
    manifest["resolution"] = {"width": width, "height": height}
    annotation["device_type"] = device_type
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    annotation_path.write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")


def test_device_type_defaults_and_dimensions() -> None:
    assert DEFAULT_DEVICE_TYPE == "mobile_landscape"
    assert normalize_generation_device_type(None) == "mobile_landscape"
    assert normalize_generation_device_type("mobile") == "mobile_landscape"
    assert normalize_generation_device_type("pc") == "pc_landscape"
    assert generation_dimensions("mobile_landscape") == (1536, 864)
    assert generation_dimensions("pc_landscape") == (1536, 1024)


def test_prompts_include_device_specific_constraints(tmp_path: Path) -> None:
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

    mobile_prompt = build_reference_guided_prompt(style=style, screen_type="main_ui")
    pc_prompt = build_reference_guided_prompt(style=style, screen_type="main_ui", device_type="pc_landscape")
    master_prompt = build_master_main_ui_prompt(
        screen_generation_mode="auto_generate",
        style_name="Dark Gold Dragon",
        device_type="pc_landscape",
    )

    assert "device_type: mobile_landscape" in mobile_prompt
    assert "strict 16:9 landscape" in mobile_prompt
    assert "horizontal mobile game UI" in mobile_prompt
    assert "large touch-friendly buttons" in mobile_prompt
    assert "1536x864" in mobile_prompt
    assert "device_type: pc_landscape" in pc_prompt
    assert "mouse clicking" in pc_prompt
    assert "1536x1024" in pc_prompt
    assert "pc_landscape" in master_prompt


def test_validator_enforces_mobile_landscape_16_9(tmp_path: Path) -> None:
    package = tmp_path / "mobile-package"
    copy_demo_package(package)
    update_device_package(package, device_type="mobile_landscape", width=1536, height=864)

    assert validate_package(package)["ok"] is True

    bad_package = tmp_path / "bad-mobile-package"
    copy_demo_package(bad_package)
    update_device_package(bad_package, device_type="mobile_landscape", width=1536, height=1024)
    report = validate_package(bad_package)

    assert report["ok"] is False
    assert report["checks"]["device_resolution"] is False
    assert "manifest.resolution must be 16:9 landscape for mobile_landscape" in report["errors"]


def test_validator_accepts_pc_landscape_4_3(tmp_path: Path) -> None:
    package = tmp_path / "pc-package"
    copy_demo_package(package)
    update_device_package(package, device_type="pc_landscape", width=1536, height=1024)

    assert validate_package(package)["ok"] is True


def test_style_and_delivery_reports_record_device_type(tmp_path: Path) -> None:
    package = tmp_path / "pc-package"
    copy_demo_package(package)
    update_device_package(package, device_type="pc_landscape", width=1536, height=1024)

    style = create_style_code(package_dir=package, style_root=tmp_path / "style_codes")
    report = write_delivery_report(
        package_dir=package,
        style_code=style["style_code"],
        screen_type="main_ui",
        generation_job_id="job-001",
        screen_generation_mode="auto_generate",
        prompt="prompt",
        device_type="pc_landscape",
    )

    saved_report = json.loads((package / "delivery_report.json").read_text(encoding="utf-8"))
    assert style["device_type"] == "pc_landscape"
    assert report["device_type"] == "pc_landscape"
    assert saved_report["device_type"] == "pc_landscape"
