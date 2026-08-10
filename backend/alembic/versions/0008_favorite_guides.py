"""Add editable favorite guide snapshots.

Revision ID: 0008_favorite_guides
Revises: 0007_visit_records
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_favorite_guides"
down_revision = "0007_visit_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorite_guides",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("generation_mode", sa.String(10), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("destination_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "destination_id"),
    )
    op.create_index("ix_favorite_guides_user_id", "favorite_guides", ["user_id"])
    op.create_index("ix_favorite_guides_destination_id", "favorite_guides", ["destination_id"])


def downgrade() -> None:
    op.drop_table("favorite_guides")
