from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_996_export import validate_package


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "996_ready_demo"


def copy_fixture(tmp_path: Path) -> Path:
    package_dir = tmp_path / "996_ready_demo"
    shutil.copytree(FIXTURE_DIR, package_dir)
    return package_dir


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_transparent_fields_in_demo_package_pass() -> None:
    report = validate_package(FIXTURE_DIR)

    assert report["ok"] is True
    assert report["checks"]["transparent_fields"] is True


def test_transparent_field_is_backward_compatible_when_missing(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    manifest_path = package_dir / "manifest.json"
    annotation_path = package_dir / "annotation.json"
    manifest = read_json(manifest_path)
    annotation = read_json(annotation_path)
    for component in manifest["components"]:
        component.pop("transparent", None)
    for component in annotation["components"]:
        component.pop("transparent", None)
    write_json(manifest_path, manifest)
    write_json(annotation_path, annotation)

    report = validate_package(package_dir)

    assert report["ok"] is True
    assert report["checks"]["transparent_fields"] is True


def test_button_transparent_field_must_require_transparency(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    manifest_path = package_dir / "manifest.json"
    manifest = read_json(manifest_path)
    button = next(component for component in manifest["components"] if component["component_type"] == "button")
    button["transparent"]["required"] = False
    write_json(manifest_path, manifest)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["transparent_fields"] is False
    assert "manifest.components[2].transparent.required must be true for button components" in report["errors"]


def test_transparent_field_rejects_invalid_status(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    annotation_path = package_dir / "annotation.json"
    annotation = read_json(annotation_path)
    annotation["components"][0]["transparent"]["status"] = "maybe"
    write_json(annotation_path, annotation)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["transparent_fields"] is False
    assert "annotation.components[0].transparent.status must be one of ['not_required', 'unverified', 'verified']" in report["errors"]
