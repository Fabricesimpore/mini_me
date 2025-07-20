"""add pgvector extension and update embedding column

Revision ID: add_vector_extension
Revises: 
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_vector_extension'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create pgvector extension if not exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Note: The embedding column is already created as JSON in the existing schema
    # If you want to use pgvector's vector type, you would need to:
    # 1. Add a new column with vector type
    # 2. Migrate data from JSON to vector
    # 3. Drop the old column
    # 
    # For now, we'll keep using JSON for compatibility and ease of deployment
    # The application code handles this transparently
    
    # Create indexes for better performance
    op.create_index(
        'idx_memories_user_type',
        'memories',
        ['user_id', 'memory_type']
    )
    
    op.create_index(
        'idx_memories_created_at',
        'memories',
        ['created_at']
    )
    
    # Create index on memory relations
    op.create_index(
        'idx_memory_relations_source',
        'memory_relations',
        ['source_memory_id']
    )
    
    op.create_index(
        'idx_memory_relations_target',
        'memory_relations',
        ['target_memory_id']
    )
    
    op.create_index(
        'idx_memory_relations_strength',
        'memory_relations',
        ['strength']
    )


def downgrade():
    # Drop indexes
    op.drop_index('idx_memory_relations_strength', 'memory_relations')
    op.drop_index('idx_memory_relations_target', 'memory_relations')
    op.drop_index('idx_memory_relations_source', 'memory_relations')
    op.drop_index('idx_memories_created_at', 'memories')
    op.drop_index('idx_memories_user_type', 'memories')
    
    # Note: We don't drop the pgvector extension as it might be used by other applications