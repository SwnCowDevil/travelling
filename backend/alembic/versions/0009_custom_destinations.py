"""Add user custom destinations.

Revision ID: 0009_custom_destinations
Revises: 0008_favorite_guides
Create Date: 2026-08-10
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_custom_destinations"
down_revision = "0008_favorite_guides"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("custom_destinations", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), nullable=False), sa.Column("amap_poi_id", sa.String(128), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("address", sa.String(500), nullable=False), sa.Column("region_name", sa.String(200), nullable=False), sa.Column("latitude", sa.Float(), nullable=False), sa.Column("longitude", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id", "amap_poi_id"))
    op.create_index("ix_custom_destinations_user_id", "custom_destinations", ["user_id"])


def downgrade() -> None:
    op.drop_table("custom_destinations")
