from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any
from uuid import uuid4


class LayerPackageError(ValueError):
    pass


def _safe_member_path(root: Path, member_name: str) -> Path:
    if member_name.endswith("/"):
        return root
    candidate = (root / member_name).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise LayerPackageError(f"Unsafe zip member path: {member_name}")
    return candidate


def _extract_zip(zip_path: Path, target_dir: Path) -> None:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue
                target = _safe_member_path(target_dir, member.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
    except zipfile.BadZipFile as exc:
        raise LayerPackageError("Layer package must be a valid zip file") from exc


def _first_existing(root: Path, *relative_paths: str) -> Path | None:
    for relative_path in relative_paths:
        candidate = root / relative_path
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _layer_file_from_manifest(layer: dict[str, Any], index: int) -> str:
    raw = (
        layer.get("file")
        or layer.get("path")
        or layer.get("png")
        or layer.get("image")
        or layer.get("image_path")
        or layer.get("src")
        or ""
    )
    value = str(raw).replace("\\", "/")
    if value:
        return value if value.startswith("png_layers/") else f"png_layers/{value}"
    layer_id = str(layer.get("id") or layer.get("name") or f"layer_{index:03d}")
    return f"png_layers/{layer_id}.png"


def _manifest_layers(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    layers = manifest.get("layers")
    if isinstance(layers, list):
        return [item for item in layers if isinstance(item, dict)]
    groups = manifest.get("groups")
    if isinstance(groups, list):
        flattened: list[dict[str, Any]] = []
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get("layers"), list):
                flattened.extend(item for item in group["layers"] if isinstance(item, dict))
        return flattened
    return []


def _canvas_from_manifest(manifest: dict[str, Any]) -> dict[str, int]:
    canvas = manifest.get("canvas") if isinstance(manifest.get("canvas"), dict) else {}
    size = manifest.get("size") if isinstance(manifest.get("size"), dict) else {}
    width = canvas.get("width") or size.get("width") or manifest.get("width") or 0
    height = canvas.get("height") or size.get("height") or manifest.get("height") or 0
    return {"width": int(width or 0), "height": int(height or 0)}


def _psd_status(psd_path: Path | None) -> str:
    if psd_path is None:
        return "missing_psd"
    try:
        data = psd_path.read_bytes()
    except OSError:
        return "missing_psd"
    if len(data) < 32 or data[:4] != b"8BPS":
        return "placeholder_psd"
    return "provided_psd"


def import_layer_package(zip_path: Path, upload_root: Path) -> dict[str, Any]:
    package_id = f"layer-package-{uuid4().hex[:12]}"
    package_dir = upload_root / "layer-packages" / package_id
    package_dir.mkdir(parents=True, exist_ok=True)
    _extract_zip(zip_path, package_dir)

    manifest_path = _first_existing(package_dir, "manifest.json")
    if manifest_path is None:
        raise LayerPackageError("Layer package must contain manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LayerPackageError("manifest.json is invalid JSON") from exc
    if not isinstance(manifest, dict):
        raise LayerPackageError("manifest.json must be an object")

    source_path = _first_existing(package_dir, "source.png", "source.jpg", "source.jpeg")
    png_layers_dir = package_dir / "png_layers"
    if not png_layers_dir.exists() or not png_layers_dir.is_dir():
        raise LayerPackageError("Layer package must contain png_layers/")
    psd_path = _first_existing(package_dir, "game_ui_layered.psd")

    layers: list[dict[str, Any]] = []
    for index, layer in enumerate(_manifest_layers(manifest), start=1):
        layer_file = _layer_file_from_manifest(layer, index)
        layer_path = (package_dir / layer_file).resolve()
        if not layer_path.is_relative_to(package_dir.resolve()):
            raise LayerPackageError(f"Layer path must stay inside package: {layer_file}")
        exists = layer_path.exists() and layer_path.is_file()
        layers.append(
            {
                "id": str(layer.get("id") or layer.get("layer_id") or f"layer_{index:03d}"),
                "name": str(layer.get("name") or layer.get("id") or f"Layer {index}"),
                "type": str(layer.get("type") or layer.get("component_type") or "unknown"),
                "visible": bool(layer.get("visible", True)),
                "opacity": float(layer.get("opacity", 1.0)),
                "bbox": layer.get("bbox") if isinstance(layer.get("bbox"), dict) else {},
                "file": layer_file,
                "url": f"layer-packages/{package_id}/{layer_file}" if exists else "",
                "exists": exists,
            }
        )

    return {
        "package_id": package_id,
        "package_dir": str(package_dir),
        "canvas": _canvas_from_manifest(manifest),
        "source_url": f"layer-packages/{package_id}/{source_path.name}" if source_path else "",
        "manifest_url": f"layer-packages/{package_id}/manifest.json",
        "psd_status": _psd_status(psd_path),
        "psd_file": psd_path.name if psd_path else "",
        "layers": layers,
        "warnings": [f"missing layer PNG: {item['file']}" for item in layers if not item["exists"]],
    }
