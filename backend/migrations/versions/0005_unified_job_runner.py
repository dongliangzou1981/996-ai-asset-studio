"""unified job runner fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-03
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE assets ADD COLUMN thumbnail_path TEXT")
    op.execute("ALTER TABLE generation_jobs ADD COLUMN provider_id TEXT")
    op.execute("ALTER TABLE generation_jobs ADD COLUMN output_preview_path TEXT")
    op.execute("ALTER TABLE ai_providers ADD COLUMN type TEXT")
    op.execute("ALTER TABLE ai_providers ADD COLUMN config_json TEXT")
    op.execute("UPDATE ai_providers SET type = provider_type WHERE type IS NULL")
    op.execute("UPDATE ai_providers SET config_json = '{}' WHERE config_json IS NULL")


def downgrade() -> None:
    pass
