"""Add destination and region footprint statuses.

Revision ID: 0006_footprint_statuses
Revises: 0005_guide_caches
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_footprint_statuses"
down_revision = "0005_guide_caches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status_check = "status IN ('want', 'visited', 'revisit', 'avoid')"
    op.create_table(
        "destination_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.CheckConstraint(status_check, name="ck_destination_status_value"),
        sa.UniqueConstraint("user_id", "destination_id"),
    )
    op.create_index("ix_destination_statuses_user_id", "destination_statuses", ["user_id"])
    op.create_index("ix_destination_statuses_destination_id", "destination_statuses", ["destination_id"])
    op.create_table(
        "region_statuses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("region_code", sa.String(12), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_code"], ["administrative_regions.code"], ondelete="CASCADE"),
        sa.CheckConstraint(status_check, name="ck_region_status_value"),
        sa.UniqueConstraint("user_id", "region_code"),
    )
    op.create_index("ix_region_statuses_user_id", "region_statuses", ["user_id"])
    op.create_index("ix_region_statuses_region_code", "region_statuses", ["region_code"])


def downgrade() -> None:
    op.drop_table("region_statuses")
    op.drop_table("destination_statuses")
