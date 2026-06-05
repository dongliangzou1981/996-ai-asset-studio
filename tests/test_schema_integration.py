from __future__ import annotations

import json
from pathlib import Path
import sys
import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import create_app
from scripts.validate_996_export import validate_package


class FakeImageResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def png_b64() -> str:
    buffer = BytesIO()
    Image.new("RGBA", (1024, 1024), color=(32, 48, 64, 255)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def test_component_processing_outputs_schema_v1_package(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project = client.post(
        "/projects",
        json={"name": "Sprint 11A Schema Integration", "description": "", "status": "active"},
    ).json()
    preview_path = tmp_path / "source-ui-preview.png"
    Image.new("RGBA", (1024, 1024), color=(32, 48, 64, 255)).save(preview_path, format="PNG")
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
            "original_filename": "source-ui-preview.png",
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
    report = validate_package(package_dir)
    assert report["ok"] is True
    assert report["checks"]["schema_v1"] is True
    assert report["checks"]["transparent_fields"] is True
    assert report["errors"] == []

    manifest = json.loads(Path(payload["manifest_path"]).read_text(encoding="utf-8"))
    annotation = json.loads(Path(payload["annotation_path"]).read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "1.0"
    assert manifest["package_type"] == "996-ready"
    assert manifest["ui_preview"] == "ui_preview.png"
    assert manifest["components_dir"] == "components"
    assert all(component["file"].startswith("components/") for component in manifest["components"])
    assert all("transparent" in component for component in manifest["components"])
    assert annotation["schema_version"] == "1.0"
    assert annotation["coordinate_space"] == "ui_preview_pixels"
    assert all("transparent" in component for component in annotation["components"])


def test_mocked_ofox_real_job_outputs_schema_v1_package(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setenv("OFOX_API_KEY", "sk-ofox-test-secret")
    project = client.post(
        "/projects",
        json={"name": "Sprint 11A Ofox Schema", "description": "", "status": "active"},
    ).json()
    provider = client.post(
        "/ai_providers",
        json={
            "name": "Ofox Schema Provider",
            "type": "ofox",
            "enabled": True,
            "config_json": "{\"api_key_env\":\"OFOX_API_KEY\",\"base_url\":\"https://api.ofox.ai/v1\",\"model\":\"gpt-image-2\"}",
        },
    ).json()
    job = client.post(
        "/generation_jobs",
        json={
            "project_id": project["id"],
            "provider_id": provider["id"],
            "job_type": "real_ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": json.dumps(
                {
                    "project_id": project["id"],
                    "prompt": "Generate a mobile game main UI",
                    "device_type": "mobile",
                    "width": 1024,
                    "height": 1024,
                }
            ),
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "queued",
        },
    ).json()

    def fake_post(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert url == "https://api.ofox.ai/v1/images/generations"
        assert kwargs["json"]["model"] == "gpt-image-2"
        return FakeImageResponse({"data": [{"b64_json": png_b64()}]})

    monkeypatch.setattr("app.job_runner.httpx.post", fake_post)

    completed = client.post(f"/generation_jobs/{job['id']}/run").json()

    output = json.loads(completed["output_json"])
    package_dir = Path(output["component_processing"]["manifest_path"]).parent
    report = validate_package(package_dir)
    assert completed["status"] == "completed"
    assert report["ok"] is True
    assert report["checks"]["schema_v1"] is True
    assert report["checks"]["transparent_fields"] is True
    assert report["errors"] == []
