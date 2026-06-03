from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(database_path=tmp_path / "studio.db"))


def seed_project_and_style(client: TestClient) -> tuple[str, str]:
    project = client.post(
        "/projects",
        json={"name": "Panel Project", "description": "Panel test", "status": "active"},
    ).json()
    style = client.post(
        "/style_profiles",
        json={
            "project_id": project["id"],
            "name": "Clean Mobile",
            "description": "Simple UI",
            "palette_json": "{}",
            "prompt_notes": "",
        },
    ).json()
    return project["id"], style["id"]


def panel_payload(project_id: str, style_profile_id: str) -> dict[str, str | int]:
    return {
        "project_id": project_id,
        "style_profile_id": style_profile_id,
        "panel_type": "main_panel",
        "device_type": "mobile",
        "width": 1080,
        "height": 1920,
        "texture": "soft_glass",
        "border_style": "rounded_8",
        "background_style": "layered_gradient",
        "color_scheme": "blue_white",
    }


def test_base_panel_crud_and_copy_round_trip(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id, style_profile_id = seed_project_and_style(client)

    created = client.post("/base_panels", json=panel_payload(project_id, style_profile_id))
    assert created.status_code == 201
    panel = created.json()
    assert panel["id"]
    assert panel["project_id"] == project_id
    assert panel["style_profile_id"] == style_profile_id
    assert panel["panel_type"] == "main_panel"
    assert panel["device_type"] == "mobile"
    assert panel["width"] == 1080
    assert panel["created_at"]
    assert panel["updated_at"]

    listed = client.get(f"/base_panels?project_id={project_id}")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [panel["id"]]

    fetched = client.get(f"/base_panels/{panel['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["background_style"] == "layered_gradient"

    update_payload = panel_payload(project_id, style_profile_id)
    update_payload.update(
        {
            "panel_type": "popup_panel",
            "device_type": "tablet",
            "width": 1536,
            "height": 2048,
            "texture": "paper",
            "border_style": "thin_line",
            "background_style": "flat",
            "color_scheme": "warm_gray",
        }
    )
    updated = client.put(f"/base_panels/{panel['id']}", json=update_payload)
    assert updated.status_code == 200
    assert updated.json()["panel_type"] == "popup_panel"
    assert updated.json()["width"] == 1536

    copied = client.post(f"/base_panels/{panel['id']}/copy")
    assert copied.status_code == 201
    copy = copied.json()
    assert copy["id"] != panel["id"]
    assert copy["panel_type"] == "popup_panel"
    assert copy["color_scheme"] == "warm_gray"

    deleted = client.delete(f"/base_panels/{panel['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/base_panels/{panel['id']}").status_code == 404
    assert client.get(f"/base_panels/{copy['id']}").status_code == 200


def test_rejects_unknown_base_panel_type(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    project_id, style_profile_id = seed_project_and_style(client)
    payload = panel_payload(project_id, style_profile_id)
    payload["panel_type"] = "unknown_panel"

    response = client.post("/base_panels", json=payload)

    assert response.status_code == 422


def test_generation_jobs_list_and_openapi_contract(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    jobs = client.get("/generation_jobs")
    assert jobs.status_code == 200
    assert jobs.json()["items"] == []

    schema = client.get("/openapi.json").json()
    assert "/base_panels" in schema["paths"]
    assert "/base_panels/{base_panel_id}" in schema["paths"]
    assert "/base_panels/{base_panel_id}/copy" in schema["paths"]
    assert "/generation_jobs" in schema["paths"]
    assert "BasePanelCreate" in schema["components"]["schemas"]
    assert "GenerationJob" in schema["components"]["schemas"]

