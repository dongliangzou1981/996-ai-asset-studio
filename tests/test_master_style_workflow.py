from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.generate_screen_with_style import build_reference_guided_prompt
from scripts.master_style_workflow import (
    MASTER_SCREEN_TYPES,
    SCREEN_GENERATION_MODES,
    build_master_main_ui_prompt,
    create_master_style_from_package,
    save_master_style_artifacts,
)
from scripts.validate_996_export import validate_package


def copy_demo_package(target: Path, *, job_id: str, asset_id: str) -> None:
    source_package = Path(__file__).parent / "fixtures" / "996_ready_demo"
    shutil.copytree(source_package, target)
    manifest_path = target / "manifest.json"
    annotation_path = target / "annotation.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    annotation = json.loads(annotation_path.read_text(encoding="utf-8"))
    manifest["generation_job_id"] = job_id
    manifest["source_asset_id"] = asset_id
    annotation["source_asset_id"] = asset_id
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    annotation_path.write_text(json.dumps(annotation, ensure_ascii=False, indent=2), encoding="utf-8")


def test_master_style_modes_and_screen_types_are_explicit() -> None:
    assert SCREEN_GENERATION_MODES == {"auto_generate", "reference_guided"}
    assert MASTER_SCREEN_TYPES == {"main_ui", "role_ui", "bag_ui", "shop_ui", "activity_ui"}


def test_auto_generate_main_ui_prompt_keeps_core_operation_layout() -> None:
    prompt = build_master_main_ui_prompt(
        screen_generation_mode="auto_generate",
        style_name="Dark Gold Dragon",
        screen_type="main_ui",
        user_prompt="strong dragon ornament and clear combat controls",
    )

    for required in [
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
    ]:
        assert required in prompt
    assert "do not remove core entries" in prompt
    assert "strict 16:9 landscape" in prompt
    assert "1536x864" in prompt
    assert "strong dragon ornament" in prompt


def test_reference_guided_main_ui_prompt_records_reference_without_copying_it(tmp_path: Path) -> None:
    reference = tmp_path / "main-reference.png"
    reference.write_bytes(b"reference")

    prompt = build_master_main_ui_prompt(
        screen_generation_mode="reference_guided",
        style_name="Retro Red Gold",
        screen_type="main_ui",
        reference_image_path=reference,
        user_prompt="use red gold festive ornament",
    )

    assert str(reference) in prompt
    assert "keep the reference layout structure" in prompt
    assert "do not copy the reference image directly" in prompt
    assert "Retro Red Gold" in prompt


def test_create_master_style_from_package_saves_style_artifacts_and_nested_output(tmp_path: Path) -> None:
    source_package = tmp_path / "996-ready" / "source-job"
    copy_demo_package(source_package, job_id="source-job", asset_id="asset-main")

    result = create_master_style_from_package(
        package_dir=source_package,
        style_root=tmp_path / "style_codes",
        upload_root=tmp_path / "uploads",
        style_name="Dark Gold Dragon",
        screen_generation_mode="auto_generate",
        screen_type="main_ui",
        prompt="master main ui prompt",
    )

    assert result["style_code"] == "STYLE_0001"
    final_package = Path(result["package_dir"])
    assert final_package == tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "source-job"
    assert validate_package(final_package)["ok"] is True
    assert (final_package / "delivery_report.json").exists()
    assert (final_package / "delivery_report.html").exists()

    style_dir = tmp_path / "style_codes" / "STYLE_0001"
    for name in [
        "style.json",
        "ui_preview.png",
        "annotation.json",
        "manifest.json",
        "delivery_report.json",
        "delivery_report.html",
    ]:
        assert (style_dir / name).exists()

    style = json.loads((style_dir / "style.json").read_text(encoding="utf-8"))
    assert style["style_code"] == "STYLE_0001"
    assert style["source_job_id"] == "source-job"


def test_master_style_artifacts_do_not_overwrite_existing_style_code(tmp_path: Path) -> None:
    package = tmp_path / "package"
    copy_demo_package(package, job_id="job-001", asset_id="asset-001")
    style = {"style_code": "STYLE_0001", "style_name": "Dark Gold Dragon"}
    style_root = tmp_path / "style_codes"

    save_master_style_artifacts(style=style, package_dir=package, style_root=style_root)

    with pytest.raises(RuntimeError, match="already exists"):
        save_master_style_artifacts(style=style, package_dir=package, style_root=style_root)


def test_style_inheritance_prompt_supports_full_screen_set(tmp_path: Path) -> None:
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

    for screen_type in ["role_ui", "bag_ui", "shop_ui", "activity_ui"]:
        prompt = build_reference_guided_prompt(
            style=style,
            screen_type=screen_type,
            reference_image_path=None,
            user_prompt="inherit master style",
        )
        assert "STYLE_0001" in prompt
        assert screen_type in prompt
        assert "dark gold dragon master style" in prompt
        assert "gold carved borders" in prompt
        assert "inherit master style" in prompt
