"""Add recommendation sessions.

Revision ID: 0004_recommendation_sessions
Revises: 0003_ai_profiles
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_recommendation_sessions"
down_revision = "0003_ai_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.JSON(), nullable=False),
        sa.Column("candidate_codes", sa.JSON(), nullable=False),
        sa.Column("shown_codes", sa.JSON(), nullable=False),
        sa.Column("batches", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("data_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_recommendation_sessions_user_id", "recommendation_sessions", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_recommendation_sessions_user_id", table_name="recommendation_sessions")
    op.drop_table("recommendation_sessions")
