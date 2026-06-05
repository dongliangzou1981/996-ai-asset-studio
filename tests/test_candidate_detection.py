from __future__ import annotations

import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import create_app
from scripts.validate_996_export import validate_package


EXPECTED_CANDIDATE_TYPES = {
    "button_candidate",
    "icon_candidate",
    "input_candidate",
    "frame_candidate",
    "tab_candidate",
    "slot_candidate",
}


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def create_candidate_source(path: Path) -> None:
    image = Image.new("RGBA", (1024, 1024), color=(28, 34, 42, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((635, 836, 858, 917), fill=(128, 74, 36, 255), outline=(238, 190, 88, 255), width=4)
    draw.rectangle((840, 664, 942, 766), fill=(46, 67, 90, 255), outline=(237, 203, 105, 255), width=4)
    draw.rectangle((246, 756, 655, 818), fill=(15, 23, 34, 255), outline=(172, 132, 76, 255), width=3)
    draw.rectangle((205, 205, 819, 758), fill=(39, 45, 54, 255), outline=(192, 146, 82, 255), width=5)
    draw.rectangle((287, 123, 471, 185), fill=(103, 59, 37, 255), outline=(230, 184, 92, 255), width=4)
    draw.rectangle((123, 635, 195, 707), fill=(33, 41, 51, 255), outline=(212, 170, 86, 255), width=4)
    image.save(path, format="PNG")


def test_component_processing_outputs_candidate_manifest_and_preview(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project = client.post(
        "/projects",
        json={"name": "Sprint 11B Candidate Detection", "description": "", "status": "active"},
    ).json()
    preview_path = tmp_path / "candidate-source.png"
    create_candidate_source(preview_path)
    job = client.post(
        "/generation_jobs",
        json={
            "project_id": project["id"],
            "job_type": "real_ui_generation",
            "status": "completed",
            "progress": 100,
            "input_json": json.dumps({"device_type": "mobile", "width": 1024, "height": 1024}),
            "output_json": "",
            "error_message": "",
            "logs": "completed",
        },
    ).json()
    asset = client.post(
        "/assets",
        json={
            "project_id": project["id"],
            "asset_type": "ui_preview",
            "device_type": "mobile",
            "width": 1024,
            "height": 1024,
            "file_path": str(preview_path),
            "original_filename": "candidate-source.png",
            "metadata_json": "{}",
            "source": "ai_generated",
            "generation_job_id": job["id"],
            "thumbnail_path": "",
        },
    ).json()

    response = client.post(f"/assets/{asset['id']}/process-components")

    assert response.status_code == 200
    payload = response.json()
    package_dir = Path(payload["manifest_path"]).parent
    legacy_report = validate_package(package_dir)
    assert legacy_report["ok"] is True

    candidate_manifest_path = Path(payload["candidate_manifest_path"])
    candidate_preview_html_path = Path(payload["candidate_preview_html_path"])
    assert candidate_manifest_path.exists()
    assert candidate_preview_html_path.exists()

    candidate_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    candidates = candidate_manifest["candidates"]
    candidate_types = {candidate["candidate_type"] for candidate in candidates}
    assert EXPECTED_CANDIDATE_TYPES.issubset(candidate_types)
    assert candidate_manifest["candidates_dir"] == "candidates"

    for candidate in candidates:
        assert set(candidate) == {
            "candidate_id",
            "candidate_type",
            "resource_category",
            "bounds",
            "confidence",
            "image_path",
            "transparent",
            "review_status",
        }
        assert candidate["candidate_type"] in EXPECTED_CANDIDATE_TYPES
        assert candidate["resource_category"].endswith("_asset")
        assert 0.0 <= candidate["confidence"] <= 1.0
        assert candidate["review_status"] == "pending"
        assert candidate["image_path"].startswith("candidates/")
        assert (package_dir / candidate["image_path"]).exists()
        assert set(candidate["bounds"]) == {"x", "y", "width", "height"}
        assert candidate["bounds"]["width"] > 0
        assert candidate["bounds"]["height"] > 0

    preview_html = candidate_preview_html_path.read_text(encoding="utf-8")
    for candidate_type in EXPECTED_CANDIDATE_TYPES:
        assert candidate_type in preview_html
