"""Track destination coordinate provenance.

Revision ID: 0002_destination_coordinates
Revises: 0001_core_tables
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_destination_coordinates"
down_revision = "0001_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("destinations") as batch:
        batch.add_column(
            sa.Column("coordinate_verified", sa.Boolean(), server_default=sa.false(), nullable=False)
        )
        batch.add_column(
            sa.Column("coordinate_source", sa.String(40), server_default="approximate", nullable=False)
        )
        batch.add_column(sa.Column("provider_place_id", sa.String(100), nullable=True))
        batch.add_column(sa.Column("provider_adcode", sa.String(12), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("destinations") as batch:
        batch.drop_column("provider_adcode")
        batch.drop_column("provider_place_id")
        batch.drop_column("coordinate_source")
        batch.drop_column("coordinate_verified")
