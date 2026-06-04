from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_996_export import validate_package


def test_validate_demo_package_passes() -> None:
    package_dir = Path(__file__).parent / "fixtures" / "996_ready_demo"

    report = validate_package(package_dir)

    assert report["ok"] is True
    assert report["package_dir"] == str(package_dir)
    assert report["checks"]["manifest_exists"] is True
    assert report["checks"]["annotation_exists"] is True
    assert report["checks"]["preview_exists"] is True
    assert report["checks"]["ui_preview_exists"] is True
    assert report["checks"]["component_files_exist"] is True
    assert report["errors"] == []


def test_validate_missing_component_reports_error(tmp_path: Path) -> None:
    package_dir = tmp_path / "broken"
    package_dir.mkdir()
    (package_dir / "manifest.json").write_text(
        '{"ui_preview":"ui_preview.png","components":[{"component_id":"missing","file":"components/missing.png"}]}',
        encoding="utf-8",
    )
    (package_dir / "annotation.json").write_text('{"components":[]}', encoding="utf-8")
    (package_dir / "preview.html").write_text("<!doctype html>", encoding="utf-8")
    (package_dir / "ui_preview.png").write_bytes(b"not-a-real-png-but-present")

    report = validate_package(package_dir)

    assert report["ok"] is False
    assert report["checks"]["component_files_exist"] is False
    assert "Missing component file: components/missing.png" in report["errors"]
