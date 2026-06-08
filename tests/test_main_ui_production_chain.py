from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.main_ui_production_chain import create_main_ui_package
from scripts.main_ui_production_chain import export_confirmed_components
from scripts.main_ui_production_chain import update_candidate_confirmation


def write_source(path: Path, *, mode: str = "RGB") -> None:
    image = Image.new(mode, (640, 360), (24, 32, 48, 255) if mode == "RGBA" else (24, 32, 48))
    image.save(path)


def test_main_ui_package_generates_required_files(tmp_path: Path) -> None:
    source = tmp_path / "main.jpg"
    write_source(source)

    result = create_main_ui_package(tmp_path / "uploads", source_image=source, job_id="job-main-ui")
    package = Path(result["package_dir"])

    assert (package / "main_ui.jpg").exists()
    assert (package / "ui_preview.png").exists()
    assert (package / "candidate_preview.jpg").exists()
    assert (package / "candidate_options" / "candidate_1.jpg").exists()
    assert (package / "candidate_options" / "candidate_2.jpg").exists()
    assert (package / "candidate_options" / "candidate_3.jpg").exists()
    assert (package / "candidate_manifest.json").exists()
    assert (package / "manual_acceptance.json").exists()
    assert (package / "production_review.json").exists()
    assert (package / "confirmed_components").is_dir()


def test_main_ui_candidates_include_levels_and_categories(tmp_path: Path) -> None:
    source = tmp_path / "main.jpg"
    write_source(source)

    result = create_main_ui_package(tmp_path / "uploads", source_image=source, job_id="job-candidates")
    manifest = json.loads((Path(result["package_dir"]) / "candidate_manifest.json").read_text(encoding="utf-8"))
    by_id = {item["component_id"]: item for item in manifest["candidates"]}

    assert by_id["skill_01"]["level"] == "A"
    assert by_id["skill_01"]["production_category"] == "Atomic"
    assert by_id["skill_01"]["layout_zone"] == "right_skill"
    assert by_id["skill_01"]["shape_type"] == "circle"
    assert by_id["skill_01"]["bbox"]
    assert len(by_id["skill_01"]["outline_points"]) > 4
    assert by_id["bottom_hud"]["level"] == "B"
    assert by_id["bottom_hud"]["production_category"] == "Panel"
    assert len(by_id["bottom_hud"]["outline_points"]) > 4
    assert by_id["screen_main_ui"]["production_category"] == "Screen"
    assert by_id["dynamic_text"]["level"] == "C"
    assert by_id["dynamic_text"]["production_category"] == "Ignore"
    assert manifest["fixed_layout_zones"] == [
        "bottom_left_joystick",
        "right_skill",
        "right_top_map",
        "top_info",
        "bottom_status",
        "chat",
        "right_system_entry",
        "left_task",
        "left_status",
    ]


def test_confirmed_components_follow_png_and_jpg_rules(tmp_path: Path) -> None:
    source = tmp_path / "main.jpg"
    write_source(source)

    result = create_main_ui_package(tmp_path / "uploads", source_image=source, job_id="job-export")
    package = Path(result["package_dir"])
    manifest = json.loads((package / "candidate_manifest.json").read_text(encoding="utf-8"))
    by_id = {item["component_id"]: item for item in manifest["candidates"]}

    assert by_id["skill_01"]["image_path"].endswith(".png")
    assert by_id["skill_01"]["transparent_warning"]
    assert (package / by_id["skill_01"]["image_path"]).exists()
    assert by_id["bottom_hud"]["image_path"].endswith(".jpg")
    assert (package / by_id["bottom_hud"]["image_path"]).exists()
    assert by_id["dynamic_text"]["image_path"] == ""


def test_manual_confirmation_controls_export(tmp_path: Path) -> None:
    source = tmp_path / "main.jpg"
    write_source(source)

    result = create_main_ui_package(tmp_path / "uploads", source_image=source, job_id="job-confirm", auto_export=False)
    package = Path(result["package_dir"])
    update_candidate_confirmation(package, "skill_01", False)
    export_confirmed_components(package)

    manifest = json.loads((package / "candidate_manifest.json").read_text(encoding="utf-8"))
    by_id = {item["component_id"]: item for item in manifest["candidates"]}

    assert by_id["skill_01"]["confirmed"] is False
    assert by_id["skill_01"]["image_path"] == ""
    assert by_id["skill_02"]["confirmed"] is True
    assert by_id["skill_02"]["image_path"].endswith(".png")
    samples = json.loads((package / "training_samples" / "main_ui" / "candidate_samples.json").read_text(encoding="utf-8"))
    sample_by_id = {item["candidate_id"]: item for item in samples["samples"]}
    assert sample_by_id["skill_01"]["user_confirmed"] is False
    assert sample_by_id["skill_01"]["accepted"] is False
    assert sample_by_id["skill_01"]["confirmation_status"] == "rejected"
    assert sample_by_id["skill_01"]["rejected_reason"] == "not_confirmed_for_slicing"
    assert sample_by_id["skill_01"]["bbox_delta"] == {"x": 0, "y": 0, "width": 0, "height": 0}
    assert sample_by_id["skill_01"]["type_changed"] is False
    assert sample_by_id["skill_02"]["confirmation_status"] == "confirmed"
    assert sample_by_id["skill_02"]["accepted"] is True
    assert sample_by_id["skill_02"]["rejected_reason"] == ""
    assert sample_by_id["skill_02"]["layout_zone"] == "right_skill"
    acceptance = json.loads((package / "manual_acceptance.json").read_text(encoding="utf-8"))
    acceptance_by_id = {item["component_id"]: item for item in acceptance["components"]}
    assert acceptance_by_id["skill_01"]["confirmed"] is False
    assert acceptance_by_id["skill_01"]["output_file"] == ""
    assert acceptance_by_id["skill_02"]["confirmed"] is True
    assert acceptance_by_id["skill_02"]["output_file"].endswith(".png")
