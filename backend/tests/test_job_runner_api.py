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
    assert health.json()["status"] == "healthy"

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
    assert client.get(f"/ai_providers/{provider_id}/health").json()["status"] == "healthy"


def test_real_ui_generation_runner_creates_placeholder_asset(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)
    style = client.post(
        "/style_profiles",
        json={
            "project_id": project_id,
            "name": "Neon RPG",
            "description": "",
            "palette_json": "{}",
            "prompt_notes": "Use sharp contrast",
        },
    ).json()
    panel = client.post(
        "/base_panels",
        json={
            "project_id": project_id,
            "style_profile_id": style["id"],
            "panel_type": "main_panel",
            "device_type": "mobile",
            "width": 480,
            "height": 720,
            "texture": "glass",
            "border_style": "thin",
            "background_style": "dark",
            "color_scheme": "neon",
        },
    ).json()
    reference = client.post(
        "/assets",
        json={
            "project_id": project_id,
            "asset_type": "reference_image",
            "device_type": "mobile",
            "width": 480,
            "height": 720,
            "file_path": "assets/reference.png",
            "original_filename": "reference.png",
            "metadata_json": "{}",
            "source": "uploaded",
            "generation_job_id": None,
            "thumbnail_path": "",
        },
    ).json()
    provider = client.post(
        "/ai_providers",
        json={"name": "Future Real Provider", "type": "custom", "enabled": True, "config_json": "{}"},
    ).json()
    prompt = "Create a cinematic mobile battle pass screen"
    job = client.post(
        "/generation_jobs",
        json={
            "project_id": project_id,
            "provider_id": provider["id"],
            "job_type": "real_ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": json.dumps(
                {
                    "project_id": project_id,
                    "style_profile_id": style["id"],
                    "base_panel_id": panel["id"],
                    "reference_image_id": reference["id"],
                    "prompt": prompt,
                    "device_type": "mobile",
                    "width": 480,
                    "height": 720,
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
    assert completed["progress"] == 100
    assert "Real UI generation started" in completed["logs"]
    assert "Real UI generation placeholder completed" in completed["logs"]
    assert Path(completed["output_preview_path"]).exists()
    output = json.loads(completed["output_json"])
    assert output["job_type"] == "real_ui_generation"
    assert output["project_id"] == project_id
    assert output["style_profile_id"] == style["id"]
    assert output["base_panel_id"] == panel["id"]
    assert output["reference_image_id"] == reference["id"]
    assert output["prompt"] == prompt
    assert output["provider_id"] == provider["id"]
    assert output["asset_id"]

    results = client.get(f"/generation_jobs/{job.json()['id']}/results").json()["items"]
    assert len(results) == 1
    asset = results[0]
    assert asset["asset_type"] == "ui_preview"
    assert asset["source"] == "real_pipeline_placeholder"
    assert asset["generation_job_id"] == job.json()["id"]
    assert asset["project_id"] == project_id
    assert asset["device_type"] == "mobile"
    assert asset["width"] == 480
    assert asset["height"] == 720
    assert Path(asset["thumbnail_path"]).exists()
    metadata = json.loads(asset["metadata_json"])
    assert metadata["project_id"] == project_id
    assert metadata["style_profile_id"] == style["id"]
    assert metadata["base_panel_id"] == panel["id"]
    assert metadata["reference_image_id"] == reference["id"]
    assert metadata["prompt"] == prompt


def test_openrouter_provider_health_and_runner_placeholder(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    project_id = seed_project(client)

    missing_config_provider = client.post(
        "/ai_providers",
        json={"name": "OpenRouter Missing Config", "type": "openrouter", "enabled": True, "config_json": "{}"},
    )
    assert missing_config_provider.status_code == 201
    missing_health = client.get(f"/ai_providers/{missing_config_provider.json()['id']}/health").json()
    assert missing_health["status"] == "unhealthy"
    assert missing_health["message"] == "OpenRouter provider requires config_json.api_key_env"

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter-test-secret")
    provider = client.post(
        "/ai_providers",
        json={
            "name": "OpenRouter",
            "type": "openrouter",
            "enabled": True,
            "config_json": "{\"api_key_env\":\"OPENROUTER_API_KEY\"}",
        },
    )
    assert provider.status_code == 201
    provider_id = provider.json()["id"]
    health = client.get(f"/ai_providers/{provider_id}/health").json()
    assert health["status"] == "healthy"
    assert "sk-openrouter-test-secret" not in json.dumps(health)

    job = client.post(
        "/generation_jobs",
        json={
            "project_id": project_id,
            "provider_id": provider_id,
            "job_type": "real_ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": json.dumps(
                {
                    "project_id": project_id,
                    "prompt": "Generate an OpenRouter placeholder",
                    "device_type": "mobile",
                    "width": 320,
                    "height": 480,
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
    assert "OpenRouter runner placeholder completed" in completed["logs"]
    assert "sk-openrouter-test-secret" not in json.dumps(completed)
    output = json.loads(completed["output_json"])
    assert output["provider_type"] == "openrouter"
    assert output["runner"] == "openrouter"

    results = client.get(f"/generation_jobs/{job.json()['id']}/results").json()["items"]
    assert len(results) == 1
    assert results[0]["source"] == "real_pipeline_placeholder"


def test_auto_run_and_openai_health_without_secret(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)

    openai_provider = client.post(
        "/ai_providers",
        json={
            "name": "OpenAI Images",
            "type": "openai",
            "enabled": True,
            "config_json": "{}",
        },
    ).json()
    missing_env_key = client.get(f"/ai_providers/{openai_provider['id']}/health").json()
    assert missing_env_key["status"] == "unhealthy"
    assert "api_key_env" in missing_env_key["message"]

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    openai_env_provider = client.post(
        "/ai_providers",
        json={
            "name": "OpenAI Env",
            "type": "openai",
            "enabled": True,
            "config_json": "{\"api_key_env\":\"OPENAI_API_KEY\"}",
        },
    ).json()
    missing_env = client.get(f"/ai_providers/{openai_env_provider['id']}/health").json()
    assert missing_env["status"] == "unhealthy"
    assert missing_env["message"] == "Environment variable OPENAI_API_KEY is not set"

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
    assert len(health_list.json()["items"]) == 3


def test_provider_config_rejects_real_api_key_without_echoing_secret(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/ai_providers",
        json={
            "name": "Unsafe Provider",
            "type": "openai",
            "enabled": True,
            "config_json": "{\"api_key\":\"sk-test-secret\"}",
        },
    )

    assert response.status_code == 422
    assert "sk-test-secret" not in response.text
    assert "api_key_env" in response.text
