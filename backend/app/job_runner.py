from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.component_processing import process_ui_preview_components
from app.db import StudioDatabase
from app.schemas import AiProvider, Asset, AssetCreate, GenerationJob, GenerationJobPatch


def log_line(message: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"{timestamp} {message}"


def append_log(existing: str, message: str) -> str:
    line = log_line(message)
    return f"{existing}\n{line}" if existing else line


def parse_json_object(value: str, label: str) -> dict[str, Any]:
    try:
        data = json.loads(value or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid {label}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")
    return data


def sanitize_error(message: str) -> str:
    sanitized = message
    for key, value in os.environ.items():
        if key.endswith("_API_KEY") and value:
            sanitized = sanitized.replace(value, "[redacted]")
    return re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", sanitized)


def openai_image_size(input_data: dict[str, Any]) -> str:
    width = int(input_data.get("width") or 1024)
    height = int(input_data.get("height") or 1024)
    if width > height:
        return "1536x1024"
    if height > width:
        return "1024x1536"
    return "1024x1024"


def render_placeholder_png(
    path: Path,
    *,
    title: str,
    project_name: str,
    device_type: str,
    width: int,
    height: int,
    job_type: str,
    asset_type: str,
) -> None:
    image = Image.new("RGB", (width, height), color=(245, 248, 252))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = [
        "996 AI Asset Studio",
        title,
        f"Project: {project_name}",
        f"Device: {device_type}",
        f"Resolution: {width}x{height}",
        f"Job: {job_type}",
        f"Asset: {asset_type}",
    ]

    draw.rectangle([(16, 16), (width - 16, height - 16)], outline=(56, 86, 112), width=3)
    y = 32
    for line in lines:
        draw.text((32, y), line, fill=(24, 36, 48), font=font)
        y += 18
    image.save(path, format="PNG")


def create_thumbnail(source_path: Path, thumbnail_path: Path) -> tuple[int, int]:
    with Image.open(source_path) as image:
        image.thumbnail((320, 320))
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(thumbnail_path, format="PNG")
        return image.size


def image_dimensions(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def write_annotated_preview(source_path: Path, output_path: Path, label: str) -> None:
    with Image.open(source_path).convert("RGB") as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.rectangle([(12, 12), (image.width - 12, image.height - 12)], outline=(224, 76, 76), width=4)
        draw.text((24, 24), label, fill=(224, 76, 76), font=font)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="PNG")


def write_component_slice(source_path: Path, output_path: Path) -> tuple[int, int]:
    with Image.open(source_path).convert("RGB") as image:
        left = max(0, image.width // 4)
        top = max(0, image.height // 4)
        right = min(image.width, left + max(160, image.width // 2))
        bottom = min(image.height, top + max(120, image.height // 3))
        crop = image.crop((left, top, right, bottom))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        crop.save(output_path, format="PNG")
        return crop.size


class BaseJobRunner(ABC):
    def __init__(self, database: StudioDatabase, upload_root: Path, job: GenerationJob) -> None:
        self.database = database
        self.upload_root = upload_root
        self.job = job

    @abstractmethod
    def generate_preview(self, input_data: dict[str, Any], project_name: str, ready_dir: Path) -> Path:
        raise NotImplementedError

    @property
    @abstractmethod
    def source(self) -> str:
        raise NotImplementedError

    @property
    def start_message(self) -> str:
        return f"{self.__class__.__name__} started"

    @property
    def complete_message(self) -> str:
        return f"{self.__class__.__name__} completed"

    @property
    def fail_message(self) -> str:
        return f"{self.__class__.__name__} failed"

    def run(self) -> GenerationJob | None:
        running_logs = append_log(self.job.logs, self.start_message)
        running = self.database.update_generation_job(
            self.job.id,
            GenerationJobPatch(status="running", progress=25, logs=running_logs, error_message=""),
        )
        if running is None:
            return None
        self.job = running

        try:
            input_data = parse_json_object(running.input_json, "input_json")
            project = self.database.get_project(running.project_id) if running.project_id else None
            project_name = project.name if project else "Loose Project"
            device_type = str(input_data.get("device_type") or "mobile")
            width = int(input_data.get("width") or 1080)
            height = int(input_data.get("height") or 1920)
            ready_dir = self.upload_root / "996-ready" / running.id
            preview_dir = ready_dir / "previews"
            component_dir = ready_dir / "components"
            thumbnail_dir = ready_dir / "thumbnails"
            package_dir = ready_dir / "package"
            for directory in [preview_dir, component_dir, thumbnail_dir, package_dir]:
                directory.mkdir(parents=True, exist_ok=True)

            preview_path = self.generate_preview(input_data, project_name, ready_dir)
            preview_width, preview_height = image_dimensions(preview_path)
            assets: list[Asset] = []
            preview_asset = self.create_asset_with_thumbnail(
                asset_type="ui_preview",
                file_path=preview_path,
                thumbnail_dir=thumbnail_dir,
                device_type=device_type,
                metadata={
                    "project_name": project_name,
                    "job_type": running.job_type,
                    "generation_job_id": running.id,
                    "ready_dir": str(ready_dir),
                },
            )
            assets.append(preview_asset)

            annotated_path = preview_dir / "annotated_preview.png"
            write_annotated_preview(preview_path, annotated_path, "996 mock annotation grid")
            assets.append(
                self.create_asset_with_thumbnail(
                    asset_type="annotated_preview",
                    file_path=annotated_path,
                    thumbnail_dir=thumbnail_dir,
                    device_type=device_type,
                    metadata={"project_name": project_name, "generation_job_id": running.id},
                )
            )

            component_path = component_dir / "sliced_component.png"
            write_component_slice(preview_path, component_path)
            assets.append(
                self.create_asset_with_thumbnail(
                    asset_type="sliced_component",
                    file_path=component_path,
                    thumbnail_dir=thumbnail_dir,
                    device_type=device_type,
                    metadata={"project_name": project_name, "generation_job_id": running.id},
                )
            )
            component_processing = self.after_preview_asset(preview_asset)

            manifest = {
                "mock": isinstance(self, MockJobRunner),
                "job_id": running.id,
                "project_id": running.project_id,
                "provider_id": running.provider_id,
                "device_type": device_type,
                "resolution": [preview_width, preview_height],
                "ready_dir": str(ready_dir),
                "asset_ids": [asset.id for asset in assets],
                "assets": [
                    {
                        "id": asset.id,
                        "asset_type": asset.asset_type,
                        "file_path": asset.file_path,
                        "thumbnail_path": asset.thumbnail_path,
                    }
                    for asset in assets
                ],
            }
            if component_processing:
                manifest["component_processing"] = component_processing
            manifest_path = package_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            completed_logs = append_log(running.logs, self.complete_message)
            return self.database.update_generation_job(
                running.id,
                GenerationJobPatch(
                    status="completed",
                    progress=100,
                    output_json=json.dumps(manifest, ensure_ascii=False),
                    output_preview_path=str(preview_path),
                    error_message="",
                    logs=completed_logs,
                ),
            )
        except Exception as exc:
            failed_logs = append_log(running.logs, self.fail_message)
            error_message = sanitize_error(str(exc))
            if isinstance(self, MockJobRunner) and error_message.startswith("Invalid input_json"):
                error_message = error_message.replace("Invalid input_json", "Invalid mock input_json", 1)
            return self.database.update_generation_job(
                running.id,
                GenerationJobPatch(
                    status="failed",
                    progress=100,
                    error_message=error_message,
                    logs=failed_logs,
                ),
            )

    def create_asset_with_thumbnail(
        self,
        *,
        asset_type: str,
        file_path: Path,
        thumbnail_dir: Path,
        device_type: str,
        metadata: dict[str, Any],
    ) -> Asset:
        width, height = image_dimensions(file_path)
        thumbnail_path = thumbnail_dir / f"{file_path.stem}_thumb.png"
        create_thumbnail(file_path, thumbnail_path)
        return self.database.create_asset(
            AssetCreate(
                project_id=self.job.project_id,
                asset_type=asset_type,  # type: ignore[arg-type]
                device_type=device_type,
                width=width,
                height=height,
                file_path=str(file_path),
                original_filename=file_path.name,
                metadata_json=json.dumps(metadata, ensure_ascii=False),
                source=self.source,  # type: ignore[arg-type]
                generation_job_id=self.job.id,
                thumbnail_path=str(thumbnail_path),
            )
        )

    def after_preview_asset(self, preview_asset: Asset) -> dict[str, str | list[str]] | None:
        return None


class MockJobRunner(BaseJobRunner):
    @property
    def source(self) -> str:
        return "mock_generated"

    @property
    def start_message(self) -> str:
        return "Mock run started"

    @property
    def complete_message(self) -> str:
        return "Mock run completed"

    @property
    def fail_message(self) -> str:
        return "Mock run failed"

    def generate_preview(self, input_data: dict[str, Any], project_name: str, ready_dir: Path) -> Path:
        device_type = str(input_data.get("device_type") or "mobile")
        width = int(input_data.get("width") or 1080)
        height = int(input_data.get("height") or 1920)
        preview_path = ready_dir / "previews" / "ui_preview.png"
        render_placeholder_png(
            preview_path,
            title="MOCK GENERATED",
            project_name=project_name,
            device_type=device_type,
            width=width,
            height=height,
            job_type=self.job.job_type,
            asset_type="ui_preview",
        )
        return preview_path


class CustomJobRunner(MockJobRunner):
    @property
    def source(self) -> str:
        return "ai_generated"

    def generate_preview(self, input_data: dict[str, Any], project_name: str, ready_dir: Path) -> Path:
        preview_path = super().generate_preview(input_data, project_name, ready_dir)
        return preview_path


class RealJobRunner(BaseJobRunner):
    def __init__(
        self,
        database: StudioDatabase,
        upload_root: Path,
        job: GenerationJob,
        provider: AiProvider | None,
    ) -> None:
        super().__init__(database, upload_root, job)
        self.provider = provider

    @property
    def source(self) -> str:
        return "real_pipeline_placeholder"

    def generate_preview(self, input_data: dict[str, Any], project_name: str, ready_dir: Path) -> Path:
        prompt = str(input_data.get("prompt") or "No prompt supplied")
        device_type = str(input_data.get("device_type") or "mobile")
        width = int(input_data.get("width") or 1080)
        height = int(input_data.get("height") or 1920)
        preview_path = ready_dir / "previews" / "ui_preview.png"
        render_placeholder_png(
            preview_path,
            title=f"REAL PIPELINE PLACEHOLDER: {prompt[:72]}",
            project_name=project_name,
            device_type=device_type,
            width=width,
            height=height,
            job_type=self.job.job_type,
            asset_type="ui_preview",
        )
        return preview_path

    def run(self) -> GenerationJob | None:
        running_logs = append_log(self.job.logs, "Real UI generation started")
        running = self.database.update_generation_job(
            self.job.id,
            GenerationJobPatch(status="running", progress=35, logs=running_logs, error_message=""),
        )
        if running is None:
            return None
        self.job = running

        try:
            input_data = parse_json_object(running.input_json, "input_json")
            prompt = str(input_data.get("prompt") or "")
            style_profile_id = input_data.get("style_profile_id")
            base_panel_id = input_data.get("base_panel_id")
            reference_image_id = input_data.get("reference_image_id")
            project = self.database.get_project(running.project_id) if running.project_id else None
            project_name = project.name if project else "Loose Project"
            device_type = str(input_data.get("device_type") or "mobile")
            ready_dir = self.upload_root / "real-pipeline" / running.id
            preview_dir = ready_dir / "previews"
            thumbnail_dir = ready_dir / "thumbnails"
            preview_dir.mkdir(parents=True, exist_ok=True)
            thumbnail_dir.mkdir(parents=True, exist_ok=True)

            preview_path = self.generate_preview(input_data, project_name, ready_dir)
            asset = self.create_asset_with_thumbnail(
                asset_type="ui_preview",
                file_path=preview_path,
                thumbnail_dir=thumbnail_dir,
                device_type=device_type,
                metadata={
                    "placeholder": True,
                    "project_id": running.project_id,
                    "style_profile_id": style_profile_id,
                    "base_panel_id": base_panel_id,
                    "reference_image_id": reference_image_id,
                    "prompt": prompt,
                    "project_name": project_name,
                    "job_type": running.job_type,
                    "generation_job_id": running.id,
                    "provider_id": self.provider.id if self.provider else None,
                    "provider_type": self.provider.type if self.provider else "default",
                },
            )
            output = {
                "placeholder": True,
                "job_type": running.job_type,
                "runner": self.runner_name,
                "project_id": running.project_id,
                "style_profile_id": style_profile_id,
                "base_panel_id": base_panel_id,
                "reference_image_id": reference_image_id,
                "prompt": prompt,
                "provider_id": self.provider.id if self.provider else None,
                "provider_type": self.provider.type if self.provider else "default",
                "preview_path": str(preview_path),
                "thumbnail_path": asset.thumbnail_path,
                "asset_id": asset.id,
            }
            completed_logs = append_log(running.logs, "Real UI generation placeholder completed")
            return self.database.update_generation_job(
                running.id,
                GenerationJobPatch(
                    status="completed",
                    progress=100,
                    output_json=json.dumps(output, ensure_ascii=False),
                    output_preview_path=str(preview_path),
                    error_message="",
                    logs=completed_logs,
                ),
            )
        except Exception as exc:
            failed_logs = append_log(running.logs, "Real UI generation failed")
            return self.database.update_generation_job(
                running.id,
                GenerationJobPatch(
                    status="failed",
                    progress=100,
                    error_message=sanitize_error(str(exc)),
                    logs=failed_logs,
                ),
            )

    @property
    def runner_name(self) -> str:
        return "real_placeholder"


class OpenAIJobRunner(BaseJobRunner):
    def __init__(self, database: StudioDatabase, upload_root: Path, job: GenerationJob, provider: AiProvider) -> None:
        super().__init__(database, upload_root, job)
        self.provider = provider

    @property
    def source(self) -> str:
        return "ai_generated"

    @property
    def start_message(self) -> str:
        return f"{self.provider_label} run started"

    @property
    def complete_message(self) -> str:
        return f"{self.provider_label} run completed"

    @property
    def fail_message(self) -> str:
        return f"{self.provider_label} run failed"

    @property
    def provider_label(self) -> str:
        return "OpenAI"

    def generate_preview(self, input_data: dict[str, Any], project_name: str, ready_dir: Path) -> Path:
        config = parse_json_object(self.provider.config_json, "provider config_json")
        api_key_env = str(config.get("api_key_env") or "")
        if not api_key_env:
            raise RuntimeError(f"{self.provider_label} provider requires config_json.api_key_env")
        api_key = os.getenv(api_key_env, "")
        if not api_key:
            raise RuntimeError(f"Environment variable {api_key_env} is not set")

        model = self.image_model(config)
        output_format = "png"
        size = openai_image_size(input_data)
        prompt = str(
            input_data.get("prompt")
            or f"Create a polished game UI preview for {project_name}."
        )

        try:
            response = httpx.post(
                self.image_generation_url(config),
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "prompt": prompt,
                    "size": size,
                    "n": 1,
                    "output_format": output_format,
                },
                timeout=180,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"{self.provider_label} API request failed: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"{self.provider_label} API request failed") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"{self.provider_label} API response was not valid JSON") from exc

        data = payload.get("data")
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"{self.provider_label} response did not include image data")
        image_data = data[0]
        if not isinstance(image_data, dict):
            raise RuntimeError(f"{self.provider_label} response did not include image data")

        preview_path = ready_dir / "previews" / f"ui_preview.{output_format}"
        try:
            if image_data.get("b64_json"):
                preview_path.write_bytes(base64.b64decode(image_data["b64_json"]))
            elif image_data.get("url"):
                image_response = httpx.get(image_data["url"], timeout=180)
                image_response.raise_for_status()
                preview_path.write_bytes(image_response.content)
            else:
                raise RuntimeError(f"{self.provider_label} response did not include image data")
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Failed to save {self.provider_label} image: {exc}") from exc
        return preview_path

    def image_generation_url(self, config: dict[str, Any]) -> str:
        return "https://api.openai.com/v1/images/generations"

    def image_model(self, config: dict[str, Any]) -> str:
        return "gpt-image-1"

    def after_preview_asset(self, preview_asset: Asset) -> dict[str, str | list[str]] | None:
        return process_ui_preview_components(
            database=self.database,
            upload_root=self.upload_root,
            ui_preview=preview_asset,
        )


class OfoxJobRunner(OpenAIJobRunner):
    @property
    def provider_label(self) -> str:
        return "Ofox"

    def image_generation_url(self, config: dict[str, Any]) -> str:
        base_url = str(config.get("base_url") or "https://api.ofox.ai/v1").rstrip("/")
        return f"{base_url}/images/generations"

    def image_model(self, config: dict[str, Any]) -> str:
        return str(config.get("model") or "ofox-ui")


class OpenRouterRunner(RealJobRunner):
    @property
    def runner_name(self) -> str:
        return "openrouter"

    def run(self) -> GenerationJob | None:
        running_logs = append_log(self.job.logs, "OpenRouter runner placeholder started")
        self.job = GenerationJob.model_validate({**self.job.model_dump(), "logs": running_logs})
        completed = super().run()
        if completed is None:
            return None
        logs = append_log(completed.logs, "OpenRouter runner placeholder completed")
        return self.database.update_generation_job(completed.id, GenerationJobPatch(logs=logs))


class JobRunnerService:
    def __init__(self, database: StudioDatabase, upload_root: Path) -> None:
        self.database = database
        self.upload_root = upload_root

    def run(self, generation_job_id: str) -> GenerationJob | None:
        job = self.database.get_generation_job(generation_job_id)
        if job is None:
            return None
        provider = self.resolve_provider(job)
        runner = self.create_runner(job, provider)
        return runner.run()

    def resolve_provider(self, job: GenerationJob) -> AiProvider | None:
        if job.provider_id:
            return self.database.get_ai_provider(job.provider_id)
        enabled = [provider for provider in self.database.list_ai_providers() if provider.enabled]
        return enabled[0] if enabled else None

    def create_runner(self, job: GenerationJob, provider: AiProvider | None) -> BaseJobRunner:
        provider_type = provider.type if provider else "mock"
        if provider_type == "openrouter":
            return OpenRouterRunner(self.database, self.upload_root, job, provider)
        if provider_type == "openai":
            if provider is None:
                raise RuntimeError("OpenAI provider is not configured")
            return OpenAIJobRunner(self.database, self.upload_root, job, provider)
        if provider_type == "ofox":
            if provider is None:
                raise RuntimeError("Ofox provider is not configured")
            return OfoxJobRunner(self.database, self.upload_root, job, provider)
        if job.job_type == "real_ui_generation":
            return RealJobRunner(self.database, self.upload_root, job, provider)
        if job.job_type == "mock_ui_generation" or provider_type == "mock":
            return MockJobRunner(self.database, self.upload_root, job)
        return CustomJobRunner(self.database, self.upload_root, job)


def provider_health(provider: AiProvider) -> dict[str, str | bool]:
    if provider.type in {"mock", "custom"}:
        return {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
            "enabled": provider.enabled,
            "status": "healthy",
            "message": "Local provider is ready",
        }
    if provider.type in {"openai", "openrouter", "ofox"}:
        try:
            config = parse_json_object(provider.config_json, "provider config_json")
        except ValueError as exc:
            return {
                "id": provider.id,
                "name": provider.name,
                "type": provider.type,
                "enabled": provider.enabled,
                "status": "unhealthy",
                "message": str(exc),
            }
        api_key_env = str(config.get("api_key_env") or "")
        provider_name = {
            "openai": "OpenAI",
            "openrouter": "OpenRouter",
            "ofox": "Ofox",
        }[provider.type]
        if not api_key_env:
            return {
                "id": provider.id,
                "name": provider.name,
                "type": provider.type,
                "enabled": provider.enabled,
                "status": "unhealthy",
                "message": f"{provider_name} provider requires config_json.api_key_env",
            }
        if not os.getenv(api_key_env):
            return {
                "id": provider.id,
                "name": provider.name,
                "type": provider.type,
                "enabled": provider.enabled,
                "status": "unhealthy",
                "message": f"Environment variable {api_key_env} is not set",
            }
        return {
            "id": provider.id,
            "name": provider.name,
            "type": provider.type,
            "enabled": provider.enabled,
            "status": "healthy",
            "message": f"Environment variable {api_key_env} is configured",
        }
    return {
        "id": provider.id,
        "name": provider.name,
        "type": provider.type,
        "enabled": provider.enabled,
        "status": "unhealthy",
        "message": "Unknown provider type",
    }
