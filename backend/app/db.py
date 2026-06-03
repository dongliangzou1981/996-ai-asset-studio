from pathlib import Path
import sqlite3
from uuid import uuid4

from app.schemas import Project, ProjectCreate, StyleProfile, StyleProfileCreate


class StudioDatabase:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        schema_path = Path(__file__).resolve().parent / "db" / "schema.sql"
        with self.connect() as connection:
            connection.executescript(schema_path.read_text(encoding="utf-8"))

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def create_project(self, payload: ProjectCreate) -> Project:
        project_id = uuid4().hex
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, description, status)
                VALUES (?, ?, ?, ?)
                """,
                (project_id, payload.name, payload.description, payload.status),
            )
        project = self.get_project(project_id)
        if project is None:
            raise RuntimeError("Created project could not be loaded")
        return project

    def list_projects(self) -> list[Project]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, name, description, status, created_at, updated_at
                FROM projects
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [Project.model_validate(dict(row)) for row in rows]

    def get_project(self, project_id: str) -> Project | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, name, description, status, created_at, updated_at
                FROM projects
                WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
        return Project.model_validate(dict(row)) if row else None

    def update_project(self, project_id: str, payload: ProjectCreate) -> Project | None:
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE projects
                SET name = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (payload.name, payload.description, payload.status, project_id),
            )
        if result.rowcount == 0:
            return None
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self.connect() as connection:
            result = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return result.rowcount > 0

    def create_style_profile(self, payload: StyleProfileCreate) -> StyleProfile:
        style_profile_id = uuid4().hex
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO style_profiles (
                  id, project_id, name, description, palette_json, prompt_notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    style_profile_id,
                    payload.project_id,
                    payload.name,
                    payload.description,
                    payload.palette_json,
                    payload.prompt_notes,
                ),
            )
        style_profile = self.get_style_profile(style_profile_id)
        if style_profile is None:
            raise RuntimeError("Created style profile could not be loaded")
        return style_profile

    def list_style_profiles(self, project_id: str | None = None) -> list[StyleProfile]:
        query = """
            SELECT id, project_id, name, description, palette_json, prompt_notes, created_at, updated_at
            FROM style_profiles
        """
        params: tuple[str, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY created_at ASC, id ASC"

        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [StyleProfile.model_validate(dict(row)) for row in rows]

    def get_style_profile(self, style_profile_id: str) -> StyleProfile | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, name, description, palette_json, prompt_notes, created_at, updated_at
                FROM style_profiles
                WHERE id = ?
                """,
                (style_profile_id,),
            ).fetchone()
        return StyleProfile.model_validate(dict(row)) if row else None

    def update_style_profile(
        self, style_profile_id: str, payload: StyleProfileCreate
    ) -> StyleProfile | None:
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE style_profiles
                SET project_id = ?,
                    name = ?,
                    description = ?,
                    palette_json = ?,
                    prompt_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.project_id,
                    payload.name,
                    payload.description,
                    payload.palette_json,
                    payload.prompt_notes,
                    style_profile_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_style_profile(style_profile_id)

    def delete_style_profile(self, style_profile_id: str) -> bool:
        with self.connect() as connection:
            result = connection.execute("DELETE FROM style_profiles WHERE id = ?", (style_profile_id,))
        return result.rowcount > 0

