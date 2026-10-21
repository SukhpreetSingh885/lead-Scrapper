"""add discovery_job_leads association and branch_id to discovery_job_items

Revision ID: 003_job_leads_association
Revises: 002_archive_demo_and_overpass
Create Date: 2026-10-16 13:38:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_job_leads_association'
down_revision: Union[str, None] = '002_archive_demo_and_overpass'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create discovery_job_leads association table
    op.create_table(
        'discovery_job_leads',
        sa.Column('job_id', sa.String(length=36), nullable=False),
        sa.Column('branch_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['discovery_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('job_id', 'branch_id')
    )
    op.create_index('ix_discovery_job_leads_job_id', 'discovery_job_leads', ['job_id'], unique=False)
    op.create_index('ix_discovery_job_leads_branch_id', 'discovery_job_leads', ['branch_id'], unique=False)

    # 2. Add branch_id to discovery_job_items
    with op.batch_alter_table('discovery_job_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('branch_id', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_discovery_job_items_branch_id', ['branch_id'])


def downgrade() -> None:
    with op.batch_alter_table('discovery_job_items', schema=None) as batch_op:
        batch_op.drop_index('ix_discovery_job_items_branch_id')
        batch_op.drop_column('branch_id')

    op.drop_index('ix_discovery_job_leads_branch_id', table_name='discovery_job_leads')
    op.drop_index('ix_discovery_job_leads_job_id', table_name='discovery_job_leads')
    op.drop_table('discovery_job_leads')

