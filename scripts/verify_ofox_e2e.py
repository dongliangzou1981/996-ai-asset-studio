from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from setup_ofox_provider import (
    DEFAULT_API_BASE,
    DEFAULT_OFOX_BASE_URL,
    DEFAULT_OFOX_MODEL,
    DEFAULT_PROVIDER_NAME,
    ensure_default_ofox_provider,
    request_json,
)


VERIFY_PROJECT_NAME = "Sprint8C-Ofox-E2E"
VERIFY_PROMPT = (
    "生成一张移动端游戏主界面 UI，包含底部主功能栏、左侧状态栏、右侧菜单栏、小地图、聊天区域和技能区域。"
)
REQUIRED_ANNOTATION_FIELDS = ["组件名称", "组件类型", "X坐标", "Y坐标", "宽度", "高度", "字体", "字号", "字体颜色"]


def ensure_ofox_key_present() -> None:
    if not os.getenv("OFOX_API_KEY"):
        raise RuntimeError("OFOX_API_KEY is not set in this terminal. Set it before running the E2E script.")


def ensure_project(api_base: str) -> dict[str, Any]:
    projects = request_json("GET", api_base, "/projects").get("items", [])
    for project in projects:
        if project.get("name") == VERIFY_PROJECT_NAME:
            return project
    return request_json(
        "POST",
        api_base,
        "/projects",
        {
            "name": VERIFY_PROJECT_NAME,
            "description": "Sprint 8C local Ofox E2E verification project",
            "status": "active",
        },
    )


def create_real_ui_job(api_base: str, project_id: str, provider_id: str) -> dict[str, Any]:
    input_json = {
        "project_id": project_id,
        "style_profile_id": "",
        "base_panel_id": "",
        "reference_image_id": "",
        "prompt": VERIFY_PROMPT,
        "device_type": "mobile",
        "width": 1024,
        "height": 1024,
    }
    return request_json(
        "POST",
        api_base,
        "/generation_jobs",
        {
            "project_id": project_id,
            "provider_id": provider_id,
            "job_type": "real_ui_generation",
            "status": "pending",
            "progress": 0,
            "input_json": json.dumps(input_json, ensure_ascii=False),
            "output_json": "",
            "output_preview_path": "",
            "error_message": "",
            "logs": "Sprint 8C Ofox E2E queued",
            "auto_run": False,
        },
    )


def read_json_file(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise RuntimeError(f"Expected file does not exist: {file_path}")
    return json.loads(file_path.read_text(encoding="utf-8"))


def require_file(path: str, label: str) -> None:
    if not Path(path).exists():
        raise RuntimeError(f"Missing {label}: {path}")


def verify_outputs(completed_job: dict[str, Any], result_assets: list[dict[str, Any]]) -> dict[str, Any]:
    if completed_job.get("status") != "completed":
        raise RuntimeError(
            "Ofox job did not complete. "
            f"status={completed_job.get('status')} error={completed_job.get('error_message')} logs={completed_job.get('logs')}"
        )

    output = json.loads(completed_job.get("output_json") or "{}")
    ui_assets = [
        asset
        for asset in result_assets
        if asset.get("asset_type") == "ui_preview" and asset.get("source") == "ai_generated"
    ]
    component_assets = [
        asset
        for asset in result_assets
        if asset.get("asset_type") == "sliced_component" and asset.get("source") == "component_processing"
    ]
    if not ui_assets:
        raise RuntimeError("No ai_generated ui_preview asset was created")
    if len(component_assets) < 6:
        raise RuntimeError(f"Expected at least 6 sliced_component assets, got {len(component_assets)}")

    require_file(ui_assets[0]["file_path"], "ui_preview")
    component_processing = output.get("component_processing") or {}
    manifest_path = component_processing.get("manifest_path")
    annotation_path = component_processing.get("annotation_path")
    preview_html_path = component_processing.get("preview_html_path")
    if not manifest_path or not annotation_path or not preview_html_path:
        raise RuntimeError("Job output_json does not include component processing paths")

    manifest = read_json_file(manifest_path)
    annotation = read_json_file(annotation_path)
    require_file(preview_html_path, "preview.html")

    manifest_components = manifest.get("components") or []
    annotation_components = annotation.get("components") or []
    if len(manifest_components) < 6:
        raise RuntimeError(f"Expected at least 6 manifest components, got {len(manifest_components)}")
    if len(annotation_components) < 6:
        raise RuntimeError(f"Expected at least 6 annotation components, got {len(annotation_components)}")
    if not all(component.get("component_name_zh") for component in manifest_components):
        raise RuntimeError("manifest.json is missing Chinese component names")

    first_annotation = annotation_components[0]
    missing_fields = [field for field in REQUIRED_ANNOTATION_FIELDS if field not in first_annotation]
    if missing_fields:
        raise RuntimeError(f"annotation.json is missing Chinese fields: {', '.join(missing_fields)}")

    preview_html = Path(preview_html_path).read_text(encoding="utf-8")
    if "主功能栏" not in preview_html:
        raise RuntimeError("preview.html does not include Chinese component names")

    for asset in component_assets[:6]:
        require_file(asset["file_path"], f"component {asset['original_filename']}")

    return {
        "job_id": completed_job["id"],
        "ui_preview_path": ui_assets[0]["file_path"],
        "manifest_path": manifest_path,
        "annotation_path": annotation_path,
        "preview_html_path": preview_html_path,
        "component_count": len(component_assets),
        "manifest_sample": manifest_components[0],
        "annotation_sample": first_annotation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local real Ofox E2E verification through the backend API.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help=f"Backend API base URL. Default: {DEFAULT_API_BASE}")
    parser.add_argument("--provider-name", default=DEFAULT_PROVIDER_NAME, help=f"Provider name. Default: {DEFAULT_PROVIDER_NAME}")
    parser.add_argument("--base-url", default=DEFAULT_OFOX_BASE_URL, help=f"Ofox base URL. Default: {DEFAULT_OFOX_BASE_URL}")
    parser.add_argument("--model", default=DEFAULT_OFOX_MODEL, help=f"Ofox image model. Default: {DEFAULT_OFOX_MODEL}")
    parser.add_argument("--timeout", type=int, default=240, help="HTTP timeout in seconds for the generation run.")
    args = parser.parse_args()

    try:
        ensure_ofox_key_present()
        provider = ensure_default_ofox_provider(
            args.api_base,
            args.provider_name,
            base_url=args.base_url,
            model=args.model,
        )
        health = request_json("GET", args.api_base, f"/ai_providers/{provider['id']}/health")
        if health.get("status") != "healthy":
            raise RuntimeError(
                "Ofox provider is not healthy in the backend process. "
                f"health={health.get('status')} message={health.get('message')}"
            )

        project = ensure_project(args.api_base)
        job = create_real_ui_job(args.api_base, project["id"], provider["id"])
        completed = request_json("POST", args.api_base, f"/generation_jobs/{job['id']}/run", timeout=args.timeout)
        results = request_json("GET", args.api_base, f"/generation_jobs/{job['id']}/results").get("items", [])
        verified = verify_outputs(completed, results)
    except RuntimeError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1

    print("[ok] Sprint 8C Ofox real E2E verification passed")
    print(f"provider_id={provider['id']}")
    print(f"project_id={project['id']}")
    print(f"job_id={verified['job_id']}")
    print(f"ui_preview={verified['ui_preview_path']}")
    print(f"manifest={verified['manifest_path']}")
    print(f"annotation={verified['annotation_path']}")
    print(f"preview_html={verified['preview_html_path']}")
    print(f"component_count={verified['component_count']}")
    print("manifest_sample=" + json.dumps(verified["manifest_sample"], ensure_ascii=False))
    print("annotation_sample=" + json.dumps(verified["annotation_sample"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
