"""Fix data types for CSV compatibility

Revision ID: fix_data_types
Revises: complete_asset_schema
Create Date: 2025-08-26 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_data_types'
down_revision = 'complete_asset_schema'
branch_labels = None
depends_on = None

def upgrade():
    """Fix data types to be CSV-friendly (all strings except vcpu)"""
    
    # Change inet fields to varchar for easier CSV processing
    op.alter_column('asset_registry', 'ip_address', 
                   type_=sa.String(), 
                   postgresql_using='ip_address::text')
    
    op.alter_column('asset_registry', 'gateway',
                   type_=sa.String(),
                   postgresql_using='gateway::text')
    
    # Change memory from double precision to varchar to handle various formats
    op.alter_column('asset_registry', 'memory',
                   type_=sa.String(),
                   postgresql_using='memory::text')

def downgrade():
    """Revert data types back to original"""
    
    # Revert back to inet types
    op.alter_column('asset_registry', 'ip_address',
                   type_=sa.dialects.postgresql.INET(),
                   postgresql_using='ip_address::inet')
    
    op.alter_column('asset_registry', 'gateway', 
                   type_=sa.dialects.postgresql.INET(),
                   postgresql_using='gateway::inet')
    
    # Revert memory back to double precision
    op.alter_column('asset_registry', 'memory',
                   type_=sa.Float(),
                   postgresql_using='memory::double precision')
