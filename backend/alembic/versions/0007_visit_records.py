"""Add dated visit records.

Revision ID: 0007_visit_records
Revises: 0006_footprint_statuses
Create Date: 2026-08-06
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_visit_records"
down_revision = "0006_footprint_statuses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visit_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("visited_on", sa.Date(), nullable=False),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column("idempotency_key", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "idempotency_key"),
    )
    op.create_index("ix_visit_records_user_id", "visit_records", ["user_id"])
    op.create_index("ix_visit_records_destination_id", "visit_records", ["destination_id"])


def downgrade() -> None:
    op.drop_table("visit_records")
