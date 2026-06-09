from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.opencv_ui_slicer import slice_ui_image


def test_opencv_ui_slicer_generates_workspace_outputs(tmp_path: Path) -> None:
    pytest.importorskip("cv2")
    source = Path("harness/examples/main_ui/marking_test/original.jpg")
    assert source.exists()

    result = slice_ui_image(source, tmp_path / "output", max_components=24)

    slices_dir = Path(result["slices_dir"])
    manifest_path = Path(result["layer_manifest"])
    preview_path = Path(result["candidate_preview"])
    assert slices_dir.is_dir()
    assert manifest_path.exists()
    assert preview_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["canvas"]["width"] > 0
    assert manifest["canvas"]["height"] > 0
    assert len(manifest["layers"]) > 0
    assert len(list(slices_dir.glob("*.png"))) == len(manifest["layers"])
    first_layer = manifest["layers"][0]
    assert first_layer["id"].startswith("component_")
    assert first_layer["slice_file"].startswith("slices/")
