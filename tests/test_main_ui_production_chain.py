from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.main_ui_production_chain import create_main_ui_package
from scripts.main_ui_production_chain import create_ui_package
from scripts.main_ui_production_chain import export_confirmed_components
from scripts.main_ui_production_chain import update_candidate_confirmation
from scripts import main_ui_production_chain as chain


def write_source(path: Path, *, mode: str = "RGB") -> None:
    image = Image.new(mode, (640, 360), (24, 32, 48, 255) if mode == "RGBA" else (24, 32, 48))
    image.save(path)


def write_checkerboard_task_panel(path: Path, *, size: tuple[int, int] = (286, 330)) -> None:
    image = Image.new("RGBA", size, (232, 232, 232, 255))
    pixels = image.load()
    for y in range(size[1]):
        for x in range(size[0]):
            shade = 226 if ((x // 12) + (y // 12)) % 2 == 0 else 248
            pixels[x, y] = (shade, shade, shade, 255)
    for y in range(32, size[1] - 32):
        for x in range(24, size[0] - 24):
            pixels[x, y] = (46, 34, 22, 255)
    image.save(path, "PNG")


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


def test_ui_package_uses_unique_job_dirs_for_rapid_generations(tmp_path: Path) -> None:
    source = tmp_path / "main.jpg"
    write_source(source)

    first = create_ui_package(tmp_path / "uploads", source_image=source)
    second = create_ui_package(tmp_path / "uploads", source_image=source)

    assert first["package_dir"] != second["package_dir"]


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


def test_main_task_panel_transparency_detection_flags_fully_opaque_rgba(tmp_path: Path) -> None:
    image_path = tmp_path / "opaque.png"
    Image.new("RGBA", (286, 330), (210, 210, 210, 255)).save(image_path, "PNG")

    result = chain.inspect_main_task_panel_transparency(image_path)

    assert result["is_png"] is True
    assert result["alpha_channel_present"] is True
    assert result["alpha_min"] == 255
    assert result["alpha_max"] == 255
    assert result["alpha_all_255"] is True
    assert result["has_real_transparency"] is False
    assert result["transparent_guaranteed"] is False


def test_main_task_panel_transparency_detection_accepts_real_alpha(tmp_path: Path) -> None:
    image_path = tmp_path / "transparent.png"
    image = Image.new("RGBA", (286, 330), (50, 42, 32, 255))
    image.putpixel((0, 0), (0, 0, 0, 0))
    image.save(image_path, "PNG")

    result = chain.inspect_main_task_panel_transparency(image_path)

    assert result["alpha_channel_present"] is True
    assert result["alpha_min"] == 0
    assert result["has_real_transparency"] is True
    assert result["transparent_guaranteed"] is True


def test_main_task_panel_transparency_postprocess_removes_checkerboard_background(tmp_path: Path) -> None:
    image_path = tmp_path / "candidate.png"
    write_checkerboard_task_panel(image_path)

    result = chain.ensure_main_task_panel_candidate_transparency(
        image_path,
        raw_image_path="raw/main_task_panel_candidate_1_raw.png",
        processed_image_path="candidates/main_task_panel_candidate_1.png",
    )

    assert result["raw_image_path"] == "raw/main_task_panel_candidate_1_raw.png"
    assert result["processed_image_path"] == "candidates/main_task_panel_candidate_1.png"
    assert result["transparency_postprocess_applied"] is True
    assert result["transparency_postprocess_status"] == "applied"
    assert result["has_real_transparency"] is True
    assert result["transparent_guaranteed"] is True
    assert result["raw_alpha_min"] == 255
    assert result["alpha_min"] == 0
    with Image.open(image_path) as image:
        assert image.getchannel("A").getextrema()[0] == 0
        assert image.getpixel((143, 165))[3] == 255


def test_main_task_panel_module_loop_generates_selects_previews_and_accepts(tmp_path: Path) -> None:
    result = chain.create_main_task_panel_package(tmp_path / "uploads", job_id="job-main-task-panel")
    package = Path(result["package_dir"])

    assert result["module_id"] == "main_task_panel"
    assert result["requested_generation_mode"] == "mock"
    assert result["generation_mode"] == "mock"
    assert result["fallback_used"] is False
    assert result["fallback_reason"] == ""
    assert result["production_ready"] is False
    assert result["visual_quality_status"] == "not_started"
    assert result["usage_note"] == "Engineering loop validation only; not a production-ready AI visual asset."
    assert len(result["candidates"]) == 3
    assert result["selected_candidate_id"] == ""
    assert result["accepted"] is False

    for candidate in result["candidates"]:
        assert candidate["module_id"] == "main_task_panel"
        assert candidate["generation_mode"] == "mock"
        assert candidate["production_ready"] is False
        assert candidate["visual_quality_status"] == "not_started"
        assert candidate["width"] == 286
        assert candidate["height"] == 330
        assert candidate["target_x"] == 24
        assert candidate["target_y"] == 40
        assert candidate["canvas_width"] == 1728
        assert candidate["canvas_height"] == 972
        assert "生成一个 996 传奇手游横屏主界面左上任务追踪 HUD 模块皮肤" in candidate["prompt"]
        assert candidate["image_path"].startswith("candidates/")
        assert (package / candidate["image_path"]).exists()

    selected = chain.select_main_task_panel_candidate(package, "main_task_panel_candidate_2")
    assert selected["selected_candidate_id"] == "main_task_panel_candidate_2"

    preview = chain.preview_main_task_panel_on_canvas(package)
    preview_path = package / preview["canvas_preview_path"]
    assert preview["canvas_width"] == 1728
    assert preview["canvas_height"] == 972
    assert preview["target_rect"] == {"x": 24, "y": 40, "width": 286, "height": 330}
    assert preview_path.exists()
    with Image.open(preview_path) as image:
        assert image.size == (1728, 972)

    accepted = chain.accept_main_task_panel_candidate(package)
    component_path = package / "components" / "main_task_panel.png"
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    component_record = json.loads((package / "component_record.json").read_text(encoding="utf-8"))

    assert accepted["accepted"] is True
    assert accepted["component_file"] == "components/main_task_panel.png"
    assert accepted["export_dir"].endswith("components")
    assert component_path.exists()
    with Image.open(component_path) as image:
        assert image.size == (286, 330)
        assert image.mode == "RGBA"
    assert manifest["components"][0]["module_id"] == "main_task_panel"
    assert manifest["components"][0]["file"] == "components/main_task_panel.png"
    assert manifest["components"][0]["bounds"] == {"x": 24, "y": 40, "width": 286, "height": 330}
    assert manifest["generation_mode"] == "mock"
    assert manifest["production_ready"] is False
    assert manifest["visual_quality_status"] == "not_started"
    assert component_record["module_id"] == "main_task_panel"
    assert component_record["selected_candidate_id"] == "main_task_panel_candidate_2"
    assert component_record["generation_mode"] == "mock"
    assert component_record["production_ready"] is False
    assert component_record["usage_note"] == "Engineering loop validation only; not a production-ready AI visual asset."


def test_main_task_panel_ai_mode_uses_injected_generator(tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_ai_generator(target: Path, index: int, context: dict[str, object]) -> dict[str, object]:
        calls.append({"target": target, "index": index, "context": context})
        Image.new("RGBA", (512, 512), (index * 40, 30, 80, 180)).save(target)
        return {"generation_provider": "fake-provider", "generation_job_id": f"job-ai-{index}"}

    result = chain.create_main_task_panel_package(
        tmp_path / "uploads",
        job_id="job-ai-main-task-panel",
        generation_mode="ai",
        ai_candidate_generator=fake_ai_generator,
    )
    package = Path(result["package_dir"])

    assert len(calls) == 3
    assert result["requested_generation_mode"] == "ai"
    assert result["generation_mode"] == "ai"
    assert result["generation_provider"] == "fake-provider"
    assert result["production_ready"] is False
    assert result["visual_quality_status"] == "pending_review"
    assert result["fallback_used"] is False
    assert result["fallback_reason"] == ""
    for candidate in result["candidates"]:
        assert candidate["generation_mode"] == "ai"
        assert candidate["requested_generation_mode"] == "ai"
        assert candidate["generation_provider"] == "fake-provider"
        assert candidate["fallback_used"] is False
        with Image.open(package / candidate["image_path"]) as image:
            assert image.size == (286, 330)
            assert image.mode == "RGBA"


def test_main_task_panel_ai_mode_postprocesses_opaque_checkerboard_candidates(tmp_path: Path) -> None:
    def fake_ai_generator(target: Path, index: int, context: dict[str, object]) -> dict[str, object]:
        write_checkerboard_task_panel(target, size=(512, 512))
        return {"generation_provider": "fake-provider", "generation_job_id": f"job-ai-{index}"}

    result = chain.create_main_task_panel_package(
        tmp_path / "uploads",
        job_id="job-ai-opaque-main-task-panel",
        generation_mode="ai",
        ai_candidate_generator=fake_ai_generator,
    )
    package = Path(result["package_dir"])

    assert result["requested_generation_mode"] == "ai"
    assert result["generation_mode"] == "ai"
    assert len(result["candidates"]) == 3
    for index, candidate in enumerate(result["candidates"], 1):
        assert candidate["raw_image_path"] == f"raw/main_task_panel_candidate_{index}_raw.png"
        assert candidate["processed_image_path"] == f"candidates/main_task_panel_candidate_{index}.png"
        assert candidate["transparency_postprocess_applied"] is True
        assert candidate["transparency_postprocess_status"] == "applied"
        assert candidate["has_real_transparency"] is True
        assert candidate["transparent_guaranteed"] is True
        assert candidate["alpha_min"] == 0
        assert candidate["alpha_max"] == 255
        assert (package / candidate["raw_image_path"]).exists()
        with Image.open(package / candidate["image_path"]) as image:
            assert image.size == (286, 330)
            assert image.mode == "RGBA"
            assert image.getchannel("A").getextrema()[0] == 0

    chain.select_main_task_panel_candidate(package, "main_task_panel_candidate_2")
    preview = chain.preview_main_task_panel_on_canvas(package)
    assert (package / preview["canvas_preview_path"]).exists()
    accepted = chain.accept_main_task_panel_candidate(package)
    component_record = json.loads((package / "component_record.json").read_text(encoding="utf-8"))
    assert accepted["accepted"] is True
    assert component_record["raw_image_path"] == "raw/main_task_panel_candidate_2_raw.png"
    assert component_record["processed_image_path"] == "candidates/main_task_panel_candidate_2.png"
    assert component_record["transparency_postprocess_status"] == "applied"
    assert component_record["has_real_transparency"] is True
    with Image.open(package / "components" / "main_task_panel.png") as image:
        assert image.getchannel("A").getextrema()[0] == 0


def test_main_task_panel_ai_mode_falls_back_to_mock_when_generator_fails(tmp_path: Path) -> None:
    def failing_ai_generator(target: Path, index: int, context: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("provider unavailable")

    result = chain.create_main_task_panel_package(
        tmp_path / "uploads",
        job_id="job-ai-fallback-main-task-panel",
        generation_mode="ai",
        ai_candidate_generator=failing_ai_generator,
    )

    assert result["requested_generation_mode"] == "ai"
    assert result["generation_mode"] == "mock"
    assert result["fallback_used"] is True
    assert "provider unavailable" in result["fallback_reason"]
    assert result["visual_quality_status"] == "not_started"
    assert len(result["candidates"]) == 3
    assert all(candidate["generation_mode"] == "mock" for candidate in result["candidates"])
    assert all(candidate["requested_generation_mode"] == "ai" for candidate in result["candidates"])
    assert all(candidate["fallback_used"] is True for candidate in result["candidates"])
