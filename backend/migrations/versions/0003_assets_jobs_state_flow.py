"""assets and generation job state flow

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS assets")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
          id TEXT PRIMARY KEY,
          project_id TEXT,
          asset_type TEXT NOT NULL,
          device_type TEXT,
          width INTEGER NOT NULL DEFAULT 0,
          height INTEGER NOT NULL DEFAULT 0,
          file_path TEXT NOT NULL,
          original_filename TEXT,
          metadata_json TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
        """
    )
    op.execute("DROP TABLE IF EXISTS reference_images")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS reference_images (
          id TEXT PRIMARY KEY,
          project_id TEXT,
          asset_type TEXT NOT NULL DEFAULT 'reference_image',
          device_type TEXT,
          width INTEGER NOT NULL DEFAULT 0,
          height INTEGER NOT NULL DEFAULT 0,
          file_path TEXT NOT NULL,
          original_filename TEXT,
          metadata_json TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
        """
    )
    op.execute("DROP TABLE IF EXISTS generation_jobs")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS generation_jobs (
          id TEXT PRIMARY KEY,
          project_id TEXT,
          job_type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          progress INTEGER NOT NULL DEFAULT 0,
          input_json TEXT,
          output_json TEXT,
          error_message TEXT,
          retry_count INTEGER NOT NULL DEFAULT 0,
          logs TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS generation_jobs")
    op.execute("DROP TABLE IF EXISTS reference_images")
    op.execute("DROP TABLE IF EXISTS assets")

