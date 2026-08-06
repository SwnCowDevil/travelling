"""Create users, regions, and destinations.

Revision ID: 0001_core_tables
Revises: 0000_initial
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_core_tables"
down_revision = "0000_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("openid", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("openid"),
    )
    op.create_index("ix_users_openid", "users", ["openid"])
    op.create_table(
        "administrative_regions",
        sa.Column("code", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("parent_code", sa.String(12), nullable=True),
        sa.ForeignKeyConstraint(["parent_code"], ["administrative_regions.code"]),
    )
    op.create_index("ix_administrative_regions_name", "administrative_regions", ["name"])
    op.create_table(
        "destinations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("region_code", sa.String(12), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("suitable_months", sa.JSON(), nullable=False),
        sa.Column("season_tags", sa.JSON(), nullable=False),
        sa.Column("crowd_tags", sa.JSON(), nullable=False),
        sa.Column("transport_modes", sa.JSON(), nullable=False),
        sa.Column("climate", sa.JSON(), nullable=False),
        sa.Column("min_budget", sa.Integer(), nullable=True),
        sa.Column("max_budget", sa.Integer(), nullable=True),
        sa.Column("min_days", sa.Integer(), nullable=True),
        sa.Column("max_days", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("data_version", sa.String(32), nullable=False),
        sa.ForeignKeyConstraint(["region_code"], ["administrative_regions.code"]),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_destinations_code", "destinations", ["code"])
    op.create_index("ix_destinations_name", "destinations", ["name"])


def downgrade() -> None:
    op.drop_table("destinations")
    op.drop_table("administrative_regions")
    op.drop_table("users")
