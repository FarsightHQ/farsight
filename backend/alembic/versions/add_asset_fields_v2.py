"""Add comprehensive asset fields v2

Revision ID: add_asset_fields_v2
Revises: 
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '674f2744c8ee'
down_revision = 'af3a92009573'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to asset_registry table
    op.add_column('asset_registry', sa.Column('gateway', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('subnet_mask', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('os_name', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('memory', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('cpu', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('storage', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('vm_display_name', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('owner', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('location', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('status', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('availability', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('itm_id', sa.String(), nullable=True))

    # Rename existing columns to match new schema
    try:
        op.alter_column('asset_registry', 'os', new_column_name='os_name_old')
        op.alter_column('asset_registry', 'memory_gb', new_column_name='memory_gb_old')
        op.alter_column('asset_registry', 'asset_owner', new_column_name='owner_old')
    except Exception:
        # Columns might not exist, continue
        pass

def downgrade():
    # Remove new columns
    op.drop_column('asset_registry', 'itm_id')
    op.drop_column('asset_registry', 'availability')
    op.drop_column('asset_registry', 'status')
    op.drop_column('asset_registry', 'location')
    op.drop_column('asset_registry', 'owner')
    op.drop_column('asset_registry', 'vm_display_name')
    op.drop_column('asset_registry', 'storage')
    op.drop_column('asset_registry', 'cpu')
    op.drop_column('asset_registry', 'memory')
    op.drop_column('asset_registry', 'os_name')
    op.drop_column('asset_registry', 'subnet_mask')
    op.drop_column('asset_registry', 'gateway')

    # Restore old column names
    try:
        op.alter_column('asset_registry', 'os_name_old', new_column_name='os')
        op.alter_column('asset_registry', 'memory_gb_old', new_column_name='memory_gb')
        op.alter_column('asset_registry', 'owner_old', new_column_name='asset_owner')
    except Exception:
        pass
