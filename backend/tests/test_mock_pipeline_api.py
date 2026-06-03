from pathlib import Path
import json
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    upload_dir = tmp_path / "uploads"
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=upload_dir))


def seed_project(client: TestClient) -> tuple[str, str]:
    project = client.post(
        "/projects",
        json={"name": "Mock Project", "description": "Mock pipeline", "status": "active"},
    ).json()
    return project["id"], project["name"]


def test_create_and_run_mock_ui_generation_job(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id, project_name = seed_project(client)

    created = client.post(
        "/generation_jobs/mock-ui",
        json={
            "project_id": project_id,
            "device_type": "mobile",
            "width": 320,
            "height": 480,
        },
    )

    assert created.status_code == 201
    job = created.json()
    assert job["job_type"] == "mock_ui_generation"
    assert job["status"] == "pending"
    assert job["progress"] == 0
    assert "Mock UI job queued" in job["logs"]

    run = client.post(f"/generation_jobs/{job['id']}/run-mock")

    assert run.status_code == 200
    completed = run.json()
    assert completed["status"] == "completed"
    assert completed["progress"] == 100
    assert completed["error_message"] == ""
    assert "Mock run started" in completed["logs"]
    assert "Mock run completed" in completed["logs"]

    output = json.loads(completed["output_json"])
    assert output["mock"] is True
    assert len(output["asset_ids"]) == 3
    assert {item["asset_type"] for item in output["assets"]} == {
        "ui_preview",
        "annotated_preview",
        "sliced_component",
    }

    results = client.get(f"/generation_jobs/{job['id']}/results")
    assert results.status_code == 200
    result_items = results.json()["items"]
    assert len(result_items) == 3
    assert {item["source"] for item in result_items} == {"mock_generated"}
    assert {item["generation_job_id"] for item in result_items} == {job["id"]}
    assert all(Path(item["file_path"]).exists() for item in result_items)
    assert all(project_name in item["metadata_json"] for item in result_items)

    filtered = client.get(f"/assets?generation_job_id={job['id']}")
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [item["id"] for item in result_items]


def test_run_mock_marks_invalid_input_as_failed_and_retry_resets(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    created = client.post(
        "/generation_jobs",
        json={
            "project_id": None,
            "job_type": "mock_ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": "{",
            "output_json": "",
            "error_message": "",
            "logs": "queued",
        },
    ).json()

    run = client.post(f"/generation_jobs/{created['id']}/run-mock")

    assert run.status_code == 200
    failed = run.json()
    assert failed["status"] == "failed"
    assert failed["progress"] == 100
    assert "Invalid mock input_json" in failed["error_message"]
    assert "Mock run failed" in failed["logs"]

    retried = client.post(f"/generation_jobs/{created['id']}/retry")
    assert retried.status_code == 200
    assert retried.json()["status"] == "pending"
    assert retried.json()["retry_count"] == 1
    assert "Retry 1 queued" in retried.json()["logs"]


def test_mock_pipeline_openapi_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    schema = client.get("/openapi.json").json()

    assert "/generation_jobs/mock-ui" in schema["paths"]
    assert "/generation_jobs/{generation_job_id}/run-mock" in schema["paths"]
    assert "/generation_jobs/{generation_job_id}/results" in schema["paths"]
    assert "MockUiGenerationRequest" in schema["components"]["schemas"]
