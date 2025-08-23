"""remove_redundant_columns_from_far_rules

Revision ID: 3c32035d64ad
Revises: 7bd0bc1fde0e
Create Date: 2025-08-23 19:14:06.142160

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c32035d64ad'
down_revision = '7bd0bc1fde0e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove redundant columns from far_rules table
    # These columns are unused and their data is stored in the facts JSONB column
    op.drop_column('far_rules', 'src_raw')
    op.drop_column('far_rules', 'dst_raw')
    op.drop_column('far_rules', 'svc_raw')
    op.drop_column('far_rules', 'service_count')
    op.drop_column('far_rules', 'max_port_span')
    op.drop_column('far_rules', 'tuple_estimate')


def downgrade() -> None:
    # Restore the removed columns in case of rollback
    op.add_column('far_rules', sa.Column('src_raw', sa.Text(), nullable=True))
    op.add_column('far_rules', sa.Column('dst_raw', sa.Text(), nullable=True))
    op.add_column('far_rules', sa.Column('svc_raw', sa.Text(), nullable=True))
    op.add_column('far_rules', sa.Column('service_count', sa.Integer(), nullable=True))
    op.add_column('far_rules', sa.Column('max_port_span', sa.Integer(), nullable=True))
    op.add_column('far_rules', sa.Column('tuple_estimate', sa.BigInteger(), nullable=True))
