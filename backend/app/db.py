from pathlib import Path
import sqlite3
from uuid import uuid4

from app.schemas import (
    AiProvider,
    AiProviderCreate,
    Asset,
    AssetCreate,
    BasePanel,
    BasePanelCreate,
    GenerationJob,
    GenerationJobCreate,
    GenerationJobPatch,
    Project,
    ProjectCreate,
    StyleProfile,
    StyleProfileCreate,
)


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

    def table_columns(self, connection: sqlite3.Connection, table_name: str) -> set[str]:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

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

    def create_base_panel(self, payload: BasePanelCreate) -> BasePanel:
        base_panel_id = uuid4().hex
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO base_panels (
                  id, project_id, style_profile_id, panel_type, device_type, width, height,
                  texture, border_style, background_style, color_scheme
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    base_panel_id,
                    payload.project_id,
                    payload.style_profile_id,
                    payload.panel_type,
                    payload.device_type,
                    payload.width,
                    payload.height,
                    payload.texture,
                    payload.border_style,
                    payload.background_style,
                    payload.color_scheme,
                ),
            )
        base_panel = self.get_base_panel(base_panel_id)
        if base_panel is None:
            raise RuntimeError("Created base panel could not be loaded")
        return base_panel

    def list_base_panels(self, project_id: str | None = None) -> list[BasePanel]:
        query = """
            SELECT id, project_id, style_profile_id, panel_type, device_type, width, height,
                   texture, border_style, background_style, color_scheme, created_at, updated_at
            FROM base_panels
        """
        params: tuple[str, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY created_at ASC, id ASC"

        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [BasePanel.model_validate(dict(row)) for row in rows]

    def get_base_panel(self, base_panel_id: str) -> BasePanel | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, style_profile_id, panel_type, device_type, width, height,
                       texture, border_style, background_style, color_scheme, created_at, updated_at
                FROM base_panels
                WHERE id = ?
                """,
                (base_panel_id,),
            ).fetchone()
        return BasePanel.model_validate(dict(row)) if row else None

    def update_base_panel(self, base_panel_id: str, payload: BasePanelCreate) -> BasePanel | None:
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE base_panels
                SET project_id = ?,
                    style_profile_id = ?,
                    panel_type = ?,
                    device_type = ?,
                    width = ?,
                    height = ?,
                    texture = ?,
                    border_style = ?,
                    background_style = ?,
                    color_scheme = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.project_id,
                    payload.style_profile_id,
                    payload.panel_type,
                    payload.device_type,
                    payload.width,
                    payload.height,
                    payload.texture,
                    payload.border_style,
                    payload.background_style,
                    payload.color_scheme,
                    base_panel_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_base_panel(base_panel_id)

    def delete_base_panel(self, base_panel_id: str) -> bool:
        with self.connect() as connection:
            result = connection.execute("DELETE FROM base_panels WHERE id = ?", (base_panel_id,))
        return result.rowcount > 0

    def copy_base_panel(self, base_panel_id: str) -> BasePanel | None:
        base_panel = self.get_base_panel(base_panel_id)
        if base_panel is None:
            return None
        return self.create_base_panel(
            BasePanelCreate(
                project_id=base_panel.project_id,
                style_profile_id=base_panel.style_profile_id,
                panel_type=base_panel.panel_type,
                device_type=base_panel.device_type,
                width=base_panel.width,
                height=base_panel.height,
                texture=base_panel.texture,
                border_style=base_panel.border_style,
                background_style=base_panel.background_style,
                color_scheme=base_panel.color_scheme,
            )
        )

    def list_generation_jobs(self, project_id: str | None = None) -> list[GenerationJob]:
        query = """
            SELECT id, project_id, provider_id, job_type, status, progress, input_json, output_json,
                   output_preview_path, error_message, retry_count, logs, created_at, updated_at
            FROM generation_jobs
        """
        params: tuple[str, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY created_at DESC, id DESC"

        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [GenerationJob.model_validate(dict(row)) for row in rows]

    def create_asset(self, payload: AssetCreate) -> Asset:
        asset_id = uuid4().hex
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO assets (
                  id, project_id, asset_type, device_type, width, height,
                  file_path, original_filename, metadata_json, source, generation_job_id, thumbnail_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    payload.project_id,
                    payload.asset_type,
                    payload.device_type,
                    payload.width,
                    payload.height,
                    payload.file_path,
                    payload.original_filename,
                    payload.metadata_json,
                    payload.source,
                    payload.generation_job_id,
                    payload.thumbnail_path,
                ),
            )
        asset = self.get_asset(asset_id)
        if asset is None:
            raise RuntimeError("Created asset could not be loaded")
        return asset

    def list_assets(
        self,
        project_id: str | None = None,
        asset_type: str | None = None,
        device_type: str | None = None,
        generation_job_id: str | None = None,
    ) -> list[Asset]:
        query = """
            SELECT id, project_id, asset_type, device_type, width, height,
                   file_path, original_filename, metadata_json, source, generation_job_id,
                   thumbnail_path, created_at, updated_at
            FROM assets
        """
        clauses: list[str] = []
        params: list[str] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if asset_type:
            clauses.append("asset_type = ?")
            params.append(asset_type)
        if device_type:
            clauses.append("device_type = ?")
            params.append(device_type)
        if generation_job_id:
            clauses.append("generation_job_id = ?")
            params.append(generation_job_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, id DESC"

        with self.connect() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [Asset.model_validate(dict(row)) for row in rows]

    def get_asset(self, asset_id: str) -> Asset | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, asset_type, device_type, width, height,
                       file_path, original_filename, metadata_json, source, generation_job_id,
                       thumbnail_path, created_at, updated_at
                FROM assets
                WHERE id = ?
                """,
                (asset_id,),
            ).fetchone()
        return Asset.model_validate(dict(row)) if row else None

    def update_asset(self, asset_id: str, payload: AssetCreate) -> Asset | None:
        with self.connect() as connection:
            result = connection.execute(
                """
                UPDATE assets
                SET project_id = ?,
                    asset_type = ?,
                    device_type = ?,
                    width = ?,
                    height = ?,
                    file_path = ?,
                    original_filename = ?,
                    metadata_json = ?,
                    source = ?,
                    generation_job_id = ?,
                    thumbnail_path = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.project_id,
                    payload.asset_type,
                    payload.device_type,
                    payload.width,
                    payload.height,
                    payload.file_path,
                    payload.original_filename,
                    payload.metadata_json,
                    payload.source,
                    payload.generation_job_id,
                    payload.thumbnail_path,
                    asset_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_asset(asset_id)

    def delete_asset(self, asset_id: str) -> bool:
        with self.connect() as connection:
            result = connection.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        return result.rowcount > 0

    def create_generation_job(self, payload: GenerationJobCreate) -> GenerationJob:
        job_id = uuid4().hex
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO generation_jobs (
                  id, project_id, provider_id, job_type, status, progress, input_json,
                  output_json, output_preview_path, error_message, retry_count, logs
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                """,
                (
                    job_id,
                    payload.project_id,
                    payload.provider_id,
                    payload.job_type,
                    payload.status,
                    payload.progress,
                    payload.input_json,
                    payload.output_json,
                    payload.output_preview_path,
                    payload.error_message,
                    payload.logs,
                ),
            )
        job = self.get_generation_job(job_id)
        if job is None:
            raise RuntimeError("Created generation job could not be loaded")
        return job

    def get_generation_job(self, generation_job_id: str) -> GenerationJob | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, project_id, provider_id, job_type, status, progress, input_json, output_json,
                       output_preview_path, error_message, retry_count, logs, created_at, updated_at
                FROM generation_jobs
                WHERE id = ?
                """,
                (generation_job_id,),
            ).fetchone()
        return GenerationJob.model_validate(dict(row)) if row else None

    def update_generation_job(
        self, generation_job_id: str, payload: GenerationJobPatch
    ) -> GenerationJob | None:
        current = self.get_generation_job(generation_job_id)
        if current is None:
            return None
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE generation_jobs
                SET status = ?,
                    provider_id = ?,
                    progress = ?,
                    input_json = ?,
                    output_json = ?,
                    output_preview_path = ?,
                    error_message = ?,
                    logs = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.status if payload.status is not None else current.status,
                    payload.provider_id if payload.provider_id is not None else current.provider_id,
                    payload.progress if payload.progress is not None else current.progress,
                    payload.input_json if payload.input_json is not None else current.input_json,
                    payload.output_json if payload.output_json is not None else current.output_json,
                    payload.output_preview_path
                    if payload.output_preview_path is not None
                    else current.output_preview_path,
                    payload.error_message if payload.error_message is not None else current.error_message,
                    payload.logs if payload.logs is not None else current.logs,
                    generation_job_id,
                ),
            )
        return self.get_generation_job(generation_job_id)

    def create_ai_provider(self, payload: AiProviderCreate) -> AiProvider:
        provider_id = uuid4().hex
        with self.connect() as connection:
            columns = ["id", "name", "type", "enabled", "config_json"]
            values: list[str | int] = [provider_id, payload.name, payload.type, int(payload.enabled), payload.config_json]
            if "provider_type" in self.table_columns(connection, "ai_providers"):
                columns.append("provider_type")
                values.append(payload.type)
            placeholders = ", ".join("?" for _ in columns)
            connection.execute(
                f"INSERT INTO ai_providers ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(values),
            )
        provider = self.get_ai_provider(provider_id)
        if provider is None:
            raise RuntimeError("Created AI provider could not be loaded")
        return provider

    def list_ai_providers(self) -> list[AiProvider]:
        with self.connect() as connection:
            columns = self.table_columns(connection, "ai_providers")
            type_select = "COALESCE(type, provider_type) AS type" if "provider_type" in columns else "type"
            rows = connection.execute(
                f"""
                SELECT id, name, {type_select}, enabled, config_json, created_at, updated_at
                FROM ai_providers
                ORDER BY created_at ASC, id ASC
                """
            ).fetchall()
        return [AiProvider.model_validate({**dict(row), "enabled": bool(row["enabled"])}) for row in rows]

    def get_ai_provider(self, provider_id: str) -> AiProvider | None:
        with self.connect() as connection:
            columns = self.table_columns(connection, "ai_providers")
            type_select = "COALESCE(type, provider_type) AS type" if "provider_type" in columns else "type"
            row = connection.execute(
                f"""
                SELECT id, name, {type_select}, enabled, config_json, created_at, updated_at
                FROM ai_providers
                WHERE id = ?
                """,
                (provider_id,),
            ).fetchone()
        return AiProvider.model_validate({**dict(row), "enabled": bool(row["enabled"])}) if row else None

    def update_ai_provider(self, provider_id: str, payload: AiProviderCreate) -> AiProvider | None:
        with self.connect() as connection:
            columns = self.table_columns(connection, "ai_providers")
            assignments = ["name = ?", "type = ?", "enabled = ?", "config_json = ?"]
            params: list[str | int] = [payload.name, payload.type, int(payload.enabled), payload.config_json]
            if "provider_type" in columns:
                assignments.append("provider_type = ?")
                params.append(payload.type)
            assignments.append("updated_at = CURRENT_TIMESTAMP")
            params.append(provider_id)
            result = connection.execute(
                f"""
                UPDATE ai_providers
                SET {', '.join(assignments)}
                WHERE id = ?
                """,
                tuple(params),
            )
        if result.rowcount == 0:
            return None
        return self.get_ai_provider(provider_id)

    def retry_generation_job(self, generation_job_id: str) -> GenerationJob | None:
        current = self.get_generation_job(generation_job_id)
        if current is None:
            return None
        retry_count = current.retry_count + 1
        retry_log = f"Retry {retry_count} queued"
        logs = f"{current.logs}\n{retry_log}" if current.logs else retry_log
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE generation_jobs
                SET status = 'pending',
                    progress = 0,
                    error_message = '',
                    retry_count = ?,
                    logs = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (retry_count, logs, generation_job_id),
            )
        return self.get_generation_job(generation_job_id)
