from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from app.db import StudioDatabase
from app.schema import TABLE_NAMES
from app.schemas import (
    Project,
    ProjectCreate,
    ProjectList,
    StyleProfile,
    StyleProfileCreate,
    StyleProfileList,
)


def default_database_path() -> Path:
    configured = os.getenv("STUDIO_DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "studio.db"


def create_app(database_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="996 AI Asset Studio API", version="0.2.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    database = StudioDatabase(Path(database_path) if database_path else default_database_path())
    database.initialize()
    app.state.database = database

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "996-ai-asset-studio-api"}

    @app.get("/schema/tables")
    def schema_tables() -> dict[str, list[str]]:
        return {"tables": TABLE_NAMES}

    @app.post("/projects", response_model=Project, status_code=status.HTTP_201_CREATED)
    def create_project(payload: ProjectCreate) -> Project:
        return database.create_project(payload)

    @app.get("/projects", response_model=ProjectList)
    def list_projects() -> ProjectList:
        return ProjectList(items=database.list_projects())

    @app.get("/projects/{project_id}", response_model=Project)
    def get_project(project_id: str) -> Project:
        project = database.get_project(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @app.put("/projects/{project_id}", response_model=Project)
    def update_project(project_id: str, payload: ProjectCreate) -> Project:
        project = database.update_project(project_id, payload)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    @app.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_project(project_id: str) -> Response:
        if not database.delete_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/style_profiles", response_model=StyleProfile, status_code=status.HTTP_201_CREATED)
    def create_style_profile(payload: StyleProfileCreate) -> StyleProfile:
        if database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        return database.create_style_profile(payload)

    @app.get("/style_profiles", response_model=StyleProfileList)
    def list_style_profiles(project_id: str | None = None) -> StyleProfileList:
        return StyleProfileList(items=database.list_style_profiles(project_id=project_id))

    @app.put("/style_profiles/{style_profile_id}", response_model=StyleProfile)
    def update_style_profile(style_profile_id: str, payload: StyleProfileCreate) -> StyleProfile:
        if database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        style_profile = database.update_style_profile(style_profile_id, payload)
        if style_profile is None:
            raise HTTPException(status_code=404, detail="Style profile not found")
        return style_profile

    @app.delete("/style_profiles/{style_profile_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_style_profile(style_profile_id: str) -> Response:
        if not database.delete_style_profile(style_profile_id):
            raise HTTPException(status_code=404, detail="Style profile not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return app


app = create_app()
