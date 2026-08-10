"""Store cached province and city map boundaries.

Revision ID: 0011_map_region_boundaries
Revises: 0010_custom_favorite_targets
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_map_region_boundaries"
down_revision = "0010_custom_favorite_targets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("destinations") as batch:
        batch.add_column(sa.Column("city_region_code", sa.String(12), nullable=True))
        batch.create_foreign_key(
            "fk_destinations_city_region", "administrative_regions",
            ["city_region_code"], ["code"], ondelete="SET NULL",
        )
    op.create_table(
        "region_boundaries",
        sa.Column("region_code", sa.String(12), primary_key=True),
        sa.Column("center_longitude", sa.Float(), nullable=False),
        sa.Column("center_latitude", sa.Float(), nullable=False),
        sa.Column("polygons", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False, server_default="amap"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["region_code"], ["administrative_regions.code"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("region_boundaries")
    with op.batch_alter_table("destinations") as batch:
        batch.drop_constraint("fk_destinations_city_region", type_="foreignkey")
        batch.drop_column("city_region_code")
