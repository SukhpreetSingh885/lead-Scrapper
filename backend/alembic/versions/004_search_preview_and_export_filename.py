"""Add search preview fields to discovery_job_items and filename to exports

Revision ID: 004_search_preview_and_export_filename
Revises: 003_job_leads_association
Create Date: 2026-10-16 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_search_preview_and_export_filename'
down_revision: Union[str, None] = '003_job_leads_association'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add preview fields to discovery_job_items
    with op.batch_alter_table('discovery_job_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('mobile', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('whatsapp', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('state', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('source_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('is_saved', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('is_already_saved', sa.Boolean(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Add expires_at to discovery_jobs
    with op.batch_alter_table('discovery_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))

    # 3. Add filename to exports
    with op.batch_alter_table('exports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filename', sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('exports', schema=None) as batch_op:
        batch_op.drop_column('filename')

    with op.batch_alter_table('discovery_jobs', schema=None) as batch_op:
        batch_op.drop_column('expires_at')

    with op.batch_alter_table('discovery_job_items', schema=None) as batch_op:
        batch_op.drop_column('expires_at')
        batch_op.drop_column('is_already_saved')
        batch_op.drop_column('is_saved')
        batch_op.drop_column('source_code')
        batch_op.drop_column('state')
        batch_op.drop_column('city')
        batch_op.drop_column('email')
        batch_op.drop_column('whatsapp')
        batch_op.drop_column('mobile')
        batch_op.drop_column('category')

