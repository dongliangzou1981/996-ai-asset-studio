from __future__ import annotations

import json
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def write_png(path: Path, *, transparent: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (8, 8), (0, 128, 255, 255))
    if transparent:
        image.putpixel((0, 0), (0, 128, 255, 0))
    image.save(path)


def write_package(upload_root: Path) -> Path:
    package = upload_root / "996-ready" / "STYLE_REVIEW" / "bag_ui" / "job-review"
    (package / "components").mkdir(parents=True)
    write_png(package / "ui_preview.png")
    write_png(package / "components" / "primary_action_button.png", transparent=False)
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
            }
        ],
    }
    annotation = {"schema_version": "1.0", "template": "bag_ui", "components": manifest["components"]}
    (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (package / "annotation.json").write_text(json.dumps(annotation), encoding="utf-8")
    return package


def test_analyze_endpoint_writes_review_files_and_review_can_be_read(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    package = write_package(tmp_path / "uploads")

    analyze = client.post("/production-studio/analyze", params={"package_dir": str(package)})

    assert analyze.status_code == 200
    assert (package / "production_review.json").exists()
    assert (package / "component_review_analysis.json").exists()
    assert (package / "manual_acceptance.json").exists()
    assert (package / "production_review.html").exists()

    response = client.get("/production-studio/production-review", params={"package_dir": str(package)})
    assert response.status_code == 200
    assert response.json()["screen_type"] == "bag_ui"


def test_component_review_endpoint_reads_json(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    package = write_package(tmp_path / "uploads")
    client.post("/production-studio/analyze", params={"package_dir": str(package)})

    response = client.get("/production-studio/component-review", params={"package_dir": str(package)})

    assert response.status_code == 200
    assert response.json()["components"][0]["component_id"] == "primary_action_button"


def test_missing_manual_acceptance_returns_pending_default(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    package = write_package(tmp_path / "uploads")

    response = client.get("/production-studio/manual-acceptance", params={"package_dir": str(package)})

    assert response.status_code == 200
    assert response.json()["review_status"] == "pending"
    assert response.json()["components"] == []


def test_manual_acceptance_update_writes_package_json(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    package = write_package(tmp_path / "uploads")
    client.post("/production-studio/analyze", params={"package_dir": str(package)})

    response = client.put(
        "/production-studio/manual-acceptance",
        params={"package_dir": str(package)},
        json={"review_status": "accepted", "reviewer": "qa", "remarks": "ok"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "accepted"
    assert body["reviewer"] == "qa"
    assert body["accepted_by"] == "qa"
    assert body["accepted_at"]
    saved = json.loads((package / "manual_acceptance.json").read_text(encoding="utf-8"))
    assert saved["review_status"] == "accepted"


def test_review_endpoint_rejects_path_outside_upload_root(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    response = client.get("/production-studio/production-review", params={"package_dir": str(outside)})

    assert response.status_code == 400
