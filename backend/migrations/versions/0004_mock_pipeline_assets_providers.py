"""mock pipeline assets and provider placeholders

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-03
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE assets ADD COLUMN source TEXT NOT NULL DEFAULT 'uploaded'")
    op.execute("ALTER TABLE assets ADD COLUMN generation_job_id TEXT")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_providers (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          provider_type TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ai_providers")
