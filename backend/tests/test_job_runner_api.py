from pathlib import Path
import json
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def seed_project(client: TestClient) -> str:
    return client.post(
        "/projects",
        json={"name": "Runner Project", "description": "Unified runner", "status": "active"},
    ).json()["id"]


def test_provider_health_update_and_unified_job_runner_outputs(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)

    provider = client.post(
        "/ai_providers",
        json={"name": "Local Mock", "type": "mock", "enabled": True, "config_json": "{}"},
    )
    assert provider.status_code == 201
    provider_id = provider.json()["id"]

    health = client.get(f"/ai_providers/{provider_id}/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    job = client.post(
        "/generation_jobs",
        json={
            "project_id": project_id,
            "provider_id": provider_id,
            "job_type": "ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": json.dumps(
                {
                    "prompt": "Generate a colorful shop screen",
                    "device_type": "pc",
                    "width": 640,
                    "height": 360,
                }
            ),
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "queued",
        },
    )
    assert job.status_code == 201

    run = client.post(f"/generation_jobs/{job.json()['id']}/run")
    assert run.status_code == 200
    completed = run.json()
    assert completed["status"] == "completed"
    assert completed["provider_id"] == provider_id
    assert completed["output_preview_path"]
    assert Path(completed["output_preview_path"]).exists()

    output = json.loads(completed["output_json"])
    assert "996-ready" in output["ready_dir"]
    assert len(output["asset_ids"]) == 3

    results = client.get(f"/generation_jobs/{job.json()['id']}/results").json()["items"]
    assert {item["asset_type"] for item in results} == {
        "ui_preview",
        "annotated_preview",
        "sliced_component",
    }
    assert {item["source"] for item in results} == {"mock_generated"}
    assert all(Path(item["thumbnail_path"]).exists() for item in results)

    filtered = client.get(f"/assets?device_type=pc&generation_job_id={job.json()['id']}")
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 3

    updated = client.put(
        f"/ai_providers/{provider_id}",
        json={"name": "Local Mock Disabled", "type": "mock", "enabled": False, "config_json": "{}"},
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False
    assert client.get(f"/ai_providers/{provider_id}/health").json()["status"] == "disabled"


def test_auto_run_and_openai_health_without_secret(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    openai_provider = client.post(
        "/ai_providers",
        json={
            "name": "OpenAI Images",
            "type": "openai",
            "enabled": True,
            "config_json": "{\"model\":\"gpt-image-1\"}",
        },
    ).json()
    assert client.get(f"/ai_providers/{openai_provider['id']}/health").json()["status"] == "missing_config"

    mock_provider = client.post(
        "/ai_providers",
        json={"name": "Auto Mock", "type": "mock", "enabled": True, "config_json": "{}"},
    ).json()
    job = client.post(
        "/generation_jobs",
        json={
            "project_id": None,
            "provider_id": mock_provider["id"],
            "job_type": "ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": "{\"device_type\":\"mobile\",\"width\":320,\"height\":240}",
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "queued",
            "auto_run": True,
        },
    )
    assert job.status_code == 201
    assert job.json()["status"] == "completed"
    assert job.json()["output_preview_path"]

    health_list = client.get("/ai_providers/health")
    assert health_list.status_code == 200
    assert len(health_list.json()["items"]) == 2
