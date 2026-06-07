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
from scripts.analyze_production_package import analyze_package, utc_now
from scripts.main_ui_production_chain import create_ui_package
from scripts.main_ui_production_chain import create_main_ui_package
from scripts.main_ui_production_chain import export_confirmed_components
from scripts.main_ui_production_chain import mark_candidate_components
from scripts.main_ui_production_chain import update_candidate_confirmation


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

    def resolve_production_package_dir(package_dir: str) -> Path:
        raw_path = Path(package_dir)
        upload_root_resolved = upload_root.resolve()
        if raw_path.is_absolute():
            candidate = raw_path.resolve()
        else:
            parts = raw_path.parts
            if "996-ready" in parts:
                candidate = (upload_root / Path(*parts[parts.index("996-ready"):])).resolve()
            else:
                candidate = (upload_root / raw_path).resolve()
        if not candidate.is_relative_to(upload_root_resolved):
            raise HTTPException(status_code=400, detail="Package path must stay inside upload root")
        if not candidate.exists() or not candidate.is_dir():
            raise HTTPException(status_code=404, detail="Production package not found")
        return candidate

    def read_package_json(package_dir: Path, filename: str) -> dict:
        path = package_dir / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"{filename} not found")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"{filename} is invalid JSON") from exc
        return data if isinstance(data, dict) else {}

    def pending_manual_acceptance() -> dict:
        return {
            "schema_version": "1.0",
            "review_status": "pending",
            "reviewer": "",
            "remarks": "",
            "updated_at": utc_now(),
            "accepted_at": None,
            "accepted_by": "",
            "components": [],
        }

    def package_file_url(package_dir: Path, filename: str) -> str:
        relative_package = package_dir.resolve().relative_to(upload_root.resolve())
        return "/production-studio/files/" + (relative_package / filename).as_posix()

    def resolve_uploaded_source_file(file_path: str | None) -> Path | None:
        if not file_path:
            return None
        raw_path = Path(file_path)
        upload_root_resolved = upload_root.resolve()
        candidate = raw_path.resolve() if raw_path.is_absolute() else (Path.cwd() / raw_path).resolve()
        if not candidate.is_relative_to(upload_root_resolved):
            raise HTTPException(status_code=400, detail="Reference image must stay inside upload root")
        if not candidate.exists() or not candidate.is_file():
            raise HTTPException(status_code=404, detail="Reference image not found")
        return candidate

    def image_has_alpha_pixels(path: Path) -> bool:
        if not path.exists() or path.suffix.lower() != ".png":
            return False
        try:
            from PIL import Image

            with Image.open(path) as image:
                alpha = image.convert("RGBA").getchannel("A")
                minimum, _ = alpha.getextrema()
                return minimum < 255
        except OSError:
            return False

    def main_ui_package_response(package_dir: Path) -> dict:
        candidate_path = package_dir / "candidate_manifest.json"
        candidate_manifest = read_package_json(package_dir, "candidate_manifest.json") if candidate_path.exists() else {"candidates": []}
        candidates = candidate_manifest.get("candidates") if isinstance(candidate_manifest.get("candidates"), list) else []
        package_files = []
        for label, filename in [
            ("main_ui.jpg", "main_ui.jpg"),
            ("candidate_preview.jpg", "candidate_preview.jpg"),
            ("candidate_manifest.json", "candidate_manifest.json"),
            ("manifest.json", "manifest.json"),
            ("annotation.json", "annotation.json"),
            ("production_review.json", "production_review.json"),
            ("manual_acceptance.json", "manual_acceptance.json"),
        ]:
            file_path = package_dir / filename
            package_files.append(
                {
                    "label": label,
                    "file": filename,
                    "exists": file_path.exists(),
                    "url": package_file_url(package_dir, filename) if file_path.exists() else "",
                }
            )
        confirmed_dir = package_dir / "confirmed_components"
        confirmed_screen = confirmed_dir / "screen_main_ui.jpg"
        package_files.append(
            {
                "label": "confirmed_components/",
                "file": "confirmed_components/",
                "exists": confirmed_dir.is_dir(),
                "url": package_file_url(package_dir, "confirmed_components/screen_main_ui.jpg") if confirmed_screen.exists() else "",
            }
        )
        confirmed_components = [
            {
                "component_id": candidate.get("component_id") or candidate.get("candidate_id"),
                "component_type": candidate.get("component_type") or candidate.get("candidate_type"),
                "number": candidate.get("number"),
                "confirmed": bool(candidate.get("confirmed")),
                "file": candidate.get("image_path") or "",
                "format": candidate.get("output_format") or "",
                "transparent_required": bool(candidate.get("transparent_required")),
                "has_transparent_pixels": image_has_alpha_pixels(package_dir / str(candidate.get("image_path") or "")),
                "transparent_warning": candidate.get("transparent_warning") or "",
                "url": package_file_url(package_dir, str(candidate["image_path"])) if candidate.get("image_path") else "",
            }
            for candidate in candidates
            if isinstance(candidate, dict)
        ]
        candidate_preview_path = package_dir / "candidate_preview.jpg"
        review_path = package_dir / "production_review.json"
        manual_path = package_dir / "manual_acceptance.json"
        manifest_path = package_dir / "manifest.json"
        annotation_path = package_dir / "annotation.json"
        return {
            "package_dir": str(package_dir),
            "main_ui_url": package_file_url(package_dir, "main_ui.jpg"),
            "candidate_preview_url": package_file_url(package_dir, "candidate_preview.jpg") if candidate_preview_path.exists() else "",
            "candidate_manifest_url": package_file_url(package_dir, "candidate_manifest.json") if candidate_path.exists() else "",
            "manifest_url": package_file_url(package_dir, "manifest.json") if manifest_path.exists() else "",
            "annotation_url": package_file_url(package_dir, "annotation.json") if annotation_path.exists() else "",
            "production_review_url": package_file_url(package_dir, "production_review.json") if review_path.exists() else "",
            "manual_acceptance_url": package_file_url(package_dir, "manual_acceptance.json") if manual_path.exists() else "",
            "confirmed_components_url": package_file_url(package_dir, "confirmed_components/screen_main_ui.jpg")
            if (package_dir / "confirmed_components" / "screen_main_ui.jpg").exists()
            else "",
            "candidates": candidates,
            "confirmed_components": confirmed_components,
            "package_files": package_files,
        }

    @app.post("/production-studio/analyze")
    def analyze_production_studio_package(package_dir: str) -> dict[str, str]:
        package_path = resolve_production_package_dir(package_dir)
        try:
            return analyze_package(package_path)
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/production-studio/production-review")
    def get_production_review(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        return read_package_json(package_path, "production_review.json")

    @app.get("/production-studio/component-review")
    def get_component_review(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        return read_package_json(package_path, "component_review_analysis.json")

    @app.get("/production-studio/manual-acceptance")
    def get_manual_acceptance(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        path = package_path / "manual_acceptance.json"
        if not path.exists():
            return pending_manual_acceptance()
        return read_package_json(package_path, "manual_acceptance.json")

    @app.put("/production-studio/manual-acceptance")
    def update_manual_acceptance(package_dir: str, payload: dict) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        existing = pending_manual_acceptance()
        path = package_path / "manual_acceptance.json"
        if path.exists():
            existing.update(read_package_json(package_path, "manual_acceptance.json"))
        review_status = str(payload.get("review_status") or existing.get("review_status") or "pending")
        if review_status not in {"pending", "accepted", "rejected"}:
            raise HTTPException(status_code=400, detail="review_status must be pending, accepted, or rejected")
        reviewer = str(payload.get("reviewer") if payload.get("reviewer") is not None else existing.get("reviewer") or "")
        updated = {
            **existing,
            "review_status": review_status,
            "reviewer": reviewer,
            "remarks": str(payload.get("remarks") if payload.get("remarks") is not None else existing.get("remarks") or ""),
            "updated_at": utc_now(),
        }
        if "components" in payload and isinstance(payload["components"], list):
            updated["components"] = payload["components"]
        if review_status == "accepted":
            updated["accepted_at"] = updated.get("accepted_at") or utc_now()
            updated["accepted_by"] = str(payload.get("accepted_by") or reviewer or existing.get("accepted_by") or "")
        else:
            updated["accepted_at"] = None
            updated["accepted_by"] = ""
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8")
        return updated

    @app.post("/production-studio/main-ui-production/run")
    def run_main_ui_production(payload: dict | None = None) -> dict:
        try:
            source = resolve_uploaded_source_file((payload or {}).get("reference_image_path"))
            result = create_main_ui_package(upload_root=upload_root, source_image=source)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        package_path = resolve_production_package_dir(str(result["package_dir"]))
        response = main_ui_package_response(package_path)
        response["exported_count"] = result.get("exported_count", 0)
        return response

    @app.post("/production-studio/ui-production/generate")
    def generate_ui_production_package(payload: dict) -> dict:
        screen_type = str(payload.get("screen_type") or "main_ui")
        if screen_type != "main_ui":
            return {
                "status": "placeholder",
                "screen_type": screen_type,
                "message": "该界面类型即将支持，本轮仅 main_ui 可完整跑通",
            }
        try:
            source = resolve_uploaded_source_file(payload.get("reference_image_path"))
            result = create_ui_package(
                upload_root=upload_root,
                screen_type=screen_type,
                source_image=source,
                requirement=str(payload.get("requirement") or ""),
                style_reference_strength=str(payload.get("style_reference_strength") or "none"),
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(resolve_production_package_dir(str(result["package_dir"])))

    @app.post("/production-studio/ui-production/mark-candidates")
    def mark_ui_production_candidates(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            mark_candidate_components(package_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(package_path)

    @app.put("/production-studio/ui-production/candidate")
    def update_ui_production_candidate(package_dir: str, candidate_id: str, payload: dict) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        if "confirmed" not in payload:
            raise HTTPException(status_code=400, detail="confirmed is required")
        try:
            return update_candidate_confirmation(package_path, candidate_id, bool(payload["confirmed"]))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/production-studio/ui-production/export")
    def export_ui_production_components(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            export_confirmed_components(package_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(package_path)

    @app.get("/production-studio/main-ui-production")
    def get_main_ui_production(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        return main_ui_package_response(package_path)

    @app.put("/production-studio/main-ui-production/candidate")
    def update_main_ui_candidate(package_dir: str, candidate_id: str, payload: dict) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        if "confirmed" not in payload:
            raise HTTPException(status_code=400, detail="confirmed is required")
        try:
            candidate = update_candidate_confirmation(package_path, candidate_id, bool(payload["confirmed"]))
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return candidate

    @app.post("/production-studio/main-ui-production/export")
    def export_main_ui_confirmed_components(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            export_confirmed_components(package_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(package_path)

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
