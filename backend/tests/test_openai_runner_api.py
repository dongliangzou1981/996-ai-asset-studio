from pathlib import Path
import base64
from io import BytesIO
import json
import sys

import httpx
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color=(245, 248, 252)).save(buffer, format="PNG")
    return buffer.getvalue()


class FakeOpenAIResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.openai.com/v1/images/generations")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self) -> dict:
        return self.payload


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db", upload_dir=tmp_path / "uploads"))


def create_openai_provider(client: TestClient, config_json: str = "{\"api_key_env\":\"OPENAI_API_KEY\"}") -> str:
    response = client.post(
        "/ai_providers",
        json={
            "name": "OpenAI Images",
            "type": "openai",
            "enabled": True,
            "config_json": config_json,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_openai_job(client: TestClient, provider_id: str) -> str:
    response = client.post(
        "/generation_jobs",
        json={
            "project_id": None,
            "provider_id": provider_id,
            "job_type": "ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": "{\"prompt\":\"Generate a shop UI\",\"device_type\":\"mobile\",\"width\":1024,\"height\":1536}",
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "queued",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_real_openai_job(client: TestClient, provider_id: str, project_id: str) -> str:
    response = client.post(
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
                    "prompt": "生成一张移动端主界面 UI",
                    "device_type": "mobile",
                    "width": 1024,
                    "height": 1536,
                },
                ensure_ascii=False,
            ),
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "queued",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_openai_runner_success_writes_ai_generated_assets(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    provider_id = create_openai_provider(client)
    job_id = create_openai_job(client, provider_id)

    def fake_post(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert url == "https://api.openai.com/v1/images/generations"
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test-secret"
        assert kwargs["json"]["size"] == "1024x1536"
        return FakeOpenAIResponse({"data": [{"b64_json": base64.b64encode(png_bytes()).decode("ascii")}]})

    monkeypatch.setattr("app.job_runner.httpx.post", fake_post)

    run = client.post(f"/generation_jobs/{job_id}/run")

    assert run.status_code == 200
    completed = run.json()
    assert completed["status"] == "completed"
    assert "OpenAI run completed" in completed["logs"]
    assert "sk-test-secret" not in json.dumps(completed)
    output = json.loads(completed["output_json"])
    assert output["asset_ids"]
    assert Path(completed["output_preview_path"]).exists()

    assets = client.get(f"/generation_jobs/{job_id}/results").json()["items"]
    assert {"ai_generated", "component_processing"} <= {asset["source"] for asset in assets}
    assert len([asset for asset in assets if asset["source"] == "component_processing"]) == 6
    assert all(asset["generation_job_id"] == job_id for asset in assets)
    assert all(Path(asset["thumbnail_path"]).exists() for asset in assets if asset["source"] == "ai_generated")


def test_real_ui_generation_openai_runs_component_processing(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    project = client.post(
        "/projects",
        json={"name": "Sprint8B OpenAI", "description": "Real UI generation", "status": "active"},
    ).json()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    provider_id = create_openai_provider(client)
    job_id = create_real_openai_job(client, provider_id, project["id"])

    def fake_post(url: str, **kwargs):  # type: ignore[no-untyped-def]
        assert url == "https://api.openai.com/v1/images/generations"
        assert kwargs["headers"]["Authorization"] == "Bearer sk-test-secret"
        assert kwargs["json"]["prompt"] == "生成一张移动端主界面 UI"
        return FakeOpenAIResponse({"data": [{"b64_json": base64.b64encode(png_bytes()).decode("ascii")}]})

    monkeypatch.setattr("app.job_runner.httpx.post", fake_post)

    run = client.post(f"/generation_jobs/{job_id}/run")

    assert run.status_code == 200
    completed = run.json()
    assert completed["status"] == "completed"
    assert "OpenAI run completed" in completed["logs"]
    output = json.loads(completed["output_json"])
    assert output["component_processing"]["component_asset_ids"]
    assert Path(output["component_processing"]["manifest_path"]).exists()
    assert Path(output["component_processing"]["annotation_path"]).exists()
    assert Path(output["component_processing"]["preview_html_path"]).exists()

    manifest = json.loads(Path(output["component_processing"]["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["components"][0]["component_name_zh"] == "主功能栏"
    annotation = json.loads(Path(output["component_processing"]["annotation_path"]).read_text(encoding="utf-8"))
    assert {"组件名称", "组件类型", "X坐标", "Y坐标", "宽度", "高度", "字体", "字号", "字体颜色"} <= set(
        annotation["components"][0]
    )
    preview_html = Path(output["component_processing"]["preview_html_path"]).read_text(encoding="utf-8")
    assert "主功能栏" in preview_html

    results = client.get(f"/generation_jobs/{job_id}/results").json()["items"]
    assert any(asset["asset_type"] == "ui_preview" and asset["source"] == "ai_generated" for asset in results)
    component_assets = [asset for asset in results if asset["source"] == "component_processing"]
    assert len(component_assets) == 6
    assert {asset["asset_type"] for asset in component_assets} == {"sliced_component"}
    assert all(Path(asset["file_path"]).exists() for asset in component_assets)


def test_openai_runner_missing_config_and_env_fail_jobs(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    missing_config_provider_id = create_openai_provider(client, "{}")
    missing_config_job_id = create_openai_job(client, missing_config_provider_id)

    missing_config = client.post(f"/generation_jobs/{missing_config_job_id}/run").json()
    assert missing_config["status"] == "failed"
    assert missing_config["error_message"] == "OpenAI provider requires config_json.api_key_env"
    assert "OpenAI run failed" in missing_config["logs"]

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    missing_env_provider_id = create_openai_provider(client)
    missing_env_job_id = create_openai_job(client, missing_env_provider_id)

    missing_env = client.post(f"/generation_jobs/{missing_env_job_id}/run").json()
    assert missing_env["status"] == "failed"
    assert missing_env["error_message"] == "Environment variable OPENAI_API_KEY is not set"
    assert "sk-" not in json.dumps(missing_env)


def test_openai_runner_api_failure_and_empty_response_fail_safely(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    provider_id = create_openai_provider(client)

    def failing_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        return FakeOpenAIResponse({}, status_code=500)

    monkeypatch.setattr("app.job_runner.httpx.post", failing_post)
    failed_job_id = create_openai_job(client, provider_id)
    failed = client.post(f"/generation_jobs/{failed_job_id}/run").json()
    assert failed["status"] == "failed"
    assert failed["error_message"] == "OpenAI API request failed: 500"
    assert "sk-test-secret" not in json.dumps(failed)

    def empty_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        return FakeOpenAIResponse({"data": []})

    monkeypatch.setattr("app.job_runner.httpx.post", empty_post)
    empty_job_id = create_openai_job(client, provider_id)
    empty = client.post(f"/generation_jobs/{empty_job_id}/run").json()
    assert empty["status"] == "failed"
    assert empty["error_message"] == "OpenAI response did not include image data"


def test_openai_runner_image_save_failure_fails_safely(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    provider_id = create_openai_provider(client)
    job_id = create_openai_job(client, provider_id)

    monkeypatch.setattr(
        "app.job_runner.httpx.post",
        lambda *args, **kwargs: FakeOpenAIResponse(
            {"data": [{"b64_json": base64.b64encode(png_bytes()).decode("ascii")}]}
        ),
    )
    original_write_bytes = Path.write_bytes

    def fake_write_bytes(path: Path, data: bytes) -> int:
        if path.name == "ui_preview.png":
            raise OSError("disk write failed")
        return original_write_bytes(path, data)

    monkeypatch.setattr(Path, "write_bytes", fake_write_bytes)

    failed = client.post(f"/generation_jobs/{job_id}/run").json()
    assert failed["status"] == "failed"
    assert "Failed to save OpenAI image" in failed["error_message"]
    assert "sk-test-secret" not in json.dumps(failed)
