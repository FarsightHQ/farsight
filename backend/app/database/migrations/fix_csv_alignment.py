"""
Fix CSV alignment - add tool_update column and remove patch_level
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Check if tool_update column exists before adding
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'asset_registry' AND column_name = 'tool_update'
    """)).fetchone()
    
    if not result:
        print("Adding tool_update column...")
        op.add_column('asset_registry', sa.Column('tool_update', sa.String(), nullable=True))
        
        # Add index for tool_update
        try:
            op.create_index('ix_asset_registry_tool_update', 'asset_registry', ['tool_update'])
        except Exception as e:
            print(f"Index creation failed (may already exist): {e}")
    else:
        print("tool_update column already exists")
    
    # Check if patch_level column exists before removing
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'asset_registry' AND column_name = 'patch_level'
    """)).fetchone()
    
    if result:
        print("Removing patch_level column...")
        # Drop index first if it exists
        try:
            op.drop_index('ix_asset_registry_patch_level', 'asset_registry')
        except Exception as e:
            print(f"Index drop failed (may not exist): {e}")
        
        op.drop_column('asset_registry', 'patch_level')
    else:
        print("patch_level column does not exist")

def downgrade():
    # Add back patch_level column
    op.add_column('asset_registry', sa.Column('patch_level', sa.String(50), nullable=True))
    op.create_index('ix_asset_registry_patch_level', 'asset_registry', ['patch_level'])
    
    # Remove tool_update column
    try:
        op.drop_index('ix_asset_registry_tool_update', 'asset_registry')
    except Exception:
        pass
    op.drop_column('asset_registry', 'tool_update')
