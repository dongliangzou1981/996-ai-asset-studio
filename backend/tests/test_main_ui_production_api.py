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


def test_main_ui_endpoint_rejects_outside_package_path(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()

    response = client.get("/production-studio/main-ui-production", params={"package_dir": str(outside)})

    assert response.status_code == 400
