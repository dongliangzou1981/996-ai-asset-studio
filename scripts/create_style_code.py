from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

from PIL import Image


STYLE_CODE_PATTERN = re.compile(r"^STYLE_(\d{4})$")


def next_style_code(style_root: Path) -> str:
    style_root.mkdir(parents=True, exist_ok=True)
    highest = 0
    for child in style_root.iterdir():
        if not child.is_dir():
            continue
        match = STYLE_CODE_PATTERN.match(child.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"STYLE_{highest + 1:04d}"


def load_manifest(package_dir: Path) -> dict[str, Any]:
    manifest_path = package_dir / "manifest.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"manifest.json not found in {package_dir}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest.json is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("manifest.json must contain a JSON object")
    return data


def dominant_palette(image_path: Path, limit: int = 5) -> list[str]:
    if not image_path.exists():
        return []
    with Image.open(image_path).convert("RGB") as image:
        image.thumbnail((128, 128))
        colors = image.getcolors(maxcolors=128 * 128) or []
    colors.sort(reverse=True, key=lambda item: item[0])
    palette: list[str] = []
    for _, color in colors:
        value = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        if value not in palette:
            palette.append(value)
        if len(palette) >= limit:
            break
    return palette


def create_style_profile(
    *,
    style_code: str,
    style_name: str,
    package_dir: Path,
    manifest: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    ui_preview = str(manifest.get("ui_preview") or "ui_preview.png")
    preview_path = package_dir / ui_preview
    palette = dominant_palette(preview_path)
    palette_text = ", ".join(palette) if palette else "dark fantasy base colors, gold accents, red highlights"

    return {
        "style_code": style_code,
        "style_name": style_name,
        "source_job_id": str(manifest.get("generation_job_id") or package_dir.name),
        "source_asset_id": str(manifest.get("source_asset_id") or ""),
        "original_ui_preview": str(preview_path),
        "style_summary": f"{style_name}: 996 legend game UI style derived from source job output.",
        "color_palette": palette or ["#1A120E", "#D9A441", "#6E1F16"],
        "color_description": f"Dominant palette uses {palette_text}.",
        "font_style": "Bold, readable Chinese fantasy game UI typography; high contrast over dark panels.",
        "border_style": "Layered metallic fantasy borders with gold highlights and clear panel separation.",
        "button_style": "Readable rectangular fantasy buttons with bright trim and strong pressed-state potential.",
        "icon_style": "High-contrast item and skill icons with clear silhouettes suitable for slicing.",
        "texture_style": "Dark stone, aged metal, leather, and subtle ornamental texture.",
        "created_at": now,
        "updated_at": now,
    }


def create_style_code(
    *,
    package_dir: str | Path,
    style_root: str | Path = "style_codes",
    style_name: str | None = None,
) -> dict[str, Any]:
    package_path = Path(package_dir)
    style_root_path = Path(style_root)
    manifest = load_manifest(package_path)
    style_code = next_style_code(style_root_path)
    final_style_name = style_name or style_code
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    profile = create_style_profile(
        style_code=style_code,
        style_name=final_style_name,
        package_dir=package_path,
        manifest=manifest,
        now=now,
    )

    output_dir = style_root_path / style_code
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "style.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


def resolve_package_dir(args: argparse.Namespace) -> Path:
    if args.package_dir:
        return Path(args.package_dir)
    if args.generation_job_id:
        return Path(args.upload_root) / "996-ready" / args.generation_job_id
    raise ValueError("Provide --package-dir or --generation-job-id")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a JSON style code from an existing 996-ready package.")
    parser.add_argument("--generation-job-id", help="Existing generation job id under upload_root/996-ready.")
    parser.add_argument("--package-dir", help="Existing 996-ready package directory.")
    parser.add_argument("--style-name", help="Optional display name for the style.")
    parser.add_argument("--style-root", default="style_codes", help="Directory used to store STYLE_xxxx folders.")
    parser.add_argument("--upload-root", default="assets/uploads", help="Upload root used with --generation-job-id.")
    args = parser.parse_args()

    try:
        style = create_style_code(
            package_dir=resolve_package_dir(args),
            style_root=args.style_root,
            style_name=args.style_name,
        )
    except Exception as exc:
        print(f"Failed to create style code: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(style, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
