from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.analyze_production_package import analyze_package


def write_png(path: Path, *, transparent: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    if transparent:
        image.putpixel((0, 0), (255, 0, 0, 0))
    image.save(path)


def write_review_package(tmp_path: Path, *, include_optional: bool = True) -> Path:
    package = tmp_path / "996-ready" / "STYLE_TEST" / "bag_ui" / "job-review"
    (package / "components").mkdir(parents=True)
    write_png(package / "ui_preview.png", transparent=False)
    write_png(package / "components" / "primary_action_button.png", transparent=False)
    write_png(package / "components" / "inventory_panel.png", transparent=True)
    write_png(package / "components" / "floating_text.png", transparent=True)
    write_png(package / "components" / "screen_background.png", transparent=False)
    write_png(package / "components" / "fire_effect.png", transparent=True)

    manifest = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "template": "bag_ui",
        "generation_job_id": "job-review",
        "ui_preview": "ui_preview.png",
        "components": [
            {
                "component_id": "primary_action_button",
                "component_type": "button",
                "file": "components/primary_action_button.png",
            },
            {
                "component_id": "inventory_panel",
                "component_type": "inventory_panel",
                "file": "components/inventory_panel.png",
            },
            {
                "component_id": "floating_text",
                "component_type": "text",
                "file": "components/floating_text.png",
            },
            {
                "component_id": "screen_background",
                "component_type": "background",
                "file": "components/screen_background.png",
            },
            {
                "component_id": "fire_effect",
                "component_type": "effect",
                "file": "components/fire_effect.png",
            },
        ],
    }
    annotation = {
        "schema_version": "1.0",
        "template": "bag_ui",
        "components": manifest["components"],
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "annotation.json").write_text(json.dumps(annotation), encoding="utf-8")

    if include_optional:
        candidate_manifest = {
            "candidates": [
                {
                    "candidate_id": "currency_icon_candidate",
                    "candidate_type": "currency_icon",
                    "image_path": "components/primary_action_button.png",
                }
            ]
        }
        quality = {"total_components": 5}
        delivery = {"screen_type": "bag_ui"}
        (package / "candidate_manifest.json").write_text(json.dumps(candidate_manifest), encoding="utf-8")
        (package / "component_quality_report.json").write_text(json.dumps(quality), encoding="utf-8")
        (package / "delivery_report.json").write_text(json.dumps(delivery), encoding="utf-8")

    return package


def test_analyze_package_writes_review_outputs(tmp_path: Path) -> None:
    package = write_review_package(tmp_path)

    result = analyze_package(package)

    assert result["production_review_path"] == str(package / "production_review.json")
    assert (package / "component_review_analysis.json").exists()
    assert (package / "production_review.json").exists()
    assert (package / "manual_acceptance.json").exists()
    assert (package / "production_review.html").exists()


def test_analyze_package_classifies_levels_and_production_categories(tmp_path: Path) -> None:
    package = write_review_package(tmp_path)

    analyze_package(package)

    review = json.loads((package / "production_review.json").read_text(encoding="utf-8"))
    analysis = json.loads((package / "component_review_analysis.json").read_text(encoding="utf-8"))
    by_id = {item["component_id"]: item for item in analysis["components"]}

    assert by_id["primary_action_button"]["level"] == "A"
    assert by_id["inventory_panel"]["level"] == "B"
    assert by_id["floating_text"]["level"] == "C"
    assert by_id["screen_background"]["production_category"] == "Screen"
    assert by_id["inventory_panel"]["production_category"] == "Panel"
    assert by_id["primary_action_button"]["production_category"] == "Atomic"
    assert by_id["fire_effect"]["production_category"] == "Effect"
    assert by_id["floating_text"]["production_category"] == "Ignore"
    assert review["level_a_count"] == 2
    assert review["level_b_count"] == 1
    assert review["level_c_count"] == 3
    assert review["screen_count"] == 1
    assert review["panel_count"] == 1
    assert review["atomic_count"] == 2
    assert review["effect_count"] == 1
    assert review["ignore_count"] == 1


def test_analyze_package_marks_opaque_level_a_png_as_blocker(tmp_path: Path) -> None:
    package = write_review_package(tmp_path)

    analyze_package(package)

    review = json.loads((package / "production_review.json").read_text(encoding="utf-8"))
    analysis = json.loads((package / "component_review_analysis.json").read_text(encoding="utf-8"))
    button = next(item for item in analysis["components"] if item["component_id"] == "primary_action_button")

    assert button["transparent_check"]["file_exists"] is True
    assert button["transparent_check"]["is_png"] is True
    assert button["transparent_check"]["has_alpha_channel"] is True
    assert button["transparent_check"]["is_fully_opaque"] is True
    assert button["transparent_check"]["required_transparency"] is True
    assert any("fully opaque" in blocker for blocker in button["blockers"])
    assert review["production_ready"] is False
    assert review["transparent_issues"] >= 1
    assert review["blockers"]


def test_analyze_package_tolerates_missing_optional_json(tmp_path: Path) -> None:
    package = write_review_package(tmp_path, include_optional=False)

    analyze_package(package)

    review = json.loads((package / "production_review.json").read_text(encoding="utf-8"))
    assert review["components_count"] == 5
    assert review["candidates_count"] == 0
    assert review["warnings"]


def test_analyze_package_writes_pending_manual_acceptance(tmp_path: Path) -> None:
    package = write_review_package(tmp_path)

    analyze_package(package)

    acceptance = json.loads((package / "manual_acceptance.json").read_text(encoding="utf-8"))
    assert acceptance["review_status"] == "pending"
    assert acceptance["reviewer"] == ""
    assert acceptance["remarks"] == ""
    assert acceptance["accepted_at"] is None
    assert acceptance["accepted_by"] == ""
    assert {item["component_id"] for item in acceptance["components"]} >= {
        "primary_action_button",
        "inventory_panel",
    }
