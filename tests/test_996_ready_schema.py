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


def test_schema_v1_demo_package_passes() -> None:
    report = validate_package(FIXTURE_DIR)

    assert report["ok"] is True
    assert report["checks"]["schema_v1"] is True
    assert report["checks"]["manifest_required_fields"] is True
    assert report["checks"]["annotation_required_fields"] is True
    assert report["checks"]["field_types"] is True
    assert report["checks"]["component_classification"] is True
    assert report["schema_version"] == "1.0"


def test_schema_v1_rejects_missing_manifest_required_field(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    manifest_path = package_dir / "manifest.json"
    manifest = read_json(manifest_path)
    del manifest["package_type"]
    write_json(manifest_path, manifest)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["manifest_required_fields"] is False
    assert "manifest.package_type is required" in report["errors"]


def test_schema_v1_rejects_invalid_field_type(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    manifest_path = package_dir / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["resolution"]["width"] = "1024"
    write_json(manifest_path, manifest)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["field_types"] is False
    assert "manifest.resolution.width must be a positive integer" in report["errors"]


def test_schema_v1_rejects_path_traversal(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    manifest_path = package_dir / "manifest.json"
    manifest = read_json(manifest_path)
    manifest["components"][0]["file"] = "../main_bottom_bar.png"
    write_json(manifest_path, manifest)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["component_paths_relative"] is False
    assert "component main_bottom_bar must not traverse outside package: ../main_bottom_bar.png" in report["errors"]


def test_schema_v1_rejects_unknown_component_type(tmp_path: Path) -> None:
    package_dir = copy_fixture(tmp_path)
    annotation_path = package_dir / "annotation.json"
    annotation = read_json(annotation_path)
    annotation["components"][0]["component_type"] = "magic_widget"
    write_json(annotation_path, annotation)

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["component_classification"] is False
    assert "annotation.components[0].component_type must be one of Schema V1 component types" in report["errors"]
