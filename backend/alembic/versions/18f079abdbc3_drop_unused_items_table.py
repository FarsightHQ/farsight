"""drop_unused_items_table

Revision ID: 18f079abdbc3
Revises: 3c32035d64ad
Create Date: 2025-08-23 19:34:11.879730

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18f079abdbc3'
down_revision = '3c32035d64ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the unused items table
    op.drop_table('items')


def downgrade() -> None:
    # Recreate the items table if rollback is needed
    op.create_table('items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index(op.f('ix_items_name'), 'items', ['name'], unique=False)
