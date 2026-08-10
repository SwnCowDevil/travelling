"""Allow favorites for custom destinations.

Revision ID: 0010_custom_favorite_targets
Revises: 0009_custom_destinations
"""
from alembic import op
import sqlalchemy as sa

revision="0010_custom_favorite_targets"
down_revision="0009_custom_destinations"
branch_labels=None
depends_on=None

def upgrade():
    with op.batch_alter_table("favorite_guides") as batch:
        batch.alter_column("destination_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("custom_destination_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("destination_type", sa.String(10), nullable=False, server_default="public"))
        batch.create_foreign_key("fk_favorite_custom_destination", "custom_destinations", ["custom_destination_id"], ["id"], ondelete="CASCADE")
        batch.create_unique_constraint("uq_favorite_user_custom", ["user_id", "custom_destination_id"])
        batch.create_check_constraint("ck_favorite_one_target", "(destination_id IS NOT NULL) != (custom_destination_id IS NOT NULL)")

def downgrade():
    raise RuntimeError("Downgrade not supported after custom favorite migration")
