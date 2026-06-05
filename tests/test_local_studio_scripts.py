from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_studio_start_script_checks_key_and_starts_services() -> None:
    script = ROOT / "scripts" / "start_local_studio.ps1"

    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "backend\\.venv\\Scripts\\python.exe" in content
    assert "OFOX_API_KEY" in content
    assert "Read-Host" in content
    assert "-AsSecureString" in content
    assert "uvicorn" in content
    assert "npm run dev" in content
    assert "http://127.0.0.1:3001/studio" in content
    assert ".env" not in content


def test_local_studio_check_script_reports_core_endpoints() -> None:
    script = ROOT / "scripts" / "check_studio_env.ps1"

    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "OFOX_API_KEY" in content
    assert "http://127.0.0.1:8001/health" in content
    assert "http://127.0.0.1:3001/studio" in content
    assert "http://127.0.0.1:8001/production-studio/style-codes" in content
    assert "http://127.0.0.1:8001/ai_providers/health" in content
    assert ".env" not in content


def test_chinese_startup_entrypoint_wraps_local_studio_script() -> None:
    script = ROOT / "启动工作台.ps1"

    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "scripts\\start_local_studio.ps1" in content
    assert "Start-Process" in content
    assert "$FrontendPort/studio" in content
    assert ".env" not in content


def test_chinese_environment_check_uses_user_facing_statuses() -> None:
    script = ROOT / "环境检查.ps1"

    assert script.exists()
    content = script.read_text(encoding="utf-8")

    assert "OFOX_API_KEY" in content
    assert "http://127.0.0.1:$BackendPort/health" in content or "$backendUrl/health" in content
    assert "production-studio/style-codes" in content
    assert "ai_providers/health" in content
    assert "44CQ5q2j5bi4" in content
    assert "44CQ5byC5bi4" in content
    assert ".env" not in content
