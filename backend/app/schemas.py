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

