"""add integrations data to user

Revision ID: add_integrations_data
Revises: add_cognitive_profile_tables
Create Date: 2024-01-18 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_integrations_data'
down_revision = 'add_cognitive_profile_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add integrations_data column to users table
    op.add_column('users', sa.Column('integrations_data', postgresql.JSON, nullable=True))


def downgrade() -> None:
    # Remove integrations_data column from users table
    op.drop_column('users', 'integrations_data')