"""base panels and generation jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-03
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS base_panels")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS base_panels (
          id TEXT PRIMARY KEY,
          project_id TEXT NOT NULL,
          style_profile_id TEXT NOT NULL,
          panel_type TEXT NOT NULL,
          device_type TEXT NOT NULL,
          width INTEGER NOT NULL,
          height INTEGER NOT NULL,
          texture TEXT,
          border_style TEXT,
          background_style TEXT,
          color_scheme TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
          FOREIGN KEY (style_profile_id) REFERENCES style_profiles(id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS generation_jobs (
          id TEXT PRIMARY KEY,
          project_id TEXT NOT NULL,
          job_type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          progress INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS generation_jobs")
    op.execute("DROP TABLE IF EXISTS base_panels")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS base_panels (
          id TEXT PRIMARY KEY,
          project_id TEXT NOT NULL,
          title TEXT NOT NULL,
          layout_type TEXT NOT NULL,
          width INTEGER NOT NULL,
          height INTEGER NOT NULL,
          notes TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        """
    )
