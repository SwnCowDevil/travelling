"""Add generated guide caches.

Revision ID: 0005_guide_caches
Revises: 0004_recommendation_sessions
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_guide_caches"
down_revision = "0004_recommendation_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guide_caches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("data_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("cache_key"),
    )
    op.create_index("ix_guide_caches_destination_id", "guide_caches", ["destination_id"])
    op.create_index("ix_guide_caches_cache_key", "guide_caches", ["cache_key"])


def downgrade() -> None:
    op.drop_index("ix_guide_caches_cache_key", table_name="guide_caches")
    op.drop_index("ix_guide_caches_destination_id", table_name="guide_caches")
    op.drop_table("guide_caches")
