"""Add source_url and evidence to business_contacts

Revision ID: 006_contact_source_and_evidence
Revises: 005_add_contact_qualified_to_jobs
Create Date: 2026-10-16 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_contact_source_and_evidence'
down_revision: Union[str, None] = '005_add_contact_qualified_to_jobs'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('business_contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('evidence', sa.String(500), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('business_contacts', schema=None) as batch_op:
        batch_op.drop_column('evidence')
        batch_op.drop_column('source_url')

