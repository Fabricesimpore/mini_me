"""add cognitive profile tables

Revision ID: add_cognitive_profile_tables
Revises: add_vector_extension
Create Date: 2024-01-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_cognitive_profile_tables'
down_revision = 'add_vector_extension'
branch_labels = None
depends_on = None


def upgrade():
    # Create cognitive_profiles table
    op.create_table('cognitive_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('openness', sa.Float(), nullable=True),
        sa.Column('conscientiousness', sa.Float(), nullable=True),
        sa.Column('extraversion', sa.Float(), nullable=True),
        sa.Column('agreeableness', sa.Float(), nullable=True),
        sa.Column('neuroticism', sa.Float(), nullable=True),
        sa.Column('communication_formality', sa.Float(), nullable=True),
        sa.Column('communication_verbosity', sa.Float(), nullable=True),
        sa.Column('preferred_communication_channels', sa.JSON(), nullable=True),
        sa.Column('decision_speed', sa.Float(), nullable=True),
        sa.Column('risk_tolerance', sa.Float(), nullable=True),
        sa.Column('analytical_vs_intuitive', sa.Float(), nullable=True),
        sa.Column('work_style', sa.JSON(), nullable=True),
        sa.Column('peak_productivity_hours', sa.JSON(), nullable=True),
        sa.Column('preferred_task_types', sa.JSON(), nullable=True),
        sa.Column('learning_preferences', sa.JSON(), nullable=True),
        sa.Column('curiosity_level', sa.Float(), nullable=True),
        sa.Column('social_energy', sa.Float(), nullable=True),
        sa.Column('relationship_depth', sa.Float(), nullable=True),
        sa.Column('conflict_style', sa.JSON(), nullable=True),
        sa.Column('interest_categories', sa.JSON(), nullable=True),
        sa.Column('expertise_areas', sa.JSON(), nullable=True),
        sa.Column('emotional_stability', sa.Float(), nullable=True),
        sa.Column('stress_triggers', sa.JSON(), nullable=True),
        sa.Column('coping_mechanisms', sa.JSON(), nullable=True),
        sa.Column('core_values', sa.JSON(), nullable=True),
        sa.Column('motivators', sa.JSON(), nullable=True),
        sa.Column('routine_preference', sa.Float(), nullable=True),
        sa.Column('multitasking_preference', sa.Float(), nullable=True),
        sa.Column('profile_confidence', sa.Float(), nullable=True),
        sa.Column('trait_confidences', sa.JSON(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('analysis_count', sa.Float(), nullable=True),
        sa.Column('data_points', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create profile_analysis_logs table
    op.create_table('profile_analysis_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_type', sa.String(), nullable=True),
        sa.Column('source_data', sa.JSON(), nullable=True),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('adjustments', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['cognitive_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_cognitive_profiles_user_id', 'cognitive_profiles', ['user_id'])
    op.create_index('idx_profile_analysis_logs_profile_id', 'profile_analysis_logs', ['profile_id'])
    op.create_index('idx_profile_analysis_logs_created_at', 'profile_analysis_logs', ['created_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_profile_analysis_logs_created_at', 'profile_analysis_logs')
    op.drop_index('idx_profile_analysis_logs_profile_id', 'profile_analysis_logs')
    op.drop_index('idx_cognitive_profiles_user_id', 'cognitive_profiles')
    
    # Drop tables
    op.drop_table('profile_analysis_logs')
    op.drop_table('cognitive_profiles')