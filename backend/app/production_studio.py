from __future__ import annotations

import json
import html
import sys
from pathlib import Path
from typing import Any

from app.schemas import (
    ProductionStudioRequest,
    ProductionStudioResponse,
    ProductionStudioScreenResult,
    ProductionStudioStyleCode,
)

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_screen_with_style import generate_screen_with_style
from scripts.analyze_production_package import analyze_package
from scripts.master_style_workflow import run_master_style_workflow
from scripts.validate_996_export import validate_package


SEMANTIC_ICON_IDS = {
    "bag",
    "role",
    "skill",
    "shop",
    "activity",
    "settings",
    "close",
    "back",
    "confirm",
    "cancel",
}


LAYOUT_TEMPLATE_LABELS = {
    "classic_legend_mobile": "经典传奇手游布局",
    "legend_176": "1.76经典版",
    "legend_185_combo": "1.85合击版",
    "silent_version": "沉默版本",
    "hot_blood": "热血版本",
}

FIXED_LAYOUT_RULES = (
    "手机横屏传奇手游界面，采用经典传奇手游固定布局：左下摇杆区、右下环绕式技能操作区、"
    "右上小地图区、顶部信息区、底部状态信息区、右侧系统入口区、左下聊天区。"
    "保持布局稳定，只改变美术风格、按钮材质、边框纹饰和整体色调。"
)


def final_prompt_for_payload(payload: ProductionStudioRequest) -> str:
    prompt = payload.prompt.strip() or FIXED_LAYOUT_RULES
    template_label = LAYOUT_TEMPLATE_LABELS.get(payload.layout_template, payload.layout_template)
    return f"{prompt}\n布局模板：{template_label}\n固定布局规则已应用：{FIXED_LAYOUT_RULES}"


def record_generation_context(
    package_dir: str | Path,
    *,
    layout_template: str,
    generation_mode: str,
    reference_image_path: str | None,
    final_prompt: str,
) -> None:
    package_path = Path(package_dir)
    if not package_path.is_absolute():
        package_path = ROOT / package_path
    context = {
        "layout_template": layout_template,
        "generation_mode": generation_mode,
        "reference_image_path": reference_image_path,
        "final_prompt": final_prompt,
        "fixed_layout_rules_applied": True,
    }
    for name in ["manifest.json", "annotation.json", "delivery_report.json"]:
        path = package_path / name
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.update(context)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    html_path = package_path / "delivery_report.html"
    if html_path.exists():
        html_text = html_path.read_text(encoding="utf-8")
        context_html = (
            "<h2>Sprint 19 generation context</h2>"
            f"<p>layout_template: <code>{html.escape(layout_template)}</code></p>"
            f"<p>generation_mode: <code>{html.escape(generation_mode)}</code></p>"
            f"<p>reference_image_path: <code>{html.escape(reference_image_path or '')}</code></p>"
            f"<p>fixed_layout_rules_applied: <code>true</code></p>"
        )
        if "</body>" in html_text:
            html_text = html_text.replace("</body>", context_html + "</body>")
        else:
            html_text += context_html
        html_path.write_text(html_text, encoding="utf-8")


def list_style_codes(style_root: str | Path | None = None) -> list[ProductionStudioStyleCode]:
    root = Path(style_root) if style_root else ROOT / "style_codes"
    if not root.exists():
        return []

    items: list[ProductionStudioStyleCode] = []
    for style_dir in sorted(path for path in root.iterdir() if path.is_dir() and path.name.startswith("STYLE_")):
        style_json = style_dir / "style.json"
        data: dict[str, Any] = {}
        if style_json.exists():
            try:
                parsed = json.loads(style_json.read_text(encoding="utf-8"))
                if isinstance(parsed, dict):
                    data = parsed
            except json.JSONDecodeError:
                data = {}
        items.append(
            ProductionStudioStyleCode(
                style_code=str(data.get("style_code") or style_dir.name),
                style_name=str(data.get("style_name") or style_dir.name),
                source_job_id=str(data.get("source_job_id") or ""),
                device_type=str(data.get("device_type") or ""),
            )
        )
    return items


def package_file_url(package_dir: Path, upload_root: Path, filename: str) -> str:
    try:
        relative_package = package_dir.resolve().relative_to(upload_root.resolve())
    except ValueError:
        relative_package = Path(package_dir.as_posix())
    return "/production-studio/files/" + (relative_package / filename).as_posix()


def has_semantic_icons(manifest: dict[str, Any], candidate_manifest: dict[str, Any]) -> bool:
    names: set[str] = set()
    for component in manifest.get("components") or []:
        if isinstance(component, dict):
            names.add(str(component.get("component_id") or "").lower())
            names.add(str(component.get("component_name_zh") or "").lower())
    for candidate in candidate_manifest.get("candidates") or []:
        if isinstance(candidate, dict):
            names.add(str(candidate.get("candidate_id") or "").lower())
            names.add(str(candidate.get("candidate_type") or "").lower())
    return all(any(icon in name for name in names) for icon in SEMANTIC_ICON_IDS)


def read_package_json(package_dir: Path, filename: str) -> dict[str, Any]:
    path = package_dir / filename
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def summarize_package(package_dir: str | Path, upload_root: str | Path, screen_type: str) -> ProductionStudioScreenResult:
    package_path = Path(package_dir)
    if not package_path.is_absolute():
        package_path = ROOT / package_path
    upload_path = Path(upload_root)
    if not upload_path.is_absolute():
        upload_path = ROOT / upload_path

    manifest = json.loads((package_path / "manifest.json").read_text(encoding="utf-8"))
    candidate_manifest = json.loads((package_path / "candidate_manifest.json").read_text(encoding="utf-8"))
    validation = validate_package(package_path)
    semantic_icons_ready = has_semantic_icons(manifest, candidate_manifest)
    production_review_warning = ""
    try:
        analyze_package(package_path)
    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
        production_review_warning = str(exc)
    production_review = read_package_json(package_path, "production_review.json")
    manual_acceptance = read_package_json(package_path, "manual_acceptance.json")
    return ProductionStudioScreenResult(
        screen_type=screen_type,  # type: ignore[arg-type]
        generation_job_id=str(manifest.get("generation_job_id") or package_path.name),
        status="completed" if validation["ok"] else "failed",
        package_dir=str(package_path.relative_to(ROOT) if package_path.is_relative_to(ROOT) else package_path).replace("\\", "/"),
        ui_preview_url=package_file_url(package_path, upload_path, "ui_preview.png"),
        delivery_report_url=package_file_url(package_path, upload_path, "delivery_report.html"),
        candidate_preview_url=package_file_url(package_path, upload_path, "candidate_preview.html"),
        component_quality_report_url=package_file_url(package_path, upload_path, "component_quality_report.html"),
        components_count=len(manifest.get("components") or []),
        candidates_count=len(candidate_manifest.get("candidates") or []),
        validator_ok=bool(validation["ok"]),
        missing_semantic_icons=not semantic_icons_ready,
        common_icons_note=(
            "common_icons semantic naming is complete"
            if semantic_icons_ready
            else "common_icons semantic naming still needs improvement; current slices are generic candidates."
        ),
        production_review=production_review,
        manual_acceptance_status=str(manual_acceptance.get("review_status") or "pending"),
        production_review_url=package_file_url(package_path, upload_path, "production_review.json"),
        component_review_url=package_file_url(package_path, upload_path, "component_review_analysis.json"),
        manual_acceptance_url=package_file_url(package_path, upload_path, "manual_acceptance.json"),
        production_review_html_url=package_file_url(package_path, upload_path, "production_review.html"),
        production_review_warning=production_review_warning,
    )


def run_production_studio(
    *,
    payload: ProductionStudioRequest,
    database_path: str | Path,
    upload_root: str | Path,
    style_root: str | Path | None = None,
) -> ProductionStudioResponse:
    style_root_path = Path(style_root) if style_root else ROOT / "style_codes"
    upload_path = Path(upload_root)
    if not upload_path.is_absolute():
        upload_path = ROOT / upload_path
    database_path_value = Path(database_path)
    if not database_path_value.is_absolute():
        database_path_value = ROOT / database_path_value

    results: list[ProductionStudioScreenResult] = []
    style_code = payload.style_code or ""
    generated_screen_types: set[str] = set()
    final_prompt = final_prompt_for_payload(payload)
    reference_image = payload.reference_image_path if payload.generation_mode == "reference_guided" else None

    if payload.style_source == "new_style":
        master = run_master_style_workflow(
            screen_generation_mode=payload.generation_mode,
            style_name=payload.style_name,
            prompt=final_prompt,
            reference_image=reference_image,
            style_root=style_root_path,
            database_path=database_path_value,
            upload_root=upload_path,
            device_type=payload.device_type,
            asset_mode=payload.asset_mode,
        )
        style_code = str(master["style_code"])
        record_generation_context(
            master["package_dir"],
            layout_template=payload.layout_template,
            generation_mode=payload.generation_mode,
            reference_image_path=reference_image,
            final_prompt=final_prompt,
        )
        if master.get("style_dir"):
            record_generation_context(
                master["style_dir"],
                layout_template=payload.layout_template,
                generation_mode=payload.generation_mode,
                reference_image_path=reference_image,
                final_prompt=final_prompt,
            )
        results.append(summarize_package(master["package_dir"], upload_path, "main_ui"))
        generated_screen_types.add("main_ui")

    for screen_type in payload.screen_types:
        if screen_type in generated_screen_types:
            continue
        generated = generate_screen_with_style(
            style_code=style_code,
            screen_type=screen_type,
            reference_image=reference_image,
            user_prompt=final_prompt,
            style_root=style_root_path,
            database_path=database_path_value,
            upload_root=upload_path,
            device_type=payload.device_type,
            asset_mode=payload.asset_mode,
        )
        record_generation_context(
            generated["package_dir"],
            layout_template=payload.layout_template,
            generation_mode=payload.generation_mode,
            reference_image_path=reference_image,
            final_prompt=final_prompt,
        )
        results.append(summarize_package(generated["package_dir"], upload_path, screen_type))

    return ProductionStudioResponse(
        style_code=style_code,
        device_type=payload.device_type,
        asset_mode=payload.asset_mode,
        style_source=payload.style_source,
        layout_template=payload.layout_template,
        generation_mode=payload.generation_mode,
        reference_image_path=reference_image,
        final_prompt=final_prompt,
        results=results,
    )
