"""Add global risky_port_policy_entries table.

Revision ID: 20260408120000
Revises: 20260407120000
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa

revision = "20260408120000"
down_revision = "20260407120000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risky_port_policy_entries",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("protocol", sa.String(length=10), nullable=False),
        sa.Column("port_start", sa.Integer(), nullable=False),
        sa.Column("port_end", sa.Integer(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_risky_port_policy_entries_sort_order"),
        "risky_port_policy_entries",
        ["sort_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_risky_port_policy_entries_sort_order"), table_name="risky_port_policy_entries")
    op.drop_table("risky_port_policy_entries")
