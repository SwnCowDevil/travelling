"""Store AI provenance for favorite guides.

Revision ID: 0012_favorite_ai_provenance
Revises: 0011_map_region_boundaries
"""
from alembic import op
import sqlalchemy as sa


revision = "0012_favorite_ai_provenance"
down_revision = "0011_map_region_boundaries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("favorite_guides") as batch:
        batch.add_column(
            sa.Column(
                "source", sa.String(10), nullable=False, server_default="unknown"
            )
        )
        batch.add_column(
            sa.Column(
                "user_edited", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("favorite_guides") as batch:
        batch.drop_column("user_edited")
        batch.drop_column("source")
