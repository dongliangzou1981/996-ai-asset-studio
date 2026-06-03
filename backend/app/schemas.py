from typing import Literal

import json

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {"name": "Match-3 Launch", "description": "Playable ad art", "status": "draft"}
        ]
    })

    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    status: str = Field(default="draft", min_length=1, max_length=32)


class Project(ProjectCreate):
    id: str
    created_at: str
    updated_at: str


class ProjectList(BaseModel):
    items: list[Project]


class StyleProfileCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "project_id": "project-id",
                "name": "Candy UI",
                "description": "Bright, rounded, mobile friendly",
                "palette_json": "{\"primary\":\"#ff6b9a\"}",
                "prompt_notes": "Use glossy buttons",
            }
        ]
    })

    project_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    palette_json: str = ""
    prompt_notes: str = ""


class StyleProfile(StyleProfileCreate):
    id: str
    created_at: str
    updated_at: str


class StyleProfileList(BaseModel):
    items: list[StyleProfile]


PanelType = Literal[
    "main_panel",
    "sub_panel",
    "popup_panel",
    "list_panel",
    "input_panel",
    "button_panel",
    "icon_panel",
]


class BasePanelCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "project_id": "project-id",
                "style_profile_id": "style-profile-id",
                "panel_type": "main_panel",
                "device_type": "mobile",
                "width": 1080,
                "height": 1920,
                "texture": "soft_glass",
                "border_style": "rounded_8",
                "background_style": "layered_gradient",
                "color_scheme": "blue_white",
            }
        ]
    })

    project_id: str = Field(min_length=1)
    style_profile_id: str = Field(min_length=1)
    panel_type: PanelType
    device_type: str = Field(min_length=1, max_length=40)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    texture: str = ""
    border_style: str = ""
    background_style: str = ""
    color_scheme: str = ""


class BasePanel(BasePanelCreate):
    id: str
    created_at: str
    updated_at: str


class BasePanelList(BaseModel):
    items: list[BasePanel]


class GenerationJob(BaseModel):
    id: str
    project_id: str | None
    provider_id: str | None
    job_type: str
    status: str
    progress: int
    input_json: str
    output_json: str
    output_preview_path: str
    error_message: str
    retry_count: int
    logs: str
    created_at: str
    updated_at: str


class GenerationJobList(BaseModel):
    items: list[GenerationJob]


AssetType = Literal[
    "reference_image",
    "ui_preview",
    "annotated_preview",
    "sliced_component",
    "base_panel",
    "icon",
]

JobStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
AssetSource = Literal["uploaded", "mock_generated", "ai_generated"]


class AssetCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "project_id": "project-id",
                "asset_type": "reference_image",
                "device_type": "mobile",
                "width": 1080,
                "height": 1920,
                "file_path": "assets/reference.png",
                "original_filename": "reference.png",
                "metadata_json": "{\"role\":\"mood\"}",
            }
        ]
    })

    project_id: str | None = None
    asset_type: AssetType
    device_type: str = ""
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    file_path: str = Field(min_length=1)
    original_filename: str = ""
    metadata_json: str = ""
    source: AssetSource = "uploaded"
    generation_job_id: str | None = None
    thumbnail_path: str = ""


class Asset(AssetCreate):
    id: str
    created_at: str
    updated_at: str


class AssetList(BaseModel):
    items: list[Asset]


class GenerationJobCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "examples": [
            {
                "project_id": "project-id",
                "job_type": "asset_prepare",
                "status": "pending",
                "progress": 0,
                "input_json": "{\"asset_id\":\"asset-id\"}",
                "output_json": "",
                "error_message": "",
                "logs": "queued",
            }
        ]
    })

    project_id: str | None = None
    provider_id: str | None = None
    job_type: str = Field(min_length=1, max_length=80)
    status: JobStatus = "pending"
    progress: int = Field(default=0, ge=0, le=100)
    input_json: str = ""
    output_json: str = ""
    output_preview_path: str = ""
    error_message: str = ""
    logs: str = ""
    auto_run: bool = False


class GenerationJobPatch(BaseModel):
    provider_id: str | None = None
    status: JobStatus | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    input_json: str | None = None
    output_json: str | None = None
    output_preview_path: str | None = None
    error_message: str | None = None
    logs: str | None = None


class MockUiGenerationRequest(BaseModel):
    project_id: str | None = None
    device_type: str = Field(default="mobile", min_length=1, max_length=40)
    width: int = Field(default=1080, gt=0)
    height: int = Field(default=1920, gt=0)


class AiProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: Literal["mock", "openai", "custom"] = "mock"
    enabled: bool = False
    config_json: str = "{}"

    @field_validator("config_json")
    @classmethod
    def validate_safe_config_json(cls, value: str) -> str:
        try:
            config = json.loads(value or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("config_json must be a JSON object") from exc
        if not isinstance(config, dict):
            raise ValueError("config_json must be a JSON object")
        allowed_keys = {"api_key_env"}
        extra_keys = set(config) - allowed_keys
        if extra_keys:
            raise ValueError("config_json may only contain api_key_env")
        if "api_key_env" in config and not isinstance(config["api_key_env"], str):
            raise ValueError("api_key_env must be a string")
        return json.dumps(config, separators=(",", ":"))


class AiProvider(AiProviderCreate):
    id: str
    created_at: str
    updated_at: str


class AiProviderList(BaseModel):
    items: list[AiProvider]


class ProviderHealth(BaseModel):
    id: str
    name: str
    type: str
    enabled: bool
    status: str
    message: str


class ProviderHealthList(BaseModel):
    items: list[ProviderHealth]
