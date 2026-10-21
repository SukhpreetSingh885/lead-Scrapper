"""Add total_contact_qualified to discovery_jobs

Revision ID: 005_add_contact_qualified_to_jobs
Revises: 004_search_preview_and_export_filename
Create Date: 2026-10-16 17:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_add_contact_qualified_to_jobs'
down_revision: Union[str, None] = '004_search_preview_and_export_filename'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('discovery_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('total_contact_qualified', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    with op.batch_alter_table('discovery_jobs', schema=None) as batch_op:
        batch_op.drop_column('total_contact_qualified')

