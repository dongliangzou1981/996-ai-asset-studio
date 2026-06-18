from __future__ import annotations

import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app
import app.main as main_module
from scripts.main_ui_production_chain import create_main_ui_package as real_create_main_ui_package


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def write_source(path: Path) -> None:
    Image.new("RGB", (640, 360), (24, 32, 48)).save(path)


def test_main_ui_run_endpoint_generates_package(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.jpg"
    write_source(source)

    def fake_create_main_ui_package(**kwargs):  # type: ignore[no-untyped-def]
        return real_create_main_ui_package(kwargs["upload_root"], source_image=source, job_id="job-main-ui-api")

    monkeypatch.setattr(main_module, "create_main_ui_package", fake_create_main_ui_package)
    client = make_client(tmp_path)

    response = client.post("/production-studio/main-ui-production/run")

    assert response.status_code == 200
    body = response.json()
    assert body["package_dir"].endswith("job-main-ui-api")
    assert body["main_ui_url"].endswith("/main_ui.jpg")
    assert body["candidate_preview_url"].endswith("/candidate_preview.jpg")
    assert body["candidates"]
    assert len(body["candidate_options"]) == 3
    assert body["candidate_options"][0]["selected"] is True
    assert body["project_context"]["project_name"] == "996 UI Asset Studio"
    package_files = {item["file"]: item for item in body["package_files"]}
    assert package_files["main_ui.jpg"]["exists"] is True
    assert package_files["candidate_preview.jpg"]["exists"] is True
    assert package_files["manifest.json"]["exists"] is True
    assert package_files["manual_acceptance.json"]["exists"] is True
    assert package_files["confirmed_components/"]["exists"] is True
    assert any(item["file"].endswith(".png") for item in body["confirmed_components"] if item["file"])


def test_main_ui_candidate_update_and_export(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source.jpg"
    write_source(source)

    def fake_create_main_ui_package(**kwargs):  # type: ignore[no-untyped-def]
        return real_create_main_ui_package(kwargs["upload_root"], source_image=source, job_id="job-main-ui-export")

    monkeypatch.setattr(main_module, "create_main_ui_package", fake_create_main_ui_package)
    client = make_client(tmp_path)
    package_dir = client.post("/production-studio/main-ui-production/run").json()["package_dir"]

    update = client.put(
        "/production-studio/main-ui-production/candidate",
        params={"package_dir": package_dir, "candidate_id": "skill_01"},
        json={"confirmed": False},
    )
    assert update.status_code == 200
    assert update.json()["confirmed"] is False

    export = client.post("/production-studio/main-ui-production/export", params={"package_dir": package_dir})

    assert export.status_code == 200
    body = export.json()
    by_id = {item["component_id"]: item for item in body["confirmed_components"]}
    assert by_id["skill_01"]["confirmed"] is False
    assert by_id["skill_01"]["file"] == ""
    saved = json.loads((Path(package_dir) / "candidate_manifest.json").read_text(encoding="utf-8"))
    assert next(item for item in saved["candidates"] if item["component_id"] == "skill_01")["image_path"] == ""


def test_main_task_panel_module_api_loop(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    generated = client.post("/production-studio/hud-modules/main-task-panel/generate")

    assert generated.status_code == 200
    body = generated.json()
    assert body["module_id"] == "main_task_panel"
    assert body["requested_generation_mode"] == "mock"
    assert body["generation_mode"] == "mock"
    assert body["fallback_used"] is False
    assert body["fallback_reason"] == ""
    assert body["production_ready"] is False
    assert body["visual_quality_status"] == "not_started"
    assert body["usage_note"] == "Engineering loop validation only; not a production-ready AI visual asset."
    assert body["accepted"] is False
    assert len(body["candidates"]) == 3
    first = body["candidates"][0]
    assert first["candidate_id"] == "main_task_panel_candidate_1"
    assert first["module_id"] == "main_task_panel"
    assert first["generation_mode"] == "mock"
    assert first["production_ready"] is False
    assert first["width"] == 286
    assert first["height"] == 330
    assert first["target_x"] == 24
    assert first["target_y"] == 40
    assert first["canvas_width"] == 1728
    assert first["canvas_height"] == 972
    assert first["image_url"].endswith("/candidates/main_task_panel_candidate_1.png")

    package_dir = body["package_dir"]
    selected = client.post(
        "/production-studio/hud-modules/main-task-panel/select",
        params={"package_dir": package_dir, "candidate_id": "main_task_panel_candidate_2"},
    )
    assert selected.status_code == 200
    assert selected.json()["selected_candidate_id"] == "main_task_panel_candidate_2"

    preview = client.post("/production-studio/hud-modules/main-task-panel/preview", params={"package_dir": package_dir})
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["canvas_preview_url"].endswith("/canvas_preview.png")
    assert preview_body["target_rect"] == {"x": 24, "y": 40, "width": 286, "height": 330}

    accepted = client.post("/production-studio/hud-modules/main-task-panel/accept", params={"package_dir": package_dir})
    assert accepted.status_code == 200
    accepted_body = accepted.json()
    assert accepted_body["accepted"] is True
    assert accepted_body["export_dir"].endswith("components")
    assert accepted_body["component_path"].endswith("components/main_task_panel.png")
    assert accepted_body["component_record_path"] == "component_record.json"
    assert accepted_body["component_record_url"].endswith("/component_record.json")
    assert accepted_body["canvas_preview_path"] == "canvas_preview.png"
    assert accepted_body["component_url"].endswith("/components/main_task_panel.png")
    assert accepted_body["manifest_url"].endswith("/manifest.json")
    manifest = json.loads((Path(package_dir) / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["components"][0]["module_id"] == "main_task_panel"
    assert manifest["components"][0]["bounds"] == {"x": 24, "y": 40, "width": 286, "height": 330}
    assert manifest["generation_mode"] == "mock"
    assert manifest["production_ready"] is False


def test_main_task_panel_api_accepts_ai_generation_mode(tmp_path: Path, monkeypatch) -> None:
    def fake_ai_generator(target: Path, index: int, context: dict) -> dict:  # type: ignore[type-arg]
        Image.new("RGBA", (512, 512), (index * 50, 20, 90, 180)).save(target)
        return {"generation_provider": "fake-provider", "generation_job_id": f"job-ai-{index}"}

    monkeypatch.setattr(main_module, "main_task_panel_ai_candidate_generator", fake_ai_generator)
    client = make_client(tmp_path)

    response = client.post("/production-studio/hud-modules/main-task-panel/generate", json={"generation_mode": "ai"})

    assert response.status_code == 200
    body = response.json()
    assert body["requested_generation_mode"] == "ai"
    assert body["generation_mode"] == "ai"
    assert body["generation_provider"] == "fake-provider"
    assert body["fallback_used"] is False
    assert body["visual_quality_status"] == "pending_review"
    assert len(body["candidates"]) == 3
    assert all(candidate["generation_mode"] == "ai" for candidate in body["candidates"])


def test_main_task_panel_api_falls_back_to_mock_when_ai_generation_fails(tmp_path: Path, monkeypatch) -> None:
    def failing_ai_generator(target: Path, index: int, context: dict) -> dict:  # type: ignore[type-arg]
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main_module, "main_task_panel_ai_candidate_generator", failing_ai_generator)
    client = make_client(tmp_path)

    response = client.post("/production-studio/hud-modules/main-task-panel/generate", json={"generation_mode": "ai"})

    assert response.status_code == 200
    body = response.json()
    assert body["requested_generation_mode"] == "ai"
    assert body["generation_mode"] == "mock"
    assert body["fallback_used"] is True
    assert "provider unavailable" in body["fallback_reason"]
    assert len(body["candidates"]) == 3
    assert all(candidate["generation_mode"] == "mock" for candidate in body["candidates"])


def create_ofox_provider(client: TestClient) -> None:
    response = client.post(
        "/ai_providers",
        json={
            "name": "Ofox UI Default",
            "type": "ofox",
            "enabled": True,
            "config_json": json.dumps(
                {
                    "api_key_env": "OFOX_API_KEY",
                    "base_url": "https://api.ofox.ai/v1",
                    "model": "gpt-image-2",
                }
            ),
        },
    )
    assert response.status_code == 201


def test_main_task_panel_ai_status_reports_missing_key_without_leaking_env_value(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OFOX_API_KEY", raising=False)
    client = make_client(tmp_path)
    create_ofox_provider(client)

    response = client.get("/production-studio/main-task-panel/ai-status")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "default_provider": "Ofox UI Default",
        "provider_type": "ofox",
        "required_env": "OFOX_API_KEY",
        "api_key_configured": False,
        "ai_generation_available": False,
        "mock_generation_available": True,
        "message": "OFOX_API_KEY is not configured. AI generation is unavailable; mock generation is still available.",
    }


def test_main_task_panel_ai_status_reports_configured_key_without_leaking_env_value(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OFOX_API_KEY", "configured-env-value-for-test")
    client = make_client(tmp_path)
    create_ofox_provider(client)

    response = client.get("/production-studio/main-task-panel/ai-status")

    assert response.status_code == 200
    body = response.json()
    assert body["default_provider"] == "Ofox UI Default"
    assert body["provider_type"] == "ofox"
    assert body["required_env"] == "OFOX_API_KEY"
    assert body["api_key_configured"] is True
    assert body["ai_generation_available"] is True
    assert body["mock_generation_available"] is True
    assert "configured-env-value-for-test" not in response.text


def test_main_ui_endpoint_rejects_outside_package_path(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    response = client.get("/production-studio/main-ui-production", params={"package_dir": str(outside)})

    assert response.status_code == 400


def test_ui_production_generate_mark_export_and_prompt_samples(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    generated = client.post(
        "/production-studio/ui-production/generate",
        json={
            "screen_type": "main_ui",
            "system_prompt": "system generated prompt",
            "requirement": "main ui layout",
            "style_reference_strength": "60",
            "reference_influence_percent": 60,
            "project_id": "project-1",
            "device_type": "mobile_landscape",
            "layout_template": "classic_legend_mobile",
            "adjustment_note": "manual note",
        },
    )
    assert generated.status_code == 200
    package_dir = generated.json()["package_dir"]
    assert generated.json()["main_ui_url"].endswith("/main_ui.jpg")
    assert generated.json()["reference_influence_percent"] == 60
    assert generated.json()["candidates"] == []
    generated_files = {item["file"]: item for item in generated.json()["package_files"]}
    assert generated_files["main_ui.jpg"]["exists"] is True
    assert generated_files["candidate_preview.jpg"]["exists"] is False
    prompt_samples_path = tmp_path / "training_samples" / "prompts" / "prompt_samples.json"
    prompt_samples = json.loads(prompt_samples_path.read_text(encoding="utf-8"))
    sample = prompt_samples["samples"][0]
    assert sample["system_prompt"] == "system generated prompt"
    assert sample["final_prompt"] == "main ui layout"
    assert sample["project_id"] == "project-1"
    assert sample["interface_type"] == "main_ui"
    assert sample["device_type"] == "mobile_landscape"
    assert sample["layout_template"] == "classic_legend_mobile"
    assert sample["accepted"] is False
    assert sample["manual_adjustment_note"] == "manual note"
    delivery = json.loads((Path(package_dir) / "delivery_report.json").read_text(encoding="utf-8"))
    assert delivery["reference_influence_percent"] == 60
    assert delivery["generation_parameters"]["reference_influence_percent"] == 60

    marked = client.post("/production-studio/ui-production/mark-candidates", params={"package_dir": package_dir})
    assert marked.status_code == 200
    assert marked.json()["candidate_preview_url"].endswith("/candidate_preview.jpg")
    assert marked.json()["candidates"]
    by_candidate = {item["component_id"]: item for item in marked.json()["candidates"]}
    assert by_candidate["skill_01"]["layout_zone"] == "right_skill"
    assert by_candidate["skill_01"]["shape_type"] == "circle"
    assert len(by_candidate["skill_01"]["outline_points"]) > 4
    assert by_candidate["skill_01"]["layer_name"] == "skill_01"
    assert by_candidate["skill_01"]["slice_layer"]["group"] == "right_skill"
    assert by_candidate["bottom_hud"]["shape_type"] == "composite"
    assert len(by_candidate["bottom_hud"]["outline_points"]) > 4
    marked_files = {item["file"]: item for item in marked.json()["package_files"]}
    assert marked_files["candidate_manifest.json"]["exists"] is True

    selected = client.post(
        "/production-studio/ui-production/select-candidate",
        params={"package_dir": package_dir, "candidate_id": "candidate_2"},
    )
    assert selected.status_code == 200
    assert selected.json()["selected_candidate_id"] == "candidate_2"

    updated = client.put(
        "/production-studio/ui-production/candidate",
        params={"package_dir": package_dir, "candidate_id": "skill_01"},
        json={"confirmed": False},
    )
    assert updated.status_code == 200
    assert updated.json()["confirmed"] is False

    exported = client.post("/production-studio/ui-production/export", params={"package_dir": package_dir})
    assert exported.status_code == 200
    by_id = {item["component_id"]: item for item in exported.json()["confirmed_components"]}
    assert by_id["skill_01"]["file"] == ""
    assert any(item["file"].endswith(".jpg") for item in exported.json()["confirmed_components"] if item["file"])
    exported_files = {item["file"]: item for item in exported.json()["package_files"]}
    assert exported_files["confirmed_components/"]["exists"] is True
    assert exported_files["production_review.json"]["exists"] is True
    assert exported_files["training_samples/main_ui/candidate_samples.json"]["exists"] is True
    assert exported.json()["training_samples_url"].endswith("/training_samples/main_ui/candidate_samples.json")
    manifest = json.loads((Path(package_dir) / "manifest.json").read_text(encoding="utf-8"))
    manifest_by_id = {item["component_id"]: item for item in manifest["components"]}
    assert manifest_by_id["bottom_hud"]["slice_layer"]["group"] == "bottom_status"
    samples = json.loads((Path(package_dir) / "training_samples" / "main_ui" / "candidate_samples.json").read_text(encoding="utf-8"))
    sample_by_id = {item["component_id"]: item for item in samples["samples"]}
    assert sample_by_id["skill_01"]["slice_layer"]["name"] == "skill_01"
    prompt_samples = json.loads(prompt_samples_path.read_text(encoding="utf-8"))
    sample = prompt_samples["samples"][0]
    assert sample["marking_result"]["status"] == "exported"
    assert sample["marking_result"]["total_marks"] > 0

    accepted = client.put(
        "/production-studio/manual-acceptance",
        params={"package_dir": package_dir},
        json={"review_status": "accepted", "reviewer": "qa", "remarks": "approved"},
    )
    assert accepted.status_code == 200
    prompt_samples = json.loads(prompt_samples_path.read_text(encoding="utf-8"))
    sample = prompt_samples["samples"][0]
    assert sample["accepted"] is True
    assert sample["quality"] == "high_quality"

    best = client.get(
        "/production-studio/prompt-samples/best",
        params={
            "interface_type": "main_ui",
            "device_type": "mobile_landscape",
            "layout_template": "classic_legend_mobile",
        },
    )
    assert best.status_code == 200
    assert best.json()["found"] is True
    assert best.json()["final_prompt"] == "main ui layout"


def test_ui_production_other_screen_types_are_placeholders(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/production-studio/ui-production/generate",
        json={"screen_type": "bag_ui", "requirement": "bag", "style_reference_strength": "none"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "placeholder"
    assert response.json()["screen_type"] == "bag_ui"


def test_marking_acceptance_test_generates_harness_outputs(tmp_path: Path, monkeypatch) -> None:
    harness_root = tmp_path / "harness_examples"

    monkeypatch.setenv("STUDIO_HARNESS_EXAMPLES_DIR", str(harness_root))
    client = make_client(tmp_path)

    response = client.post(
        "/production-studio/marking-acceptance-test/run",
        json={
            "system_prompt": "fallback system prompt",
            "requirement": "edited prompt for fallback",
            "project_id": "project-marking",
            "device_type": "mobile_landscape",
            "layout_template": "classic_legend_mobile",
            "adjustment_note": "fallback adjustment",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["project_code"] == "MARKING_TEST"
    assert body["project"]["name"] == "标记验收测试"
    assert body["project"]["description"] == "MARKING_TEST"
    assert body["candidate_id"] == "candidate_1"
    assert body["total_marks"] > 0
    assert body["slice_success"] > 0
    assert body["by_type"]["skill"] > 0
    assert body["production"]["selected_candidate_id"] == "candidate_1"
    assert body["production"]["candidate_options"][0]["selected"] is True
    delivery = json.loads((Path(body["production"]["package_dir"]) / "delivery_report.json").read_text(encoding="utf-8"))
    assert delivery["requirement"] == "edited prompt for fallback"
    assert "sprint20i-fallback" in delivery["source_note"]["source_image"]

    output_dir = harness_root / "main_ui" / "marking_test"
    assert (output_dir / "original.jpg").exists()
    assert (output_dir / "candidate_preview.png").exists()
    assert (output_dir / "marking.json").exists()
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "manual_acceptance.json").exists()
    assert (output_dir / "marking_acceptance_report.json").exists()
    assert any((output_dir / "slices").iterdir())

    report = json.loads((output_dir / "marking_acceptance_report.json").read_text(encoding="utf-8"))
    assert report["project_code"] == "MARKING_TEST"
    assert report["total_marks"] == body["total_marks"]
    assert report["background_count"] == report["by_type"]["background"]
    assert report["panel_count"] == report["by_type"]["panel"]
    assert report["button_count"] == report["by_type"]["button"]
    assert report["icon_count"] == report["by_type"]["icon"]
    assert report["skill_count"] == report["by_type"]["skill"]
    assert report["by_type"]["background"] >= 1
    assert report["by_type"]["button"] >= 1
    assert report["by_type"]["skill"] >= 1
    assert report["missing_required"] == []
    assert report["key_component_checks"]["missing"] == []
    assert report["key_component_checks"]["required"] == ["top_bar", "mini_map", "skill_area", "chat_area", "joystick_area"]
    assert report["bbox_health"]["checked"] == report["total_marks"]
    assert report["bbox_health"]["invalid_size_count"] == 0
    assert report["bbox_health"]["out_of_bounds_count"] == 0
    assert "abnormal_overlap_count" in report["bbox_health"]
    assert report["slice_health"]["checked"] >= report["slice_success"]
    assert report["slice_health"]["file_missing_count"] == 0
    assert "png_without_alpha_count" in report["slice_health"]
    assert report["marking_json_path"].endswith("marking.json")
    prompt_samples = json.loads((tmp_path / "training_samples" / "prompts" / "prompt_samples.json").read_text(encoding="utf-8"))
    sample = prompt_samples["samples"][0]
    assert sample["system_prompt"] == "fallback system prompt"
    assert sample["final_prompt"] == "edited prompt for fallback"
    assert sample["marking_result"]["project_code"] == "MARKING_TEST"


def test_marking_acceptance_test_prefers_uploaded_reference(tmp_path: Path, monkeypatch) -> None:
    harness_root = tmp_path / "harness_examples"
    upload_root = tmp_path / "uploads"
    reference = upload_root / "references" / "uploaded-main-ui.jpg"
    reference.parent.mkdir(parents=True)
    write_source(reference)

    monkeypatch.setenv("STUDIO_HARNESS_EXAMPLES_DIR", str(harness_root))
    client = TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=upload_root))

    response = client.post(
        "/production-studio/marking-acceptance-test/run",
        json={
            "reference_image": str(reference),
            "requirement": "uploaded reference prompt",
            "adjustment_note": "uploaded reference adjustment",
        },
    )

    assert response.status_code == 200
    body = response.json()
    delivery = json.loads((Path(body["production"]["package_dir"]) / "delivery_report.json").read_text(encoding="utf-8"))
    assert delivery["requirement"] == "uploaded reference prompt"
    assert delivery["source_note"]["source_image"] == str(reference)
