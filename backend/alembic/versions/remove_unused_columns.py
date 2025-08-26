"""Remove columns not available in CSV

Revision ID: remove_unused_columns
Revises: fix_data_types
Create Date: 2025-08-26 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_unused_columns'
down_revision = 'fix_data_types'
branch_labels = None
depends_on = None

def upgrade():
    """Remove columns that are not available in the CSV file"""
    
    # Check if columns exist before trying to drop them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('asset_registry')]
    
    # Columns to remove (not available in CSV)
    columns_to_remove = [
        'subnet_mask',      # Not in CSV
        'cpu',              # Not in CSV (only vCPU is available)
        'storage',          # Not in CSV
        'business_unit',    # Not in CSV
        'owner',            # Not in CSV
        'asset_criticality', # Not in CSV
        'status',           # Not in CSV
        'security_zone',    # Not in CSV
    ]
    
    # Drop indexes first (if they exist)
    indexes_to_drop = [
        'ix_asset_registry_owner',
        'ix_asset_registry_status',
    ]
    
    for index_name in indexes_to_drop:
        try:
            op.drop_index(index_name, 'asset_registry')
        except Exception:
            # Index might not exist
            pass
    
    # Remove columns that don't exist in CSV
    for column in columns_to_remove:
        if column in existing_columns:
            op.drop_column('asset_registry', column)

def downgrade():
    """Re-add the removed columns"""
    
    # Re-add the dropped columns
    op.add_column('asset_registry', sa.Column('subnet_mask', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('cpu', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('storage', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('business_unit', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('owner', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('asset_criticality', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('status', sa.String(), nullable=True))
    op.add_column('asset_registry', sa.Column('security_zone', sa.String(), nullable=True))
    
    # Re-create indexes
    try:
        op.create_index('ix_asset_registry_owner', 'asset_registry', ['owner'])
        op.create_index('ix_asset_registry_status', 'asset_registry', ['status'])
    except Exception:
        pass
