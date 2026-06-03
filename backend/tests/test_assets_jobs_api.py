from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x02"
    b"\x00\x00\x00\x03"
    b"\x08\x02\x00\x00\x00"
    b"\x00\x00\x00\x00"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def make_client(tmp_path: Path) -> TestClient:
    upload_dir = tmp_path / "uploads"
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=upload_dir))


def seed_project(client: TestClient) -> str:
    project = client.post(
        "/projects",
        json={"name": "Asset Project", "description": "Asset test", "status": "active"},
    ).json()
    return project["id"]


def asset_payload(project_id: str | None) -> dict[str, str | int | None]:
    return {
        "project_id": project_id,
        "asset_type": "reference_image",
        "device_type": "mobile",
        "width": 1080,
        "height": 1920,
        "file_path": "assets/reference.png",
        "original_filename": "reference.png",
        "metadata_json": "{\"role\":\"mood\"}",
    }


def test_asset_crud_supports_project_and_loose_assets(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)

    created = client.post("/assets", json=asset_payload(project_id))
    assert created.status_code == 201
    asset = created.json()
    assert asset["id"]
    assert asset["project_id"] == project_id
    assert asset["asset_type"] == "reference_image"

    loose = client.post("/assets", json=asset_payload(None))
    assert loose.status_code == 201
    assert loose.json()["project_id"] is None

    by_project = client.get(f"/assets?project_id={project_id}")
    assert by_project.status_code == 200
    assert [item["id"] for item in by_project.json()["items"]] == [asset["id"]]

    by_type = client.get("/assets?asset_type=reference_image")
    assert by_type.status_code == 200
    assert len(by_type.json()["items"]) == 2

    fetched = client.get(f"/assets/{asset['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["original_filename"] == "reference.png"

    update_payload = asset_payload(project_id)
    update_payload.update(
        {
            "asset_type": "icon",
            "device_type": "desktop",
            "width": 128,
            "height": 128,
            "file_path": "assets/icon.png",
            "original_filename": "icon.png",
            "metadata_json": "{\"slot\":\"primary\"}",
        }
    )
    updated = client.put(f"/assets/{asset['id']}", json=update_payload)
    assert updated.status_code == 200
    assert updated.json()["asset_type"] == "icon"
    assert updated.json()["width"] == 128

    deleted = client.delete(f"/assets/{asset['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/assets/{asset['id']}").status_code == 404


def test_upload_asset_accepts_images_and_creates_asset_record(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)

    response = client.post(
        "/assets/upload",
        data={"project_id": project_id, "asset_type": "ui_preview", "device_type": "mobile"},
        files={"file": ("preview.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 201
    asset = response.json()
    assert asset["project_id"] == project_id
    assert asset["asset_type"] == "ui_preview"
    assert asset["width"] == 2
    assert asset["height"] == 3
    assert asset["original_filename"] == "preview.png"
    assert Path(asset["file_path"]).exists()


def test_upload_rejects_non_image_extension(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/assets/upload",
        data={"asset_type": "reference_image", "device_type": "mobile"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400


def test_generation_job_state_flow_and_retry(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)

    created = client.post(
        "/generation_jobs",
        json={
            "project_id": project_id,
            "job_type": "asset_prepare",
            "status": "pending",
            "progress": 0,
            "input_json": "{\"asset_id\":\"asset-1\"}",
            "output_json": "",
            "error_message": "",
            "logs": "queued",
        },
    )
    assert created.status_code == 201
    job = created.json()
    assert job["retry_count"] == 0
    assert job["logs"] == "queued"

    fetched = client.get(f"/generation_jobs/{job['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["job_type"] == "asset_prepare"

    updated = client.patch(
        f"/generation_jobs/{job['id']}",
        json={
            "status": "failed",
            "progress": 45,
            "output_json": "",
            "error_message": "mock failure",
            "logs": "queued\nfailed",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "failed"
    assert updated.json()["progress"] == 45
    assert updated.json()["error_message"] == "mock failure"

    retried = client.post(f"/generation_jobs/{job['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "pending"
    assert retried.json()["progress"] == 0
    assert retried.json()["retry_count"] == 1
    assert "Retry 1 queued" in retried.json()["logs"]

    listed = client.get(f"/generation_jobs?project_id={project_id}")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [job["id"]]


def test_generation_job_openapi_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    schema = client.get("/openapi.json").json()

    assert "/assets" in schema["paths"]
    assert "/assets/upload" in schema["paths"]
    assert "/generation_jobs/{generation_job_id}/retry" in schema["paths"]
    assert "AssetCreate" in schema["components"]["schemas"]
    assert "GenerationJobCreate" in schema["components"]["schemas"]

