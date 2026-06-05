from __future__ import annotations

import json
import shutil
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import StudioDatabase
from app.schemas import AiProviderCreate
from scripts.generate_screen_with_style import (
    build_reference_guided_prompt,
    ensure_real_provider_ready,
    target_package_dir,
)
from scripts.validate_996_export import validate_package


def test_reference_guided_prompt_contains_required_generation_constraints(tmp_path: Path) -> None:
    style = {
        "style_code": "STYLE_0001",
        "style_name": "Dark Gold Dragon",
        "style_summary": "dark fantasy, gold dragon ornament, heavy game UI",
        "color_palette": ["#1A120E", "#D9A441", "#6E1F16"],
        "font_style": "bold readable Chinese game UI font",
        "border_style": "gold carved border",
        "button_style": "dark red glossy button with gold trim",
        "icon_style": "high contrast fantasy icon",
        "texture_style": "aged metal and leather texture",
    }
    reference_image = tmp_path / "role-reference.png"
    reference_image.write_bytes(b"reference")

    prompt = build_reference_guided_prompt(
        style=style,
        screen_type="role_ui",
        reference_image_path=reference_image,
        user_prompt="角色面板需要突出装备槽和战力信息",
    )

    assert "STYLE_0001" in prompt
    assert "Dark Gold Dragon" in prompt
    assert "role_ui" in prompt
    assert "Keep the reference layout structure" in prompt
    assert "Do not copy the reference image directly" in prompt
    assert "996 legend game UI" in prompt
    assert "16:9 landscape" in prompt
    assert "single screen" in prompt
    assert "slicing and annotation" in prompt
    assert "角色面板需要突出装备槽和战力信息" in prompt


def test_style_inheritance_prompt_can_omit_reference_image() -> None:
    style = {
        "style_code": "STYLE_0001",
        "style_name": "Dark Gold Dragon",
        "style_summary": "dark fantasy, gold dragon ornament, heavy game UI",
        "color_palette": ["#1A120E", "#D9A441", "#6E1F16"],
        "font_style": "bold readable Chinese game UI font",
        "border_style": "gold carved border",
        "button_style": "dark red glossy button with gold trim",
        "icon_style": "high contrast fantasy icon",
        "texture_style": "aged metal and leather texture",
    }

    prompt = build_reference_guided_prompt(style=style, screen_type="bag_ui", user_prompt="large item grid")

    assert "STYLE_0001" in prompt
    assert "bag_ui" in prompt
    assert "No reference image supplied" in prompt
    assert "Inherit the master style" in prompt
    assert "large item grid" in prompt


def test_target_package_dir_uses_style_and_screen_type(tmp_path: Path) -> None:
    output = target_package_dir(
        upload_root=tmp_path / "uploads",
        style_code="STYLE_0001",
        screen_type="main_ui",
        generation_job_id="job-001",
    )

    assert output == tmp_path / "uploads" / "996-ready" / "STYLE_0001" / "main_ui" / "job-001"


def test_validator_reports_style_guided_nested_layout(tmp_path: Path) -> None:
    source_package = Path(__file__).parent / "fixtures" / "996_ready_demo"
    nested_package = tmp_path / "996-ready" / "STYLE_0001" / "main_ui" / "job-001"
    shutil.copytree(source_package, nested_package)

    report = validate_package(nested_package)

    assert report["ok"] is True
    assert report["layout"]["style_code"] == "STYLE_0001"
    assert report["layout"]["screen_type"] == "main_ui"
    assert report["layout"]["generation_job_id"] == "job-001"


def test_real_provider_env_error_is_clear(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MISSING_STYLE_API_KEY", raising=False)
    database = StudioDatabase(tmp_path / "studio.db")
    database.initialize()
    database.create_ai_provider(
        AiProviderCreate(
            name="Ofox Missing Env",
            type="ofox",
            enabled=True,
            config_json='{"api_key_env":"MISSING_STYLE_API_KEY","base_url":"https://api.ofox.ai/v1","model":"gpt-image-2"}',
        )
    )

    with pytest.raises(RuntimeError, match="Environment variable MISSING_STYLE_API_KEY is not set"):
        ensure_real_provider_ready(database)
