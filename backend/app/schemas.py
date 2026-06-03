from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    project_id: str
    job_type: str
    status: str
    progress: int
    created_at: str
    updated_at: str


class GenerationJobList(BaseModel):
    items: list[GenerationJob]
