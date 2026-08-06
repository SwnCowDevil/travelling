"""Add encrypted personal AI profiles.

Revision ID: 0003_ai_profiles
Revises: 0002_destination_coordinates
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_ai_profiles"
down_revision = "0002_destination_coordinates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("protocol", sa.String(40), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("group_note", sa.String(100), nullable=True),
        sa.Column("encrypted_token", sa.String(2000), nullable=False),
        sa.Column("token_last_four", sa.String(4), nullable=False),
        sa.Column("connection_status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("ai_profiles")
