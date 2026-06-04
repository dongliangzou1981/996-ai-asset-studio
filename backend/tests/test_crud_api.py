from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db"))


def test_cors_allows_local_frontend_origins(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

    for origin in allowed_origins:
        response = client.options(
            "/projects",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin


def test_project_crud_round_trip(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    created = client.post(
        "/projects",
        json={"name": "Match-3 Launch", "description": "Playable ad art", "status": "draft"},
    )
    assert created.status_code == 201
    project = created.json()
    assert project["id"]
    assert project["name"] == "Match-3 Launch"
    assert project["description"] == "Playable ad art"
    assert project["status"] == "draft"
    assert project["created_at"]
    assert project["updated_at"]

    listed = client.get("/projects")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [project["id"]]

    fetched = client.get(f"/projects/{project['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Match-3 Launch"

    updated = client.put(
        f"/projects/{project['id']}",
        json={"name": "Match-3 Launch V2", "description": "Refined", "status": "active"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Match-3 Launch V2"
    assert updated.json()["status"] == "active"

    deleted = client.delete(f"/projects/{project['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/projects/{project['id']}").status_code == 404


def test_style_profile_crud_round_trip(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project = client.post("/projects", json={"name": "Puzzle", "description": "", "status": "draft"}).json()

    created = client.post(
        "/style_profiles",
        json={
            "project_id": project["id"],
            "name": "Candy UI",
            "description": "Bright, rounded, mobile friendly",
            "palette_json": "{\"primary\":\"#ff6b9a\"}",
            "prompt_notes": "Use glossy buttons",
        },
    )
    assert created.status_code == 201
    style = created.json()
    assert style["id"]
    assert style["project_id"] == project["id"]
    assert style["name"] == "Candy UI"

    listed = client.get("/style_profiles")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [style["id"]]

    filtered = client.get(f"/style_profiles?project_id={project['id']}")
    assert filtered.status_code == 200
    assert len(filtered.json()["items"]) == 1

    updated = client.put(
        f"/style_profiles/{style['id']}",
        json={
            "project_id": project["id"],
            "name": "Candy UI Plus",
            "description": "More contrast",
            "palette_json": "{\"primary\":\"#f43f5e\"}",
            "prompt_notes": "Use clearer hierarchy",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Candy UI Plus"

    deleted = client.delete(f"/style_profiles/{style['id']}")
    assert deleted.status_code == 204
    assert client.get("/style_profiles").json()["items"] == []


def test_openapi_contains_crud_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    schema = client.get("/openapi.json").json()

    assert "/projects" in schema["paths"]
    assert "/projects/{project_id}" in schema["paths"]
    assert "/style_profiles" in schema["paths"]
    assert "/style_profiles/{style_profile_id}" in schema["paths"]
    assert "ProjectCreate" in schema["components"]["schemas"]
    assert "StyleProfileCreate" in schema["components"]["schemas"]
