"""add_hybrid_facts_support

Revision ID: 7bd0bc1fde0e
Revises: a0ff99d47334
Create Date: 2025-08-23 14:55:09.117764

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7bd0bc1fde0e'
down_revision = 'a0ff99d47334'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add facts column to far_rules table
    op.add_column('far_rules', sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Create far_tuple_facts table
    op.create_table('far_tuple_facts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('rule_id', sa.BigInteger(), nullable=False),
        sa.Column('source_cidr', sa.Text(), nullable=False),
        sa.Column('destination_cidr', sa.Text(), nullable=False),
        sa.Column('facts', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['far_rules.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_far_tuple_facts_id'), 'far_tuple_facts', ['id'], unique=False)
    op.create_index(op.f('ix_far_tuple_facts_rule_id'), 'far_tuple_facts', ['rule_id'], unique=False)
    op.create_index('ix_far_tuple_facts_tuple', 'far_tuple_facts', ['rule_id', 'source_cidr', 'destination_cidr'], unique=True)
    op.create_index('ix_far_tuple_facts_facts_gin', 'far_tuple_facts', ['facts'], postgresql_using='gin')


def downgrade() -> None:
    # Drop indexes and table
    op.drop_index('ix_far_tuple_facts_facts_gin', table_name='far_tuple_facts')
    op.drop_index('ix_far_tuple_facts_tuple', table_name='far_tuple_facts')
    op.drop_index(op.f('ix_far_tuple_facts_rule_id'), table_name='far_tuple_facts')
    op.drop_index(op.f('ix_far_tuple_facts_id'), table_name='far_tuple_facts')
    op.drop_table('far_tuple_facts')
    
    # Remove facts column from far_rules
    op.drop_column('far_rules', 'facts')
