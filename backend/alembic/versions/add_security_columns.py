"""Add DMZ/MZ, Confidentiality, and Integrity columns

Revision ID: add_security_columns
Revises: remove_unused_columns
Create Date: 2025-08-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_security_columns'
down_revision = 'remove_unused_columns'
branch_labels = None
depends_on = None

def upgrade():
    """Add DMZ/MZ, Confidentiality, and Integrity as separate columns"""
    
    # Check if columns exist before adding them
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [col['name'] for col in inspector.get_columns('asset_registry')]
    
    # Add the three security/compliance columns from CSV
    if 'dmz_mz' not in existing_columns:
        op.add_column('asset_registry', sa.Column('dmz_mz', sa.String(20), nullable=True))
    
    if 'confidentiality' not in existing_columns:
        op.add_column('asset_registry', sa.Column('confidentiality', sa.String(20), nullable=True))
    
    if 'integrity' not in existing_columns:
        op.add_column('asset_registry', sa.Column('integrity', sa.String(20), nullable=True))
    
    # Create indexes for these commonly queried security fields
    try:
        op.create_index('ix_asset_registry_dmz_mz', 'asset_registry', ['dmz_mz'])
        op.create_index('ix_asset_registry_confidentiality', 'asset_registry', ['confidentiality'])
        op.create_index('ix_asset_registry_integrity', 'asset_registry', ['integrity'])
    except Exception:
        # Indexes might already exist
        pass

def downgrade():
    """Remove the added security columns"""
    
    # Drop indexes first
    try:
        op.drop_index('ix_asset_registry_integrity', 'asset_registry')
        op.drop_index('ix_asset_registry_confidentiality', 'asset_registry')
        op.drop_index('ix_asset_registry_dmz_mz', 'asset_registry')
    except Exception:
        pass
    
    # Drop columns
    op.drop_column('asset_registry', 'integrity')
    op.drop_column('asset_registry', 'confidentiality')
    op.drop_column('asset_registry', 'dmz_mz')
