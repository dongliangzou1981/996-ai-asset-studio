from pathlib import Path
import json
import os
import re

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.component_processing import process_ui_preview_components
from app.db import StudioDatabase
from app.job_runner import JobRunnerService
from app.mock_worker import run_mock_generation
from app.provider_security import provider_health
from app.production_studio import list_style_codes as list_production_style_codes
from app.production_studio import run_production_studio
from app.schema import TABLE_NAMES
from app.schemas import (
    AiProvider,
    AiProviderCreate,
    AiProviderList,
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
    MockUiGenerationRequest,
    ProviderHealth,
    ProviderHealthList,
    ProductionStudioRequest,
    ProductionStudioResponse,
    ProductionStudioStyleCodeList,
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
    app = FastAPI(title="996 AI Asset Studio API", version="0.5.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def safe_validation_exception_handler(request, exc):  # type: ignore[no-untyped-def]
        safe_errors = []
        for error in exc.errors():
            safe_errors.append({key: value for key, value in error.items() if key not in {"input", "ctx"}})
        return JSONResponse(status_code=422, content={"detail": safe_errors})

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

    @app.get("/production-studio/style-codes", response_model=ProductionStudioStyleCodeList)
    def production_studio_style_codes() -> ProductionStudioStyleCodeList:
        return ProductionStudioStyleCodeList(items=list_production_style_codes())

    @app.post("/production-studio/generate", response_model=ProductionStudioResponse)
    def production_studio_generate(payload: ProductionStudioRequest) -> ProductionStudioResponse:
        try:
            return run_production_studio(
                payload=payload,
                database_path=database.database_path,
                upload_root=upload_root,
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/production-studio/files/{file_path:path}")
    def get_production_studio_file(file_path: str) -> FileResponse:
        candidate = (upload_root / file_path).resolve()
        upload_root_resolved = upload_root.resolve()
        if not candidate.is_relative_to(upload_root_resolved):
            raise HTTPException(status_code=400, detail="File path must stay inside upload root")
        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=404, detail="Production studio file not found")
        return FileResponse(candidate)

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
    def list_assets(
        project_id: str | None = None,
        asset_type: str | None = None,
        device_type: str | None = None,
        generation_job_id: str | None = None,
    ) -> AssetList:
        return AssetList(
            items=database.list_assets(
                project_id=project_id,
                asset_type=asset_type,
                device_type=device_type,
                generation_job_id=generation_job_id,
            )
        )

    @app.get("/assets/{asset_id}", response_model=Asset)
    def get_asset(asset_id: str) -> Asset:
        asset = database.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset

    @app.post("/assets/{asset_id}/process-components")
    def process_asset_components(asset_id: str) -> dict[str, str | list[str]]:
        asset = database.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        if asset.asset_type != "ui_preview":
            raise HTTPException(status_code=400, detail="Only ui_preview assets can be processed")
        try:
            return process_ui_preview_components(
                database=database,
                upload_root=upload_root,
                ui_preview=asset,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/assets/{asset_id}/file")
    def get_asset_file(asset_id: str) -> FileResponse:
        asset = database.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        file_path = Path(asset.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Asset file not found")
        return FileResponse(file_path)

    @app.get("/assets/{asset_id}/thumbnail")
    def get_asset_thumbnail(asset_id: str) -> FileResponse:
        asset = database.get_asset(asset_id)
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        thumbnail_path = Path(asset.thumbnail_path or asset.file_path)
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Asset thumbnail not found")
        return FileResponse(thumbnail_path)

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
                source="uploaded",
                generation_job_id=None,
                thumbnail_path="",
            )
        )

    @app.post("/generation_jobs/mock-ui", response_model=GenerationJob, status_code=status.HTTP_201_CREATED)
    def create_mock_ui_generation_job(payload: MockUiGenerationRequest) -> GenerationJob:
        if payload.project_id and database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        return database.create_generation_job(
            GenerationJobCreate(
                project_id=payload.project_id,
                job_type="mock_ui_generation",
                status="pending",
                progress=0,
                input_json=json.dumps(
                    {
                        "device_type": payload.device_type,
                        "width": payload.width,
                        "height": payload.height,
                    }
                ),
                output_json="",
                error_message="",
                logs="Mock UI job queued",
                provider_id=None,
            )
        )

    @app.post("/generation_jobs", response_model=GenerationJob, status_code=status.HTTP_201_CREATED)
    def create_generation_job(payload: GenerationJobCreate) -> GenerationJob:
        if payload.project_id and database.get_project(payload.project_id) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
        if payload.provider_id and database.get_ai_provider(payload.provider_id) is None:
            raise HTTPException(status_code=400, detail="Provider does not exist")
        generation_job = database.create_generation_job(payload)
        if payload.auto_run:
            return JobRunnerService(database, upload_root).run(generation_job.id) or generation_job
        return generation_job

    @app.post("/generation_jobs/{generation_job_id}/run", response_model=GenerationJob)
    def run_generation_job(generation_job_id: str) -> GenerationJob:
        generation_job = database.get_generation_job(generation_job_id)
        if generation_job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        if generation_job.status == "cancelled":
            raise HTTPException(status_code=400, detail="Cancelled jobs cannot be run")
        completed = JobRunnerService(database, upload_root).run(generation_job_id)
        if completed is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return completed

    @app.post("/generation_jobs/{generation_job_id}/run-mock", response_model=GenerationJob)
    def run_mock_generation_job(generation_job_id: str) -> GenerationJob:
        generation_job = database.get_generation_job(generation_job_id)
        if generation_job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        if generation_job.job_type != "mock_ui_generation":
            raise HTTPException(status_code=400, detail="Only mock_ui_generation jobs can run mock")
        completed = run_mock_generation(database, upload_root, generation_job_id)
        if completed is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return completed

    @app.get("/generation_jobs/{generation_job_id}/results", response_model=AssetList)
    def get_generation_job_results(generation_job_id: str) -> AssetList:
        if database.get_generation_job(generation_job_id) is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return AssetList(items=database.list_assets(generation_job_id=generation_job_id))

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

    @app.post("/ai_providers", response_model=AiProvider, status_code=status.HTTP_201_CREATED)
    def create_ai_provider(payload: AiProviderCreate) -> AiProvider:
        return database.create_ai_provider(payload)

    @app.get("/ai_providers", response_model=AiProviderList)
    def list_ai_providers() -> AiProviderList:
        return AiProviderList(items=database.list_ai_providers())

    @app.put("/ai_providers/{provider_id}", response_model=AiProvider)
    def update_ai_provider(provider_id: str, payload: AiProviderCreate) -> AiProvider:
        provider = database.update_ai_provider(provider_id, payload)
        if provider is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider

    @app.get("/ai_providers/{provider_id}/health", response_model=ProviderHealth)
    def get_ai_provider_health(provider_id: str) -> ProviderHealth:
        provider = database.get_ai_provider(provider_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return ProviderHealth.model_validate(provider_health(provider))

    @app.get("/ai_providers/health", response_model=ProviderHealthList)
    def list_ai_provider_health() -> ProviderHealthList:
        return ProviderHealthList(
            items=[ProviderHealth.model_validate(provider_health(provider)) for provider in database.list_ai_providers()]
        )

    return app


app = create_app()
