"""add_db_performance_improvements

Revision ID: 20251209145122
Revises: 3c32035d64ad
Create Date: 2025-12-09 14:51:22.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20251209145122'
down_revision = 'add_security_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================
    # Add updated_at column to far_rules
    # ============================================
    op.add_column('far_rules', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Backfill updated_at with created_at for existing records
    op.execute("""
        UPDATE far_rules 
        SET updated_at = created_at 
        WHERE updated_at IS NULL
    """)
    
    # Make updated_at non-nullable and set default
    op.alter_column('far_rules', 'updated_at',
                    nullable=False,
                    server_default=sa.text('CURRENT_TIMESTAMP'))
    
    # ============================================
    # Indexes for far_rules table
    # ============================================
    # Index on created_at for ordering queries
    op.create_index('ix_far_rules_created_at', 'far_rules', ['created_at'], unique=False)
    
    # Index on action for filtering by allow/deny
    op.create_index('ix_far_rules_action', 'far_rules', ['action'], unique=False)
    
    # Index on direction for filtering by direction
    op.create_index('ix_far_rules_direction', 'far_rules', ['direction'], unique=False)
    
    # GIN index on facts JSONB column for JSONB queries
    op.create_index('ix_far_rules_facts_gin', 'far_rules', ['facts'], 
                    unique=False, postgresql_using='gin')
    
    # Composite index on (request_id, action) for common filter combination
    op.create_index('ix_far_rules_request_id_action', 'far_rules', 
                    ['request_id', 'action'], unique=False)
    
    # Composite index on (request_id, created_at) for common ordering pattern
    op.create_index('ix_far_rules_request_id_created_at', 'far_rules', 
                    ['request_id', 'created_at'], unique=False)
    
    # ============================================
    # Indexes for far_requests table
    # ============================================
    # Index on status for frequently filtered queries
    op.create_index('ix_far_requests_status', 'far_requests', ['status'], unique=False)
    
    # Index on created_at for ordering
    op.create_index('ix_far_requests_created_at', 'far_requests', ['created_at'], unique=False)
    
    # ============================================
    # Indexes for far_rule_endpoints table
    # ============================================
    # Index on endpoint_type for joins (endpoint_type = 'source'/'destination')
    op.create_index('ix_far_rule_endpoints_endpoint_type', 'far_rule_endpoints', 
                    ['endpoint_type'], unique=False)
    
    # Composite index on (rule_id, endpoint_type) for common join pattern
    op.create_index('ix_far_rule_endpoints_rule_id_endpoint_type', 'far_rule_endpoints', 
                    ['rule_id', 'endpoint_type'], unique=False)
    
    # ============================================
    # Indexes for far_rule_services table
    # ============================================
    # Index on protocol for filtering by protocol
    op.create_index('ix_far_rule_services_protocol', 'far_rule_services', 
                    ['protocol'], unique=False)


def downgrade() -> None:
    # ============================================
    # Drop indexes
    # ============================================
    # far_rule_services indexes
    op.drop_index('ix_far_rule_services_protocol', table_name='far_rule_services')
    
    # far_rule_endpoints indexes
    op.drop_index('ix_far_rule_endpoints_rule_id_endpoint_type', table_name='far_rule_endpoints')
    op.drop_index('ix_far_rule_endpoints_endpoint_type', table_name='far_rule_endpoints')
    
    # far_requests indexes
    op.drop_index('ix_far_requests_created_at', table_name='far_requests')
    op.drop_index('ix_far_requests_status', table_name='far_requests')
    
    # far_rules indexes
    op.drop_index('ix_far_rules_request_id_created_at', table_name='far_rules')
    op.drop_index('ix_far_rules_request_id_action', table_name='far_rules')
    op.drop_index('ix_far_rules_facts_gin', table_name='far_rules')
    op.drop_index('ix_far_rules_direction', table_name='far_rules')
    op.drop_index('ix_far_rules_action', table_name='far_rules')
    op.drop_index('ix_far_rules_created_at', table_name='far_rules')
    
    # ============================================
    # Drop updated_at column from far_rules
    # ============================================
    op.drop_column('far_rules', 'updated_at')

