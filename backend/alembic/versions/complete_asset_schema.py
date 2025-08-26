"""Complete asset registry schema update

Revision ID: complete_asset_schema
Revises: af3a92009573
Create Date: 2025-08-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'complete_asset_schema'
down_revision = 'af3a92009573'
branch_labels = None
depends_on = None

def upgrade():
    """Add all missing columns to asset_registry table for 100% CSV coverage"""
    
    # Check if columns exist before adding them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('asset_registry')]
    
    # Core network fields (some may already exist)
    if 'gateway' not in existing_columns:
        op.add_column('asset_registry', sa.Column('gateway', sa.String(), nullable=True))
    if 'subnet_mask' not in existing_columns:
        op.add_column('asset_registry', sa.Column('subnet_mask', sa.String(), nullable=True))
    
    # System information updates
    if 'os_name' not in existing_columns:
        # If 'os' exists, rename it to 'os_name', otherwise create new
        if 'os' in existing_columns:
            op.alter_column('asset_registry', 'os', new_column_name='os_name')
        else:
            op.add_column('asset_registry', sa.Column('os_name', sa.String(), nullable=True))
    
    # Hardware resources
    if 'memory' not in existing_columns:
        # If 'memory_gb' exists, rename it to 'memory', otherwise create new
        if 'memory_gb' in existing_columns:
            op.alter_column('asset_registry', 'memory_gb', new_column_name='memory')
        else:
            op.add_column('asset_registry', sa.Column('memory', sa.String(), nullable=True))
    
    if 'cpu' not in existing_columns:
        op.add_column('asset_registry', sa.Column('cpu', sa.String(), nullable=True))
    if 'storage' not in existing_columns:
        op.add_column('asset_registry', sa.Column('storage', sa.String(), nullable=True))
    
    # Asset identity and metadata
    if 'vm_display_name' not in existing_columns:
        op.add_column('asset_registry', sa.Column('vm_display_name', sa.String(), nullable=True))
    
    # Organizational fields
    if 'owner' not in existing_columns:
        # If 'asset_owner' exists, rename it to 'owner', otherwise create new
        if 'asset_owner' in existing_columns:
            op.alter_column('asset_registry', 'asset_owner', new_column_name='owner')
        else:
            op.add_column('asset_registry', sa.Column('owner', sa.String(), nullable=True))
    
    if 'location' not in existing_columns:
        op.add_column('asset_registry', sa.Column('location', sa.String(), nullable=True))
    
    # Operational fields
    if 'status' not in existing_columns:
        op.add_column('asset_registry', sa.Column('status', sa.String(), nullable=True))
    if 'availability' not in existing_columns:
        op.add_column('asset_registry', sa.Column('availability', sa.String(), nullable=True))
    
    # Monitoring and compliance
    if 'itm_id' not in existing_columns:
        op.add_column('asset_registry', sa.Column('itm_id', sa.String(), nullable=True))
    
    # Create indexes for commonly queried fields
    try:
        op.create_index('ix_asset_registry_owner', 'asset_registry', ['owner'])
        op.create_index('ix_asset_registry_location', 'asset_registry', ['location'])
        op.create_index('ix_asset_registry_status', 'asset_registry', ['status'])
        op.create_index('ix_asset_registry_availability', 'asset_registry', ['availability'])
        op.create_index('ix_asset_registry_itm_id', 'asset_registry', ['itm_id'])
        op.create_index('ix_asset_registry_vm_display_name', 'asset_registry', ['vm_display_name'])
    except Exception:
        # Indexes might already exist
        pass

def downgrade():
    """Remove added columns and indexes"""
    
    # Drop indexes
    try:
        op.drop_index('ix_asset_registry_vm_display_name', 'asset_registry')
        op.drop_index('ix_asset_registry_itm_id', 'asset_registry')
        op.drop_index('ix_asset_registry_availability', 'asset_registry')
        op.drop_index('ix_asset_registry_status', 'asset_registry')
        op.drop_index('ix_asset_registry_location', 'asset_registry')
        op.drop_index('ix_asset_registry_owner', 'asset_registry')
    except Exception:
        pass
    
    # Check what columns exist before trying to drop/rename them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('asset_registry')]
    
    # Remove columns that were added (be careful with renames)
    columns_to_drop = ['subnet_mask', 'cpu', 'storage', 'vm_display_name', 'location', 'status', 'availability', 'itm_id']
    for col in columns_to_drop:
        if col in existing_columns:
            op.drop_column('asset_registry', col)
    
    # Handle renames - revert back to original names
    if 'os_name' in existing_columns and 'os' not in existing_columns:
        op.alter_column('asset_registry', 'os_name', new_column_name='os')
    
    if 'memory' in existing_columns and 'memory_gb' not in existing_columns:
        op.alter_column('asset_registry', 'memory', new_column_name='memory_gb')
    
    if 'owner' in existing_columns and 'asset_owner' not in existing_columns:
        op.alter_column('asset_registry', 'owner', new_column_name='asset_owner')
    
    # Drop gateway if it was added by this migration
    if 'gateway' in existing_columns:
        # Only drop if it was added by us (this is a simplification)
        try:
            op.drop_column('asset_registry', 'gateway')
        except Exception:
            pass
