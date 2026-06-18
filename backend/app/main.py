from pathlib import Path
import json
import os
import re
import shutil
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

from app.component_processing import process_ui_preview_components
from app.db import StudioDatabase
from app.job_runner import JobRunnerService
from app.layer_package import LayerPackageError
from app.layer_package import import_layer_package
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
from scripts.main_ui_production_chain import accept_main_task_panel_candidate
from scripts.main_ui_production_chain import create_main_task_panel_package
from scripts.main_ui_production_chain import create_ui_package
from scripts.main_ui_production_chain import create_main_ui_package
from scripts.main_ui_production_chain import export_confirmed_components
from scripts.main_ui_production_chain import main_task_panel_package_response
from scripts.main_ui_production_chain import mark_candidate_components
from scripts.main_ui_production_chain import preview_main_task_panel_on_canvas
from scripts.main_ui_production_chain import select_candidate_option
from scripts.main_ui_production_chain import select_main_task_panel_candidate
from scripts.main_ui_production_chain import update_candidate_confirmation
from scripts.opencv_ui_slicer import slice_ui_image as run_opencv_ui_slicer


def main_task_panel_ai_candidate_generator(target: Path, index: int, context: dict[str, Any]) -> dict[str, Any]:
    raise RuntimeError("AI generation provider is not configured for main_task_panel")


DEFAULT_MAIN_TASK_PANEL_AI_CANDIDATE_GENERATOR = main_task_panel_ai_candidate_generator


def default_database_path() -> Path:
    configured = os.getenv("STUDIO_DATABASE_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "data" / "studio.db"


def default_upload_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "assets" / "uploads"


def default_training_samples_dir(upload_dir: str | Path | None = None) -> Path:
    configured = os.getenv("STUDIO_TRAINING_SAMPLES_DIR")
    if configured:
        return Path(configured)
    if upload_dir:
        return Path(upload_dir).parent / "training_samples"
    return Path(__file__).resolve().parents[2] / "training_samples"


def default_harness_examples_dir() -> Path:
    configured = os.getenv("STUDIO_HARNESS_EXAMPLES_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[2] / "harness" / "examples"


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
            "http://localhost:3107",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:3107",
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
    training_samples_root = default_training_samples_dir(upload_root if upload_dir else None)
    harness_examples_root = default_harness_examples_dir()
    app.state.database = database
    app.state.upload_dir = upload_root
    app.state.training_samples_dir = training_samples_root
    app.state.harness_examples_dir = harness_examples_root

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

    @app.post("/production-studio/layer-package/import")
    async def import_production_layer_package(file: UploadFile = File(...)) -> dict:
        filename = file.filename or "layer_package.zip"
        if Path(filename).suffix.lower() != ".zip":
            raise HTTPException(status_code=400, detail="Layer package must be a zip file")
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Layer package zip is empty")
        upload_dir = upload_root / "layer-packages" / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        upload_path = upload_dir / f"{Path(safe_filename(filename)).stem}-{os.urandom(4).hex()}.zip"
        upload_path.write_bytes(data)
        try:
            return import_layer_package(upload_path, upload_root)
        except LayerPackageError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    def prompt_samples_file() -> Path:
        return training_samples_root / "prompts" / "prompt_samples.json"

    def read_prompt_samples() -> dict:
        path = prompt_samples_file()
        if not path.exists():
            return {"schema_version": "1.0", "samples": []}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"schema_version": "1.0", "samples": []}
        if not isinstance(data, dict) or not isinstance(data.get("samples"), list):
            return {"schema_version": "1.0", "samples": []}
        return data

    def write_prompt_samples(payload: dict) -> None:
        path = prompt_samples_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def prompt_sample_by_type(component_type: str) -> str:
        return marking_type(component_type)

    def prompt_marking_summary(package_dir: Path, production: dict | None = None) -> dict:
        candidate_path = package_dir / "candidate_manifest.json"
        candidates: list[dict] = []
        if candidate_path.exists():
            manifest = read_package_json(package_dir, "candidate_manifest.json")
            candidates = [item for item in manifest.get("candidates", []) if isinstance(item, dict)]
        by_type = {"background": 0, "panel": 0, "button": 0, "icon": 0, "skill": 0}
        for candidate in candidates:
            by_type[prompt_sample_by_type(str(candidate.get("component_type") or ""))] += 1
        confirmed_components = []
        if production and isinstance(production.get("confirmed_components"), list):
            confirmed_components = production["confirmed_components"]
        slice_success = sum(
            1
            for item in confirmed_components
            if isinstance(item, dict) and item.get("confirmed") and item.get("file") and (package_dir / str(item["file"])).exists()
        )
        return {
            "status": "marked" if candidates else "pending",
            "total_marks": len(candidates),
            "by_type": by_type,
            "slice_success": slice_success,
        }

    def upsert_prompt_sample(package_dir: Path, payload: dict, production: dict | None = None, marking_result: dict | None = None) -> None:
        delivery_path = package_dir / "delivery_report.json"
        delivery = read_package_json(package_dir, "delivery_report.json") if delivery_path.exists() else {}
        source_note = delivery.get("source_note") if isinstance(delivery.get("source_note"), dict) else {}
        samples_payload = read_prompt_samples()
        samples = [item for item in samples_payload.get("samples", []) if isinstance(item, dict)]
        package_dir_text = str(package_dir)
        existing = next((item for item in samples if item.get("package_dir") == package_dir_text), None)
        now = utc_now()
        record = {
            **(existing or {}),
            "sample_id": (existing or {}).get("sample_id") or package_dir.name,
            "package_dir": package_dir_text,
            "created_at": (existing or {}).get("created_at") or now,
            "updated_at": now,
            "system_prompt": str(
                payload.get("system_prompt")
                or (existing or {}).get("system_prompt")
                or payload.get("requirement")
                or delivery.get("final_prompt")
                or ""
            ),
            "final_prompt": str(payload.get("requirement") or (existing or {}).get("final_prompt") or delivery.get("final_prompt") or ""),
            "project_id": str(payload.get("project_id") or (existing or {}).get("project_id") or ""),
            "interface_type": str(payload.get("interface_type") or payload.get("screen_type") or delivery.get("screen_type") or "main_ui"),
            "device_type": str(payload.get("device_type") or (existing or {}).get("device_type") or ""),
            "layout_template": str(payload.get("layout_template") or (existing or {}).get("layout_template") or ""),
            "reference_used": bool(payload.get("reference_image_path") or source_note.get("source_image")),
            "generation_result": production
            or (existing or {}).get("generation_result")
            or {"status": "generated", "package_dir": package_dir_text},
            "marking_result": marking_result or (existing or {}).get("marking_result") or {"status": "pending"},
            "accepted": bool((existing or {}).get("accepted", False)),
            "quality": str((existing or {}).get("quality") or "unreviewed"),
            "rejected_reason": str((existing or {}).get("rejected_reason") or ""),
            "manual_adjustment_note": str(payload.get("adjustment_note") or (existing or {}).get("manual_adjustment_note") or ""),
        }
        if existing:
            samples = [record if item.get("package_dir") == package_dir_text else item for item in samples]
        else:
            samples.append(record)
        samples_payload["schema_version"] = "1.0"
        samples_payload["updated_at"] = now
        samples_payload["samples"] = samples
        write_prompt_samples(samples_payload)

    def update_prompt_sample_acceptance(package_dir: Path, review_status: str, rejected_reason: str) -> None:
        samples_payload = read_prompt_samples()
        samples = [item for item in samples_payload.get("samples", []) if isinstance(item, dict)]
        package_dir_text = str(package_dir)
        changed = False
        now = utc_now()
        for sample in samples:
            if sample.get("package_dir") != package_dir_text:
                continue
            sample["accepted"] = review_status == "accepted"
            sample["quality"] = "high_quality" if review_status == "accepted" else "rejected" if review_status == "rejected" else "unreviewed"
            sample["rejected_reason"] = rejected_reason if review_status == "rejected" else ""
            sample["updated_at"] = now
            changed = True
        if changed:
            samples_payload["updated_at"] = now
            samples_payload["samples"] = samples
            write_prompt_samples(samples_payload)

    def best_prompt_sample(interface_type: str, device_type: str, layout_template: str) -> dict:
        samples = [item for item in read_prompt_samples().get("samples", []) if isinstance(item, dict)]
        matches = [
            item
            for item in samples
            if item.get("quality") == "high_quality"
            and item.get("interface_type") == interface_type
            and (not device_type or item.get("device_type") == device_type)
            and (not layout_template or item.get("layout_template") == layout_template)
        ]
        matches.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        if not matches:
            return {"found": False}
        sample = matches[0]
        return {
            "found": True,
            "sample_id": sample.get("sample_id", ""),
            "system_prompt": sample.get("system_prompt", ""),
            "final_prompt": sample.get("final_prompt", ""),
            "quality": sample.get("quality", ""),
            "updated_at": sample.get("updated_at", ""),
        }

    def generation_result_summary(production: dict) -> dict:
        return {
            "status": "generated",
            "package_dir": production.get("package_dir", ""),
            "main_ui_url": production.get("main_ui_url", ""),
            "selected_candidate_id": production.get("selected_candidate_id", ""),
            "candidate_options_count": len(production.get("candidate_options") or []),
        }

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

    def payload_reference_image(payload: dict) -> str | None:
        value = payload.get("reference_image_path")
        if value:
            return str(value)
        value = payload.get("reference_image")
        return str(value) if value else None

    def reference_influence_percent(payload: dict) -> int | None:
        value = payload.get("reference_influence_percent")
        if value is None or value == "":
            strength = str(payload.get("style_reference_strength") or "")
            value = strength if strength.isdigit() else None
        if value is None:
            return None
        try:
            return max(0, min(100, int(value)))
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="reference_influence_percent must be between 0 and 100") from None

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

    def ensure_marking_test_project() -> Project:
        for project in database.list_projects():
            if project.name == "标记验收测试" and project.description == "MARKING_TEST":
                return project
        return database.create_project(ProjectCreate(name="标记验收测试", description="MARKING_TEST", status="draft"))

    def marking_type(component_type: str) -> str:
        value = component_type.lower()
        if "skill" in value:
            return "skill"
        if "background" in value or value == "screen":
            return "background"
        if "button" in value or "joystick" in value or "slot" in value:
            return "button"
        if "icon" in value:
            return "icon"
        return "panel"

    def copy_image_as_png(source: Path, target: Path) -> None:
        from PIL import Image

        with Image.open(source) as image:
            image.save(target, format="PNG")

    def candidate_bbox(candidate: dict) -> dict:
        raw = candidate.get("bbox") or candidate.get("bounds") or {}
        return raw if isinstance(raw, dict) else {}

    def required_marking_components(candidates: list[dict]) -> tuple[list[str], list[str]]:
        requirements = {
            "top_bar": lambda item: item.get("layout_zone") == "top_info" or item.get("component_id") == "top_player_info",
            "mini_map": lambda item: item.get("layout_zone") == "right_top_map" or item.get("component_id") == "mini_map",
            "skill_area": lambda item: item.get("layout_zone") == "right_skill",
            "chat_area": lambda item: item.get("layout_zone") == "chat" or item.get("component_id") == "chat_panel",
            "joystick_area": lambda item: item.get("layout_zone") == "bottom_left_joystick" or item.get("component_id") == "left_joystick",
        }
        missing = [key for key, matcher in requirements.items() if not any(matcher(candidate) for candidate in candidates)]
        warnings = [f"missing required main_ui component: {key}" for key in missing]
        return missing, warnings

    def bbox_health_report(candidates: list[dict], image_size: tuple[int, int]) -> dict:
        image_width, image_height = image_size
        invalid_size: list[str] = []
        out_of_bounds: list[str] = []
        overlap_warnings: list[str] = []
        boxes: list[tuple[str, str, dict]] = []
        container_types = {"screen", "panel", "hud_bar", "chat", "map", "skill_bar", "decoration"}
        for candidate in candidates:
            component_id = str(candidate.get("component_id") or candidate.get("candidate_id") or "")
            box = candidate_bbox(candidate)
            x = int(box.get("x") or 0)
            y = int(box.get("y") or 0)
            width = int(box.get("width") or 0)
            height = int(box.get("height") or 0)
            if width <= 0 or height <= 0:
                invalid_size.append(component_id)
                continue
            if x < 0 or y < 0 or x + width > image_width or y + height > image_height:
                out_of_bounds.append(component_id)
            if candidate.get("component_type") != "screen" and candidate.get("level") != "C":
                boxes.append((component_id, str(candidate.get("component_type") or ""), {"x": x, "y": y, "width": width, "height": height}))
        for index, (left_id, left_type, left_box) in enumerate(boxes):
            for right_id, right_type, right_box in boxes[index + 1 :]:
                if left_type in container_types or right_type in container_types:
                    continue
                left_area = left_box["width"] * left_box["height"]
                right_area = right_box["width"] * right_box["height"]
                if left_area <= 0 or right_area <= 0:
                    continue
                ix1 = max(left_box["x"], right_box["x"])
                iy1 = max(left_box["y"], right_box["y"])
                ix2 = min(left_box["x"] + left_box["width"], right_box["x"] + right_box["width"])
                iy2 = min(left_box["y"] + left_box["height"], right_box["y"] + right_box["height"])
                intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                if intersection / min(left_area, right_area) > 0.85:
                    overlap_warnings.append(f"{left_id} overlaps {right_id}")
        return {
            "checked": len(candidates),
            "image_width": image_width,
            "image_height": image_height,
            "invalid_size": invalid_size,
            "out_of_bounds": out_of_bounds,
            "overlap_warnings": overlap_warnings,
            "invalid_size_count": len(invalid_size),
            "out_of_bounds_count": len(out_of_bounds),
            "abnormal_overlap_count": len(overlap_warnings),
            "ok": not invalid_size and not out_of_bounds and not overlap_warnings,
        }

    def inspect_slice_file(path: Path, expected_format: str) -> dict:
        result = {
            "exists": path.exists(),
            "format": expected_format,
            "png_has_transparency": False,
            "jpg_valid": False,
            "warning": "",
        }
        if not path.exists():
            result["warning"] = "slice file missing"
            return result
        try:
            from PIL import Image

            with Image.open(path) as image:
                actual_format = (image.format or "").lower()
                if expected_format == "png":
                    result["png_has_transparency"] = image_has_alpha_pixels(path)
                    if actual_format != "png":
                        result["warning"] = "png output is not a PNG file"
                    elif not result["png_has_transparency"]:
                        result["warning"] = "png output has no transparent pixels"
                elif expected_format in {"jpg", "jpeg"}:
                    result["jpg_valid"] = actual_format in {"jpeg", "jpg"} and image.width > 0 and image.height > 0
                    if not result["jpg_valid"]:
                        result["warning"] = "jpg output is invalid"
        except OSError as exc:
            result["warning"] = f"slice file unreadable: {exc}"
        return result

    def slice_health_report(package_dir: Path, confirmed_components: list) -> dict:
        checked = 0
        file_missing: list[str] = []
        png_without_alpha: list[str] = []
        jpg_invalid: list[str] = []
        details: list[dict] = []
        for component in confirmed_components:
            if not isinstance(component, dict) or not component.get("confirmed"):
                continue
            file_name = str(component.get("file") or "")
            if not file_name:
                continue
            checked += 1
            expected_format = str(component.get("format") or Path(file_name).suffix.lstrip(".")).lower()
            check = inspect_slice_file(package_dir / file_name, expected_format)
            component_id = str(component.get("component_id") or "")
            details.append({"component_id": component_id, "file": file_name, **check})
            if not check["exists"]:
                file_missing.append(component_id)
            elif expected_format == "png" and not check["png_has_transparency"]:
                png_without_alpha.append(component_id)
            elif expected_format in {"jpg", "jpeg"} and not check["jpg_valid"]:
                jpg_invalid.append(component_id)
        return {
            "checked": checked,
            "file_missing": file_missing,
            "png_without_alpha": png_without_alpha,
            "jpg_invalid": jpg_invalid,
            "file_missing_count": len(file_missing),
            "png_without_alpha_count": len(png_without_alpha),
            "jpg_invalid_count": len(jpg_invalid),
            "ok": not file_missing and not jpg_invalid,
            "details": details,
        }

    def write_marking_acceptance_outputs(package_dir: Path, production: dict, project: Project) -> dict:
        candidate_manifest = read_package_json(package_dir, "candidate_manifest.json")
        candidates = [item for item in candidate_manifest.get("candidates", []) if isinstance(item, dict)]
        confirmed_components = production.get("confirmed_components", [])
        selected_candidate_id = str(production.get("selected_candidate_id") or "candidate_1")

        by_type = {"background": 0, "panel": 0, "button": 0, "icon": 0, "skill": 0}
        for candidate in candidates:
            by_type[marking_type(str(candidate.get("component_type") or ""))] += 1
        missing_key_components, key_component_warnings = required_marking_components(candidates)

        slice_success = 0
        slice_failed = 0
        for component in confirmed_components:
            if not isinstance(component, dict) or not component.get("confirmed"):
                continue
            file_name = str(component.get("file") or "")
            if file_name and (package_dir / file_name).exists():
                slice_success += 1
            else:
                slice_failed += 1

        missing_mark_types = [key for key, value in by_type.items() if value == 0]
        image_size = (0, 0)
        try:
            from PIL import Image

            with Image.open(package_dir / "main_ui.jpg") as image:
                image_size = image.size
        except OSError:
            image_size = (0, 0)
        bbox_health = bbox_health_report(candidates, image_size)
        slice_health = slice_health_report(package_dir, confirmed_components if isinstance(confirmed_components, list) else [])
        warnings = sorted(
            {
                str(candidate.get("transparent_warning"))
                for candidate in candidates
                if isinstance(candidate.get("transparent_warning"), str) and candidate.get("transparent_warning")
            }
        )
        warnings = sorted(
            set(
                warnings
                + key_component_warnings
                + [f"missing marking type: {item}" for item in missing_mark_types]
                + [f"invalid bbox size: {item}" for item in bbox_health["invalid_size"]]
                + [f"bbox out of bounds: {item}" for item in bbox_health["out_of_bounds"]]
                + [f"abnormal bbox overlap: {item}" for item in bbox_health["overlap_warnings"]]
                + [f"slice file missing: {item}" for item in slice_health["file_missing"]]
                + [f"png output has no transparent pixels: {item}" for item in slice_health["png_without_alpha"]]
                + [f"jpg output invalid: {item}" for item in slice_health["jpg_invalid"]]
            )
        )

        harness_dir = (harness_examples_root / "main_ui" / "marking_test").resolve()
        slices_dir = harness_dir / "slices"
        harness_dir.mkdir(parents=True, exist_ok=True)
        slices_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(package_dir / "main_ui.jpg", harness_dir / "original.jpg")
        copy_image_as_png(package_dir / "candidate_preview.jpg", harness_dir / "candidate_preview.png")
        shutil.copy2(package_dir / "candidate_manifest.json", harness_dir / "marking.json")
        shutil.copy2(package_dir / "manifest.json", harness_dir / "manifest.json")
        shutil.copy2(package_dir / "manual_acceptance.json", harness_dir / "manual_acceptance.json")
        for component in confirmed_components:
            if not isinstance(component, dict) or not component.get("file"):
                continue
            source = package_dir / str(component["file"])
            if source.exists() and source.is_file():
                shutil.copy2(source, slices_dir / source.name)

        report = {
            "project_code": "MARKING_TEST",
            "candidate_id": selected_candidate_id,
            "total_marks": len(candidates),
            "background_count": by_type["background"],
            "panel_count": by_type["panel"],
            "button_count": by_type["button"],
            "icon_count": by_type["icon"],
            "skill_count": by_type["skill"],
            "by_type": by_type,
            "slice_success": slice_success,
            "slice_failed": slice_failed,
            "missing_required": missing_key_components,
            "warnings": warnings,
            "key_component_checks": {
                "required": ["top_bar", "mini_map", "skill_area", "chat_area", "joystick_area"],
                "missing": missing_key_components,
            },
            "bbox_health": bbox_health,
            "slice_health": slice_health,
            "project_id": project.id,
            "manifest_path": str(harness_dir / "manifest.json"),
            "marking_json_path": str(harness_dir / "marking.json"),
            "manual_acceptance_path": str(harness_dir / "manual_acceptance.json"),
            "training_samples_path": str(package_dir / "training_samples" / "main_ui" / "candidate_samples.json"),
            "harness_dir": str(harness_dir),
            "candidate_preview_path": str(harness_dir / "candidate_preview.png"),
        }
        (harness_dir / "marking_acceptance_report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return report

    def main_ui_package_response(package_dir: Path) -> dict:
        candidate_path = package_dir / "candidate_manifest.json"
        candidate_manifest = read_package_json(package_dir, "candidate_manifest.json") if candidate_path.exists() else {"candidates": []}
        candidates = candidate_manifest.get("candidates") if isinstance(candidate_manifest.get("candidates"), list) else []
        delivery_path = package_dir / "delivery_report.json"
        delivery_report = read_package_json(package_dir, "delivery_report.json") if delivery_path.exists() else {}
        candidate_options = []
        for item in delivery_report.get("candidate_options", []):
            if not isinstance(item, dict) or not item.get("file"):
                continue
            file_path = package_dir / str(item["file"])
            candidate_options.append(
                {
                    **item,
                    "selected": item.get("candidate_id") == delivery_report.get("selected_candidate_id", "candidate_1"),
                    "url": package_file_url(package_dir, str(item["file"])) if file_path.exists() else "",
                }
            )
        package_files = []
        for label, filename in [
            ("main_ui.jpg", "main_ui.jpg"),
            ("candidate_preview.jpg", "candidate_preview.jpg"),
            ("candidate_manifest.json", "candidate_manifest.json"),
            ("manifest.json", "manifest.json"),
            ("annotation.json", "annotation.json"),
            ("production_review.json", "production_review.json"),
            ("manual_acceptance.json", "manual_acceptance.json"),
            ("training_samples", "training_samples/main_ui/candidate_samples.json"),
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
            "candidate_options": candidate_options,
            "selected_candidate_id": delivery_report.get("selected_candidate_id", "candidate_1"),
            "style_reference_strength": delivery_report.get("style_reference_strength", ""),
            "reference_influence_percent": delivery_report.get("reference_influence_percent"),
            "style_reference_note": delivery_report.get("style_reference_note", ""),
            "project_context": {
                "project_name": "996 UI Asset Studio",
                "screen_type": delivery_report.get("screen_type", "main_ui"),
                "style_package_name": delivery_report.get("style_reference_strength", "") or "未设置",
                "style_notes": delivery_report.get("style_reference_note", ""),
                "reference_status": "已上传/已读取" if delivery_report.get("source_note", {}).get("source_image") else "未设置",
            },
            "training_samples_url": package_file_url(package_dir, "training_samples/main_ui/candidate_samples.json")
            if (package_dir / "training_samples" / "main_ui" / "candidate_samples.json").exists()
            else "",
            "opencv_output_dir": str(package_dir / "output") if (package_dir / "output").is_dir() else "",
            "opencv_candidate_preview_url": package_file_url(package_dir, "output/candidate_preview.png")
            if (package_dir / "output" / "candidate_preview.png").exists()
            else "",
            "opencv_layer_manifest_url": package_file_url(package_dir, "output/layer_manifest.json")
            if (package_dir / "output" / "layer_manifest.json").exists()
            else "",
            "opencv_slices_dir": str(package_dir / "output" / "slices") if (package_dir / "output" / "slices").is_dir() else "",
            "opencv_layer_count": len(read_package_json(package_dir / "output", "layer_manifest.json").get("layers") or [])
            if (package_dir / "output" / "layer_manifest.json").exists()
            else 0,
        }

    def main_task_panel_api_response(package_dir: Path) -> dict:
        response = main_task_panel_package_response(package_dir)
        candidates = []
        for candidate in response.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            image_path = str(candidate.get("image_path") or "")
            candidates.append(
                {
                    **candidate,
                    "image_url": package_file_url(package_dir, image_path) if image_path and (package_dir / image_path).exists() else "",
                    "preview_url": package_file_url(package_dir, image_path) if image_path and (package_dir / image_path).exists() else "",
                }
            )
        canvas_preview_path = str(response.get("canvas_preview_path") or "")
        component_file = str(response.get("component_file") or "")
        manifest_path = str(response.get("manifest_path") or "")
        component_record_path = str(response.get("component_record_path") or "")
        return {
            **response,
            "candidates": candidates,
            "canvas_preview_url": package_file_url(package_dir, canvas_preview_path)
            if canvas_preview_path and (package_dir / canvas_preview_path).exists()
            else "",
            "component_url": package_file_url(package_dir, component_file)
            if component_file and (package_dir / component_file).exists()
            else "",
            "manifest_url": package_file_url(package_dir, manifest_path)
            if manifest_path and (package_dir / manifest_path).exists()
            else "",
            "component_record_url": package_file_url(package_dir, component_record_path)
            if component_record_path and (package_dir / component_record_path).exists()
            else "",
        }

    def app_main_task_panel_ai_candidate_generator(target: Path, index: int, context: dict[str, Any]) -> dict[str, Any]:
        providers = [
            provider
            for provider in database.list_ai_providers()
            if provider.enabled and provider.type in {"openai", "ofox"}
        ]
        if not providers:
            raise RuntimeError("No enabled AI image provider is configured for main_task_panel")
        provider = providers[0]
        target.parent.mkdir(parents=True, exist_ok=True)
        prompt = str(context.get("prompt") or "")
        width = int(context.get("width") or 286)
        height = int(context.get("height") or 330)
        job = database.create_generation_job(
            GenerationJobCreate(
                project_id=None,
                provider_id=provider.id,
                job_type="real_ui_generation",
                status="pending",
                progress=0,
                input_json=json.dumps(
                    {
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "device_type": "mobile_landscape",
                        "asset_mode": "resource_production",
                        "screen_type": "main_task_panel",
                        "module_id": "main_task_panel",
                        "candidate_id": str(context.get("candidate_id") or f"main_task_panel_candidate_{index}"),
                        "transparent_requested": True,
                        "forbidden_elements": context.get("forbidden_elements") or [],
                        "negative_prompt": context.get("negative_prompt") or "",
                    },
                    ensure_ascii=False,
                ),
                output_json="",
                output_preview_path="",
                error_message="",
                logs="main_task_panel AI candidate queued",
                auto_run=False,
            )
        )
        completed = JobRunnerService(database, upload_root).run(job.id)
        if completed is None:
            raise RuntimeError("AI generation job could not be loaded")
        if completed.status != "completed":
            raise RuntimeError(completed.error_message or "AI generation job failed")
        output_preview_path = Path(completed.output_preview_path)
        if not output_preview_path.exists():
            raise RuntimeError("AI generation job did not produce an output preview")
        with Image.open(output_preview_path) as image:
            image.convert("RGBA").save(target, "PNG")
        return {
            "generation_provider": provider.name,
            "generation_provider_type": provider.type,
            "generation_job_id": completed.id,
        }

    def main_task_panel_ai_status_response() -> dict[str, Any]:
        providers = [
            provider
            for provider in database.list_ai_providers()
            if provider.enabled and provider.type in {"openai", "ofox"}
        ]
        if not providers:
            return {
                "default_provider": "",
                "provider_type": "",
                "required_env": "",
                "api_key_configured": False,
                "ai_generation_available": False,
                "mock_generation_available": True,
                "message": "No enabled AI image provider is configured. AI generation is unavailable; mock generation is still available.",
            }
        provider = providers[0]
        try:
            config = json.loads(provider.config_json or "{}")
        except json.JSONDecodeError:
            config = {}
        required_env = str(config.get("api_key_env") or "")
        api_key_configured = bool(required_env and os.getenv(required_env))
        if api_key_configured:
            message = f"AI generation is available through {provider.name}. Manual visual review is still required."
        elif required_env:
            message = f"{required_env} is not configured. AI generation is unavailable; mock generation is still available."
        else:
            message = "Provider api_key_env is not configured. AI generation is unavailable; mock generation is still available."
        return {
            "default_provider": provider.name,
            "provider_type": provider.type,
            "required_env": required_env,
            "api_key_configured": api_key_configured,
            "ai_generation_available": api_key_configured,
            "mock_generation_available": True,
            "message": message,
        }

    def opencv_source_image(package_dir: Path) -> Path:
        for filename in ["main_ui.jpg", "main_ui.png", "ui_preview.png", "original.jpg", "original.png", "candidate_preview.jpg"]:
            candidate = package_dir / filename
            if candidate.exists() and candidate.is_file():
                return candidate
        delivery_path = package_dir / "delivery_report.json"
        if delivery_path.exists():
            delivery = read_package_json(package_dir, "delivery_report.json")
            selected_file = str(delivery.get("selected_candidate_file") or "")
            if selected_file:
                selected = package_dir / selected_file
                if selected.exists() and selected.is_file():
                    return selected
        raise FileNotFoundError("No Studio candidate image found for OpenCV baseline slicing")

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

    @app.get("/production-studio/prompt-samples/best")
    def get_best_prompt_sample(interface_type: str = "main_ui", device_type: str = "", layout_template: str = "") -> dict:
        return best_prompt_sample(interface_type, device_type, layout_template)

    @app.get("/production-studio/main-task-panel/ai-status")
    def get_main_task_panel_ai_status() -> dict[str, Any]:
        return main_task_panel_ai_status_response()

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
        update_prompt_sample_acceptance(package_path, review_status, str(updated.get("remarks") or ""))
        return updated

    @app.post("/production-studio/main-ui-production/run")
    def run_main_ui_production(payload: dict | None = None) -> dict:
        try:
            source = resolve_uploaded_source_file(payload_reference_image(payload or {}))
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
            source = resolve_uploaded_source_file(payload_reference_image(payload))
            result = create_ui_package(
                upload_root=upload_root,
                screen_type=screen_type,
                source_image=source,
                requirement=str(payload.get("requirement") or ""),
                style_reference_strength=str(payload.get("style_reference_strength") or "none"),
                reference_influence_percent=reference_influence_percent(payload),
                adjustment_note=str(payload.get("adjustment_note") or ""),
                adjustment_image_path=str(payload.get("adjustment_image_path") or ""),
            )
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        package_path = resolve_production_package_dir(str(result["package_dir"]))
        response = main_ui_package_response(package_path)
        upsert_prompt_sample(
            package_path,
            {
                **payload,
                "interface_type": screen_type,
                "screen_type": screen_type,
            },
            generation_result_summary(response),
            {"status": "generated"},
        )
        return response

    @app.post("/production-studio/hud-modules/main-task-panel/generate")
    def generate_main_task_panel_candidates(payload: dict[str, Any] | None = None) -> dict:
        generation_mode = str((payload or {}).get("generation_mode") or "mock")
        ai_generator = (
            main_task_panel_ai_candidate_generator
            if main_task_panel_ai_candidate_generator is not DEFAULT_MAIN_TASK_PANEL_AI_CANDIDATE_GENERATOR
            else app_main_task_panel_ai_candidate_generator
        )
        try:
            result = create_main_task_panel_package(
                upload_root=upload_root,
                generation_mode=generation_mode,
                ai_candidate_generator=ai_generator if generation_mode.strip().lower() == "ai" else None,
            )
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        package_path = resolve_production_package_dir(str(result["package_dir"]))
        return main_task_panel_api_response(package_path)

    @app.post("/production-studio/hud-modules/main-task-panel/select")
    def select_main_task_panel_module_candidate(package_dir: str, candidate_id: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            select_main_task_panel_candidate(package_path, candidate_id)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_task_panel_api_response(package_path)

    @app.post("/production-studio/hud-modules/main-task-panel/preview")
    def preview_main_task_panel_module(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            result = preview_main_task_panel_on_canvas(package_path)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        response = main_task_panel_api_response(package_path)
        response["target_rect"] = result.get("target_rect", response.get("fixed_rect"))
        response["canvas_width"] = result.get("canvas_width")
        response["canvas_height"] = result.get("canvas_height")
        return response

    @app.post("/production-studio/hud-modules/main-task-panel/accept")
    def accept_main_task_panel_module(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            accept_main_task_panel_candidate(package_path)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_task_panel_api_response(package_path)

    @app.post("/production-studio/ui-production/select-candidate")
    def select_ui_production_candidate(package_dir: str, candidate_id: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            select_candidate_option(package_path, candidate_id)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(package_path)

    @app.post("/production-studio/ui-production/mark-candidates")
    def mark_ui_production_candidates(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            mark_candidate_components(package_path)
        except (FileNotFoundError, RuntimeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        response = main_ui_package_response(package_path)
        upsert_prompt_sample(package_path, {}, generation_result_summary(response), prompt_marking_summary(package_path, response))
        return response

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
        response = main_ui_package_response(package_path)
        marking_summary = prompt_marking_summary(package_path, response)
        marking_summary["status"] = "exported"
        upsert_prompt_sample(package_path, {}, generation_result_summary(response), marking_summary)
        return response

    @app.post("/production-studio/ui-production/opencv-slice")
    def opencv_slice_ui_production(package_dir: str) -> dict:
        package_path = resolve_production_package_dir(package_dir)
        try:
            source = opencv_source_image(package_path)
            run_opencv_ui_slicer(source, package_path / "output")
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return main_ui_package_response(package_path)

    @app.post("/production-studio/marking-acceptance-test/run")
    def run_marking_acceptance_test(payload: dict | None = None) -> dict:
        payload = payload or {}
        project = ensure_marking_test_project()
        try:
            source = resolve_uploaded_source_file(payload_reference_image(payload))
            result = create_ui_package(
                upload_root=upload_root,
                screen_type="main_ui",
                source_image=source,
                requirement=str(payload.get("requirement") or "生成一张用于996传奇引擎的主界面UI"),
                style_reference_strength=str(payload.get("style_reference_strength") or "none"),
                reference_influence_percent=reference_influence_percent(payload),
                adjustment_note=str(payload.get("adjustment_note") or "用于测试自动标记和自动切图准确性"),
                adjustment_image_path=str(payload.get("adjustment_image_path") or ""),
            )
            package_path = resolve_production_package_dir(str(result["package_dir"]))
            select_candidate_option(package_path, "candidate_1")
            mark_candidate_components(package_path)
            export_confirmed_components(package_path)
            production = main_ui_package_response(package_path)
            report = write_marking_acceptance_outputs(package_path, production, project)
            upsert_prompt_sample(
                package_path,
                {
                    **payload,
                    "project_id": payload.get("project_id") or project.id,
                    "interface_type": "main_ui",
                    "screen_type": "main_ui",
                },
                generation_result_summary(production),
                report,
            )
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            **report,
            "project": project.model_dump(),
            "candidate_preview_url": production.get("candidate_preview_url", ""),
            "report_path": str(Path(report["harness_dir"]) / "marking_acceptance_report.json"),
            "production": production,
        }

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
