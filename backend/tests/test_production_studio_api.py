from pathlib import Path
import json
import shutil
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import production_studio
from app import main as main_app
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def write_png(target: Path) -> None:
    fixture = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "996_ready_demo" / "ui_preview.png"
    shutil.copyfile(fixture, target)


def write_package(root: Path, style_code: str, screen_type: str, job_id: str) -> Path:
    package = root / "996-ready" / style_code / screen_type / job_id
    (package / "components").mkdir(parents=True)
    (package / "candidates").mkdir()
    write_png(package / "ui_preview.png")
    write_png(package / "components" / "primary_action_button.png")
    write_png(package / "candidates" / "button_candidate_01.png")
    (package / "preview.html").write_text("<html><body>preview</body></html>", encoding="utf-8")
    (package / "candidate_preview.html").write_text("<html><body>candidate</body></html>", encoding="utf-8")
    (package / "delivery_report.html").write_text("<html><body>delivery</body></html>", encoding="utf-8")
    (package / "component_quality_report.html").write_text("<html><body>quality</body></html>", encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "source_asset_id": f"{job_id}-asset",
        "generation_job_id": job_id,
        "device_type": "mobile_landscape",
        "resolution": {"width": 1536, "height": 864},
        "ui_preview": "ui_preview.png",
        "components_dir": "components",
        "components": [
            {
                "component_id": "primary_action_button",
                "component_type": "button",
                "component_name_zh": "主按钮",
                "resource_group": "main",
                "file": "components/primary_action_button.png",
                "bounds": {"x": 10, "y": 20, "width": 120, "height": 48},
                "transparent": {"required": True, "verified": False, "status": "unverified"},
                "transparent_png_required": True,
                "transparent_png_verified": False,
            }
        ],
    }
    annotation = {
        "schema_version": "1.0",
        "source_asset_id": f"{job_id}-asset",
        "coordinate_space": "ui_preview_pixels",
        "device_type": "mobile_landscape",
        "components": [
            {
                "component_id": "primary_action_button",
                "component_type": "button",
                "component_name_zh": "主按钮",
                "resource_group": "main",
                "bounds": {"x": 10, "y": 20, "width": 120, "height": 48},
                "style": {"font_family": "Arial", "font_size": 16, "font_color": "#FFFFFF"},
                "image": {
                    "file": "components/primary_action_button.png",
                    "format": "png",
                    "color_mode": "RGBA",
                    "alpha": "required",
                    "transparent_background": True,
                },
                "recognition": {"method": "fixture", "confidence": 1.0},
                "transparent": {"required": True, "verified": False, "status": "unverified"},
                "requires_manual_review": True,
                "review_status": "pending",
                "notes": "",
            }
        ],
    }
    candidate = {
        "schema_version": "1.0",
        "package_type": "996-ready",
        "source_asset_id": f"{job_id}-asset",
        "generation_job_id": job_id,
        "candidates": [
            {
                "candidate_id": "button_candidate_01",
                "candidate_type": "button_candidate",
                "bounds": {"x": 10, "y": 20, "width": 120, "height": 48},
                "confidence": 0.9,
                "image_path": "candidates/button_candidate_01.png",
                "review_status": "pending",
            }
        ],
    }
    quality = {
        "schema_version": "1.0",
        "report_type": "component_quality",
        "coordinate_space": "ui_preview_pixels",
        "total_components": 2,
        "category_counts": {
            "button": 1,
            "icon": 0,
            "frame": 0,
            "tab": 0,
            "slot": 0,
            "input": 0,
            "panel": 1,
            "background": 0,
        },
        "category_area": {
            "button": 5760,
            "icon": 0,
            "frame": 0,
            "tab": 0,
            "slot": 0,
            "input": 0,
            "panel": 10000,
            "background": 0,
        },
        "coverage": {
            "total_area": 1327104,
            "covered_area": 15760,
            "uncovered_area": 1311344,
            "covered_ratio": 0.0119,
            "uncovered_ratio": 0.9881,
        },
        "suspected_missing_regions": [],
        "components": [],
    }
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "annotation.json").write_text(json.dumps(annotation), encoding="utf-8")
    (package / "candidate_manifest.json").write_text(json.dumps(candidate), encoding="utf-8")
    (package / "delivery_report.json").write_text(json.dumps({"screen_type": screen_type}), encoding="utf-8")
    (package / "component_quality_report.json").write_text(json.dumps(quality), encoding="utf-8")
    return package


def test_production_studio_new_style_generates_master_then_selected_screens(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    upload_root = tmp_path / "uploads"
    master_call: dict[str, object] = {}
    screen_call: dict[str, object] = {}

    def fake_master(**kwargs):  # type: ignore[no-untyped-def]
        master_call.update(kwargs)
        package = write_package(upload_root, "STYLE_TEST", "main_ui", "job-main")
        style_dir = tmp_path / "styles" / "STYLE_TEST"
        style_dir.parent.mkdir(parents=True)
        shutil.copytree(package, style_dir)
        return {"style_code": "STYLE_TEST", "package_dir": str(package), "style_dir": str(style_dir)}

    def fake_screen(**kwargs):  # type: ignore[no-untyped-def]
        screen_call.update(kwargs)
        package = write_package(upload_root, "STYLE_TEST", kwargs["screen_type"], f"job-{kwargs['screen_type']}")
        return {"package_dir": str(package)}

    monkeypatch.setattr(production_studio, "run_master_style_workflow", fake_master)
    monkeypatch.setattr(production_studio, "generate_screen_with_style", fake_screen)

    response = client.post(
        "/production-studio/generate",
        json={
            "style_source": "new_style",
            "style_name": "Dark Gold",
            "screen_types": ["main_ui", "role_ui"],
            "device_type": "mobile_landscape",
            "asset_mode": "resource_production",
            "layout_template": "classic_legend_mobile",
            "generation_mode": "auto_generate",
            "prompt": "Generate production UI",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["style_code"] == "STYLE_TEST"
    assert [item["screen_type"] for item in body["results"]] == ["main_ui", "role_ui"]
    assert all(item["validator_ok"] for item in body["results"])
    assert body["results"][0]["components_count"] == 1
    assert body["results"][0]["candidates_count"] == 1
    assert body["results"][0]["production_review"]["components_count"] == 1
    assert body["results"][0]["manual_acceptance_status"] == "pending"
    assert body["results"][0]["production_review_url"].endswith("/production_review.json")
    assert body["results"][0]["production_review_html_url"].endswith("/production_review.html")
    assert body["results"][0]["missing_semantic_icons"] is True
    assert body["results"][0]["ui_preview_url"].startswith("/production-studio/files/996-ready/")
    assert body["layout_template"] == "classic_legend_mobile"
    assert body["generation_mode"] == "auto_generate"
    assert body["final_prompt"].startswith("Generate production UI")
    assert "固定布局规则已应用" in body["final_prompt"]
    assert master_call["screen_generation_mode"] == "auto_generate"
    assert "左下摇杆区" in str(master_call["prompt"])
    assert "右下环绕式技能操作区" in str(master_call["prompt"])
    assert "左下摇杆区" in str(screen_call["user_prompt"])

    delivery_report = json.loads((upload_root / "996-ready" / "STYLE_TEST" / "main_ui" / "job-main" / "delivery_report.json").read_text(encoding="utf-8"))
    assert delivery_report["layout_template"] == "classic_legend_mobile"
    assert delivery_report["generation_mode"] == "auto_generate"
    assert delivery_report["reference_image_path"] is None
    assert delivery_report["fixed_layout_rules_applied"] is True
    assert "Generate production UI" in delivery_report["final_prompt"]


def test_production_studio_existing_style_uses_selected_style_code(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    upload_root = tmp_path / "uploads"
    calls: list[str] = []

    def fake_screen(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs["style_code"])
        package = write_package(upload_root, kwargs["style_code"], kwargs["screen_type"], "job-bag")
        return {"package_dir": str(package)}

    monkeypatch.setattr(production_studio, "generate_screen_with_style", fake_screen)

    response = client.post(
        "/production-studio/generate",
        json={
            "style_source": "existing_style",
            "style_code": "STYLE_0003",
            "screen_types": ["bag_ui"],
            "device_type": "mobile_landscape",
            "asset_mode": "resource_production",
            "style_name": "",
            "prompt": "Generate bag UI",
        },
    )

    assert response.status_code == 200
    assert calls == ["STYLE_0003"]
    body = response.json()
    assert body["style_code"] == "STYLE_0003"
    assert body["results"][0]["screen_type"] == "bag_ui"


def test_production_studio_reference_mode_passes_reference_image_and_prompt(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    upload_root = tmp_path / "uploads"
    calls: list[dict[str, object]] = []
    reference_image = tmp_path / "reference.png"
    write_png(reference_image)

    def fake_master(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(kwargs)
        package = write_package(upload_root, "STYLE_REF", "main_ui", "job-main")
        return {"style_code": "STYLE_REF", "package_dir": str(package)}

    monkeypatch.setattr(production_studio, "run_master_style_workflow", fake_master)

    response = client.post(
        "/production-studio/generate",
        json={
            "style_source": "new_style",
            "style_name": "Reference Dark Gold",
            "screen_types": ["main_ui"],
            "device_type": "mobile_landscape",
            "asset_mode": "resource_production",
            "layout_template": "legend_176",
            "generation_mode": "reference_guided",
            "reference_image_path": str(reference_image),
            "prompt": "参考上传的传奇手游界面截图，保留核心操作布局。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["style_code"] == "STYLE_REF"
    assert body["layout_template"] == "legend_176"
    assert body["generation_mode"] == "reference_guided"
    assert body["reference_image_path"] == str(reference_image)
    assert "参考上传的传奇手游界面截图" in body["final_prompt"]
    assert calls[0]["screen_generation_mode"] == "reference_guided"
    assert calls[0]["reference_image"] == str(reference_image)

    delivery_report = json.loads((upload_root / "996-ready" / "STYLE_REF" / "main_ui" / "job-main" / "delivery_report.json").read_text(encoding="utf-8"))
    assert delivery_report["layout_template"] == "legend_176"
    assert delivery_report["generation_mode"] == "reference_guided"
    assert delivery_report["reference_image_path"] == str(reference_image)


def test_opencv_slice_endpoint_returns_layer_workspace_outputs(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    upload_root = tmp_path / "uploads"
    package = write_package(upload_root, "STYLE_OPENCV", "main_ui", "job-opencv")

    def fake_slicer(source_image: Path, output_dir: Path) -> dict:  # type: ignore[no-untyped-def]
        output_dir.mkdir(parents=True)
        slices_dir = output_dir / "slices"
        slices_dir.mkdir()
        shutil.copyfile(source_image, slices_dir / "component_001.png")
        (output_dir / "layer_manifest.json").write_text(
            json.dumps(
                {
                    "canvas": {"width": 1536, "height": 864},
                    "layers": [
                        {
                            "id": "component_001",
                            "type": "button",
                            "bbox": {"x": 10, "y": 20, "width": 120, "height": 48},
                            "outline_points": [[10, 20], [130, 20], [130, 68], [10, 68]],
                            "slice_file": "slices/component_001.png",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        shutil.copyfile(source_image, output_dir / "candidate_preview.png")
        return {"layer_count": 1}

    monkeypatch.setattr(main_app, "run_opencv_ui_slicer", fake_slicer)

    response = client.post(f"/production-studio/ui-production/opencv-slice?package_dir={package}")

    assert response.status_code == 200
    body = response.json()
    assert body["opencv_layer_count"] == 1
    assert body["opencv_candidate_preview_url"].endswith("/output/candidate_preview.png")
    assert body["opencv_layer_manifest_url"].endswith("/output/layer_manifest.json")
    assert (package / "output" / "slices").is_dir()


def test_production_studio_lists_style_codes() -> None:
    items = production_studio.list_style_codes()
    assert any(item.style_code == "STYLE_0003" for item in items)
