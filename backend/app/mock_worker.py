from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.db import StudioDatabase
from app.schemas import AssetCreate, GenerationJob, GenerationJobPatch


def log_line(message: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return f"{timestamp} {message}"


def append_log(existing: str, message: str) -> str:
    line = log_line(message)
    return f"{existing}\n{line}" if existing else line


def render_placeholder_png(
    path: Path,
    *,
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
        "MOCK GENERATED",
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


def run_mock_generation(
    database: StudioDatabase,
    upload_root: Path,
    generation_job_id: str,
) -> GenerationJob | None:
    job = database.get_generation_job(generation_job_id)
    if job is None:
        return None

    running_logs = append_log(job.logs, "Mock run started")
    running = database.update_generation_job(
        generation_job_id,
        GenerationJobPatch(status="running", progress=35, logs=running_logs, error_message=""),
    )
    if running is None:
        return None

    try:
        input_data = json.loads(running.input_json or "{}")
        if not isinstance(input_data, dict):
            raise ValueError("input_json must be an object")
    except (json.JSONDecodeError, ValueError) as exc:
        failed_logs = append_log(running.logs, "Mock run failed")
        return database.update_generation_job(
            generation_job_id,
            GenerationJobPatch(
                status="failed",
                progress=100,
                error_message=f"Invalid mock input_json: {exc}",
                logs=failed_logs,
            ),
        )

    project = database.get_project(running.project_id) if running.project_id else None
    project_name = project.name if project else "Loose Mock Project"
    device_type = str(input_data.get("device_type") or "mobile")
    width = int(input_data.get("width") or 1080)
    height = int(input_data.get("height") or 1920)
    asset_specs = [
        ("ui_preview", width, height),
        ("annotated_preview", width, height),
        ("sliced_component", max(160, width // 3), max(120, height // 4)),
    ]

    job_dir = upload_root / "mock" / generation_job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    created_assets = []
    for asset_type, asset_width, asset_height in asset_specs:
        filename = f"{asset_type}.png"
        file_path = job_dir / filename
        render_placeholder_png(
            file_path,
            project_name=project_name,
            device_type=device_type,
            width=asset_width,
            height=asset_height,
            job_type=running.job_type,
            asset_type=asset_type,
        )
        asset = database.create_asset(
            AssetCreate(
                project_id=running.project_id,
                asset_type=asset_type,  # type: ignore[arg-type]
                device_type=device_type,
                width=asset_width,
                height=asset_height,
                file_path=str(file_path),
                original_filename=filename,
                metadata_json=json.dumps(
                    {
                        "mock": True,
                        "project_name": project_name,
                        "job_type": running.job_type,
                        "generation_job_id": generation_job_id,
                    },
                    ensure_ascii=False,
                ),
                source="mock_generated",
                generation_job_id=generation_job_id,
            )
        )
        created_assets.append(asset)

    output = {
        "mock": True,
        "asset_ids": [asset.id for asset in created_assets],
        "assets": [
            {
                "id": asset.id,
                "asset_type": asset.asset_type,
                "file_path": asset.file_path,
                "width": asset.width,
                "height": asset.height,
            }
            for asset in created_assets
        ],
    }
    completed_logs = append_log(running.logs, "Mock run completed")
    return database.update_generation_job(
        generation_job_id,
        GenerationJobPatch(
            status="completed",
            progress=100,
            output_json=json.dumps(output, ensure_ascii=False),
            error_message="",
            logs=completed_logs,
        ),
    )
