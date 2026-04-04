"""Add tool_update column to asset_registry (matches ORM / CSV)

Revision ID: 20260404160000
Revises: 20251209145122
Create Date: 2026-04-04

"""
from alembic import op
import sqlalchemy as sa

revision = "20260404160000"
down_revision = "20251209145122"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("asset_registry")]
    if "tool_update" not in cols:
        op.add_column(
            "asset_registry",
            sa.Column("tool_update", sa.String(length=200), nullable=True),
        )
    inspector = sa.inspect(conn)
    indexes = [ix["name"] for ix in inspector.get_indexes("asset_registry")]
    if "ix_asset_registry_tool_update" not in indexes:
        op.create_index(
            "ix_asset_registry_tool_update",
            "asset_registry",
            ["tool_update"],
            unique=False,
        )


def downgrade() -> None:
    try:
        op.drop_index("ix_asset_registry_tool_update", table_name="asset_registry")
    except Exception:
        pass
    try:
        op.drop_column("asset_registry", "tool_update")
    except Exception:
        pass
