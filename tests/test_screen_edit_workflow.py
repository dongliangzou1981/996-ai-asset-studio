from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.edit_screen_with_style import (
    build_style_edit_prompt,
    edit_target_package_dir,
    finalize_edit_package,
    load_source_package_context,
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


def test_edit_prompt_keeps_style_layout_and_edit_request(tmp_path: Path) -> None:
    source_package = tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "old-job"
    copy_demo_package(source_package, job_id="old-job", asset_id="asset-old")
    (source_package / "candidate_manifest.json").write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "candidate_id": "button_candidate_01",
                        "candidate_type": "button_candidate",
                        "bounds": {"x": 1, "y": 2, "width": 3, "height": 4},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
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
    context = load_source_package_context(source_package)

    prompt = build_style_edit_prompt(
        style=style,
        screen_type="main_ui",
        source_package=source_package,
        context=context,
        edit_request="把右侧商城按钮改大一点，底部技能栏更华丽",
        source_preview_path=source_package / "ui_preview.png",
    )

    assert "STYLE_0001" in prompt
    assert "Dark Gold Dragon" in prompt
    assert "把右侧商城按钮改大一点，底部技能栏更华丽" in prompt
    assert "Keep the original layout structure" in prompt
    assert "preserve the STYLE_CODE visual style" in prompt
    assert "old-job" in prompt
    assert "button_candidate" in prompt
    assert "gold carved borders" in prompt


def test_edit_target_package_dir_uses_new_generation_job_id(tmp_path: Path) -> None:
    target = edit_target_package_dir(
        upload_root=tmp_path / "uploads",
        style_code="STYLE_0001",
        screen_type="main_ui",
        new_generation_job_id="new-job",
    )

    assert target == tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "new-job"


def test_finalize_edit_package_writes_metadata_without_overwriting_old_package(tmp_path: Path) -> None:
    old_package = tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "old-job"
    generated_package = tmp_path / "generated" / "new-job"
    new_package = tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "new-job"
    copy_demo_package(old_package, job_id="old-job", asset_id="asset-old")
    copy_demo_package(generated_package, job_id="new-job", asset_id="asset-new")
    old_manifest_before = (old_package / "manifest.json").read_text(encoding="utf-8")

    result = finalize_edit_package(
        generated_package=generated_package,
        target_package=new_package,
        style_code="STYLE_0001",
        screen_type="main_ui",
        new_generation_job_id="new-job",
        parent_generation_job_id="old-job",
        edit_request="聊天框颜色更深",
        edit_mode="prompt_fallback",
        source_preview_path=old_package / "ui_preview.png",
        prompt="edit prompt with STYLE_0001",
    )

    assert Path(result["package_dir"]) == new_package
    assert (old_package / "manifest.json").read_text(encoding="utf-8") == old_manifest_before
    assert validate_package(new_package)["ok"] is True
    assert (new_package / "delivery_report.json").exists()
    assert (new_package / "delivery_report.html").exists()

    report = json.loads((new_package / "delivery_report.json").read_text(encoding="utf-8"))
    assert report["edit_metadata"] == {
        "parent_generation_job_id": "old-job",
        "edit_request": "聊天框颜色更深",
        "edit_mode": "prompt_fallback",
        "style_code": "STYLE_0001",
        "device_type": "mobile_landscape",
        "source_preview_path": str(old_package / "ui_preview.png"),
    }
    assert report["screen_generation_mode"] == "screen_edit"
    assert report["generation_job_id"] == "new-job"
