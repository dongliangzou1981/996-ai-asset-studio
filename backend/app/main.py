from pathlib import Path
import os
import re

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from app.db import StudioDatabase
from app.schema import TABLE_NAMES
from app.schemas import (
    Asset,
    AssetCreate,
    AssetList,
    BasePanel,
    BasePanelCreate,
    BasePanelList,
    GenerationJob,
    GenerationJobCreate,
    GenerationJobList,
    GenerationJobPatch,
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


def default_upload_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "uploads"


def safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", filename.strip())
    return cleaned or "upload.bin"


def image_size(data: bytes, extension: str) -> tuple[int, int]:
    if extension == ".png" and data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if extension in {".jpg", ".jpeg"} and data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                return int.from_bytes(data[index + 3:index + 5], "big"), int.from_bytes(data[index + 1:index + 3], "big")
            segment_length = int.from_bytes(data[index:index + 2], "big")
            index += max(segment_length, 2)
    if extension == ".webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X" and len(data) >= 30:
            width = int.from_bytes(data[24:27], "little") + 1
            height = int.from_bytes(data[27:30], "little") + 1
            return width, height
    return 0, 0


def create_app(database_path: str | Path | None = None, upload_dir: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="996 AI Asset Studio API", version="0.4.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    database = StudioDatabase(Path(database_path) if database_path else default_database_path())
    database.initialize()
    upload_root = Path(upload_dir) if upload_dir else default_upload_dir()
    upload_root.mkdir(parents=True, exist_ok=True)
    app.state.database = database
    app.state.upload_dir = upload_root

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

    @app.post("/base_panels", response_model=BasePanel, status_code=status.HTTP_201_CREATED)
    def create_base_panel(payload: BasePanelCreate) -> BasePanel:
        if database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        if database.get_style_profile(payload.style_profile_id) is None:
            raise HTTPException(status_code=400, detail="Style profile does not exist")
        return database.create_base_panel(payload)

    @app.get("/base_panels", response_model=BasePanelList)
    def list_base_panels(project_id: str | None = None) -> BasePanelList:
        return BasePanelList(items=database.list_base_panels(project_id=project_id))

    @app.get("/base_panels/{base_panel_id}", response_model=BasePanel)
    def get_base_panel(base_panel_id: str) -> BasePanel:
        base_panel = database.get_base_panel(base_panel_id)
        if base_panel is None:
            raise HTTPException(status_code=404, detail="Base panel not found")
        return base_panel

    @app.put("/base_panels/{base_panel_id}", response_model=BasePanel)
    def update_base_panel(base_panel_id: str, payload: BasePanelCreate) -> BasePanel:
        if database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        if database.get_style_profile(payload.style_profile_id) is None:
            raise HTTPException(status_code=400, detail="Style profile does not exist")
        base_panel = database.update_base_panel(base_panel_id, payload)
        if base_panel is None:
            raise HTTPException(status_code=404, detail="Base panel not found")
        return base_panel

    @app.delete("/base_panels/{base_panel_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_base_panel(base_panel_id: str) -> Response:
        if not database.delete_base_panel(base_panel_id):
            raise HTTPException(status_code=404, detail="Base panel not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/base_panels/{base_panel_id}/copy", response_model=BasePanel, status_code=status.HTTP_201_CREATED)
    def copy_base_panel(base_panel_id: str) -> BasePanel:
        base_panel = database.copy_base_panel(base_panel_id)
        if base_panel is None:
            raise HTTPException(status_code=404, detail="Base panel not found")
        return base_panel

    @app.get("/generation_jobs", response_model=GenerationJobList)
    def list_generation_jobs(project_id: str | None = None) -> GenerationJobList:
        return GenerationJobList(items=database.list_generation_jobs(project_id=project_id))

    @app.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
    def create_asset(payload: AssetCreate) -> Asset:
        if payload.project_id and database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        return database.create_asset(payload)

    @app.get("/assets", response_model=AssetList)
    def list_assets(project_id: str | None = None, asset_type: str | None = None) -> AssetList:
        return AssetList(items=database.list_assets(project_id=project_id, asset_type=asset_type))

    @app.get("/assets/{asset_id}", response_model=Asset)
    def get_asset(asset_id: str) -> Asset:
        asset = database.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @app.put("/assets/{asset_id}", response_model=Asset)
    def update_asset(asset_id: str, payload: AssetCreate) -> Asset:
        if payload.project_id and database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        asset = database.update_asset(asset_id, payload)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @app.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_asset(asset_id: str) -> Response:
        if not database.delete_asset(asset_id):
            raise HTTPException(status_code=404, detail="Asset not found")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.post("/assets/upload", response_model=Asset, status_code=status.HTTP_201_CREATED)
    async def upload_asset(
        file: UploadFile = File(...),
        project_id: str | None = Form(default=None),
        asset_type: str = Form(default="reference_image"),
        device_type: str = Form(default=""),
    ) -> Asset:
        original_filename = file.filename or "upload.bin"
        extension = Path(original_filename).suffix.lower()
        if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise HTTPException(status_code=400, detail="Only png, jpg, jpeg, and webp files are supported")
        if project_id and database.get_project(project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")

        data = await file.read()
        width, height = image_size(data, extension)
        upload_name = f"{safe_filename(Path(original_filename).stem)}-{os.urandom(4).hex()}{extension}"
        upload_path = upload_root / upload_name
        upload_path.write_bytes(data)
        return database.create_asset(
            AssetCreate(
                project_id=project_id or None,
                asset_type=asset_type,  # type: ignore[arg-type]
                device_type=device_type,
                width=width,
                height=height,
                file_path=str(upload_path),
                original_filename=original_filename,
                metadata_json="{}",
            )
        )

    @app.post("/generation_jobs", response_model=GenerationJob, status_code=status.HTTP_201_CREATED)
    def create_generation_job(payload: GenerationJobCreate) -> GenerationJob:
        if payload.project_id and database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        return database.create_generation_job(payload)

    @app.get("/generation_jobs/{generation_job_id}", response_model=GenerationJob)
    def get_generation_job(generation_job_id: str) -> GenerationJob:
        generation_job = database.get_generation_job(generation_job_id)
        if generation_job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return generation_job

    @app.patch("/generation_jobs/{generation_job_id}", response_model=GenerationJob)
    def update_generation_job(generation_job_id: str, payload: GenerationJobPatch) -> GenerationJob:
        generation_job = database.update_generation_job(generation_job_id, payload)
        if generation_job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return generation_job

    @app.post("/generation_jobs/{generation_job_id}/retry", response_model=GenerationJob)
    def retry_generation_job(generation_job_id: str) -> GenerationJob:
        generation_job = database.retry_generation_job(generation_job_id)
        if generation_job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return generation_job

    return app


app = create_app()
