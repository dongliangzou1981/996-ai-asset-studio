from __future__ import annotations

import argparse
import json
import math
import shutil
from pathlib import Path
from typing import Any


def _load_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV baseline slicer requires opencv-python-headless or opencv-python."
        ) from exc
    return cv2, np


def _read_image(path: Path, cv2: Any, np: Any) -> Any:
    data = np.fromfile(str(path), dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_UNCHANGED)


def _write_image(path: Path, image: Any, cv2: Any) -> None:
    extension = path.suffix or ".png"
    ok, encoded = cv2.imencode(extension, image)
    if not ok:
        raise RuntimeError(f"OpenCV could not encode image: {path}")
    encoded.tofile(str(path))


def _ensure_bgr(image: Any, cv2: Any, np: Any) -> Any:
    if image is None:
        return None
    if len(image.shape) == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        alpha = image[:, :, 3].astype(float) / 255.0
        foreground = image[:, :, :3].astype(float)
        background = np.full_like(foreground, 255.0)
        composited = foreground * alpha[:, :, None] + background * (1.0 - alpha[:, :, None])
        return composited.astype("uint8")
    return image


def _contour_points(contour: Any, cv2: Any, *, limit: int = 16) -> list[list[int]]:
    perimeter = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
    points = [[int(point[0][0]), int(point[0][1])] for point in approx]
    if len(points) > limit:
        step = max(1, math.ceil(len(points) / limit))
        points = points[::step][:limit]
    return points


def _circle_points(x: int, y: int, width: int, height: int, *, steps: int = 16) -> list[list[int]]:
    cx = x + width / 2
    cy = y + height / 2
    radius = min(width, height) / 2
    return [
        [int(round(cx + math.cos(2 * math.pi * index / steps) * radius)), int(round(cy + math.sin(2 * math.pi * index / steps) * radius))]
        for index in range(steps)
    ]


def _iou(left: dict[str, int], right: dict[str, int]) -> float:
    x1 = max(left["x"], right["x"])
    y1 = max(left["y"], right["y"])
    x2 = min(left["x"] + left["width"], right["x"] + right["width"])
    y2 = min(left["y"] + left["height"], right["y"] + right["height"])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0
    left_area = left["width"] * left["height"]
    right_area = right["width"] * right["height"]
    return intersection / float(left_area + right_area - intersection)


def _classify_layer(
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    area: float,
    contour_area: float,
    canvas_width: int,
    canvas_height: int,
    circularity: float,
) -> tuple[str, str]:
    aspect = width / max(height, 1)
    area_ratio = area / float(canvas_width * canvas_height)
    square_like = 0.72 <= aspect <= 1.35
    in_skill_zone = x > canvas_width * 0.62 and y > canvas_height * 0.52

    if square_like and circularity >= 0.58 and width >= 36 and height >= 36:
        return ("skill" if in_skill_zone else "button"), "circle"
    if area_ratio >= 0.025 or (width >= canvas_width * 0.22 and height >= 44) or aspect >= 4.5:
        return "panel", "rect"
    if max(width, height) <= 96 and contour_area >= 120:
        return "icon", "rect"
    if 0.45 <= aspect <= 4.5 and width >= 28 and height >= 20:
        return "button", "rect"
    return "unknown", "rect"


def slice_ui_image(source_image: str | Path, output_dir: str | Path, *, max_components: int = 80) -> dict[str, Any]:
    cv2, np = _load_cv2()
    source = Path(source_image)
    output = Path(output_dir)
    if not source.exists() or not source.is_file():
        raise FileNotFoundError(f"Source image not found: {source}")

    raw_image = _read_image(source, cv2, np)
    image = _ensure_bgr(raw_image, cv2, np)
    if image is None:
        raise RuntimeError(f"OpenCV could not read image: {source}")

    canvas_height, canvas_width = image.shape[:2]
    output.mkdir(parents=True, exist_ok=True)
    slices_dir = output / "slices"
    if slices_dir.exists():
        shutil.rmtree(slices_dir)
    slices_dir.mkdir(parents=True)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    median = float(np.median(blurred))
    lower = int(max(20, 0.66 * median))
    upper = int(min(255, max(80, 1.33 * median)))
    edges = cv2.Canny(blurred, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges = cv2.dilate(edges, kernel, iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    min_area = max(160.0, canvas_width * canvas_height * 0.00018)
    max_area = canvas_width * canvas_height * 0.72
    accepted_boxes: list[dict[str, int]] = []
    layers: list[dict[str, Any]] = []
    preview = image.copy()

    for contour in contours:
        contour_area = float(cv2.contourArea(contour))
        if contour_area < min_area:
            continue
        x, y, width, height = [int(value) for value in cv2.boundingRect(contour)]
        bbox_area = float(width * height)
        if width < 10 or height < 10 or bbox_area > max_area:
            continue
        if width > canvas_width * 0.96 and height > canvas_height * 0.96:
            continue

        bbox = {"x": x, "y": y, "width": width, "height": height}
        if any(_iou(bbox, existing) > 0.7 for existing in accepted_boxes):
            continue

        perimeter = float(cv2.arcLength(contour, True))
        circularity = 0.0 if perimeter <= 0 else (4 * math.pi * contour_area) / (perimeter * perimeter)
        component_type, shape_type = _classify_layer(
            x=x,
            y=y,
            width=width,
            height=height,
            area=bbox_area,
            contour_area=contour_area,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
            circularity=circularity,
        )

        layer_id = f"component_{len(layers) + 1:03d}"
        slice_name = f"{layer_id}.png"
        mask = np.zeros((canvas_height, canvas_width), dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
        crop = image[y : y + height, x : x + width]
        crop_mask = mask[y : y + height, x : x + width]
        crop_rgba = cv2.cvtColor(crop, cv2.COLOR_BGR2BGRA)
        crop_rgba[:, :, 3] = crop_mask
        _write_image(slices_dir / slice_name, crop_rgba, cv2)

        outline_points = _circle_points(x, y, width, height) if shape_type == "circle" else _contour_points(contour, cv2)
        layers.append(
            {
                "id": layer_id,
                "type": component_type,
                "bbox": bbox,
                "outline_points": outline_points,
                "slice_file": f"slices/{slice_name}",
            }
        )
        accepted_boxes.append(bbox)

        color = (48, 204, 113) if component_type in {"button", "skill"} else (52, 152, 219)
        if shape_type == "circle":
            center = (x + width // 2, y + height // 2)
            radius = max(4, min(width, height) // 2)
            cv2.circle(preview, center, radius, color, 2)
        else:
            cv2.rectangle(preview, (x, y), (x + width, y + height), color, 2)
        cv2.putText(preview, layer_id, (x, max(14, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

        if len(layers) >= max_components:
            break

    manifest = {
        "canvas": {"width": int(canvas_width), "height": int(canvas_height)},
        "layers": layers,
    }
    manifest_path = output / "layer_manifest.json"
    preview_path = output / "candidate_preview.png"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_image(preview_path, preview, cv2)
    return {
        "output_dir": str(output),
        "slices_dir": str(slices_dir),
        "layer_manifest": str(manifest_path),
        "candidate_preview": str(preview_path),
        "layer_count": len(layers),
        "canvas": manifest["canvas"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenCV baseline slicer for 996 UI candidate images.")
    parser.add_argument("input", help="Path to a Studio generated PNG/JPG candidate image.")
    parser.add_argument("--output", default="output", help="Output directory for slices, manifest, and preview.")
    parser.add_argument("--max-components", default=80, type=int)
    args = parser.parse_args()
    result = slice_ui_image(args.input, args.output, max_components=args.max_components)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
