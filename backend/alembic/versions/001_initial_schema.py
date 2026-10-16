"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-16 10:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_organizations_slug', 'organizations', ['slug'])

    # users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_org_id', 'users', ['organization_id'])

    # companies
    op.create_table(
        'companies',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('legal_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('website_domain', sa.String(length=255), nullable=True),
        sa.Column('primary_category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_companies_org_id', 'companies', ['organization_id'])
    op.create_index('ix_companies_norm_name', 'companies', ['normalized_name'])
    op.create_index('ix_companies_domain', 'companies', ['website_domain'])
    op.create_index('ix_companies_category', 'companies', ['primary_category'])
    op.create_index('idx_company_org_normname', 'companies', ['organization_id', 'normalized_name'])

    # lead_sources
    op.create_table(
        'lead_sources',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('requires_api_key', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_lead_sources_code', 'lead_sources', ['code'])

    # source_permissions
    op.create_table(
        'source_permissions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('source_id', sa.String(length=36), sa.ForeignKey('lead_sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('license_name', sa.String(length=255), nullable=False),
        sa.Column('permitted_storage', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('permitted_export', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('permitted_enrichment', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('license_terms_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_source_permissions_source_id', 'source_permissions', ['source_id'])

    # branches
    op.create_table(
        'branches',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('company_id', sa.String(length=36), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_name', sa.String(length=255), nullable=False),
        sa.Column('normalized_branch_name', sa.String(length=255), nullable=False),
        sa.Column('address_line', sa.String(length=500), nullable=True),
        sa.Column('locality', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('country', sa.String(length=50), nullable=False, server_default='India'),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('is_headquarters', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('source_id', sa.String(length=36), sa.ForeignKey('lead_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_reference', sa.String(length=255), nullable=True),
        sa.Column('source_permission_status', sa.String(length=50), nullable=False, server_default='permitted_storage'),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('enrichment_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_branches_company_id', 'branches', ['company_id'])
    op.create_index('ix_branches_city', 'branches', ['city'])
    op.create_index('ix_branches_state', 'branches', ['state'])
    op.create_index('ix_branches_pincode', 'branches', ['pincode'])
    op.create_index('ix_branches_norm_name', 'branches', ['normalized_branch_name'])
    op.create_index('ix_branches_is_demo', 'branches', ['is_demo'])
    op.create_index('idx_branch_city_pincode', 'branches', ['city', 'pincode'])
    op.create_index('idx_branch_norm_city', 'branches', ['normalized_branch_name', 'city'])

    # business_contacts
    op.create_table(
        'business_contacts',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contact_type', sa.String(length=20), nullable=False),
        sa.Column('original_value', sa.String(length=255), nullable=False),
        sa.Column('normalized_value', sa.String(length=255), nullable=False),
        sa.Column('is_primary', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='website_enrichment'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_contacts_branch_id', 'business_contacts', ['branch_id'])
    op.create_index('ix_contacts_norm_val', 'business_contacts', ['normalized_value'])
    op.create_index('idx_contact_branch_normval', 'business_contacts', ['branch_id', 'contact_type', 'normalized_value'], unique=True)
    op.create_index('idx_contact_type_normval', 'business_contacts', ['contact_type', 'normalized_value'])

    # social_profiles
    op.create_table(
        'social_profiles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('profile_url', sa.String(length=500), nullable=False),
        sa.Column('original_url', sa.String(length=500), nullable=True),
        sa.Column('handle', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_social_branch_id', 'social_profiles', ['branch_id'])
    op.create_index('idx_social_branch_platform', 'social_profiles', ['branch_id', 'platform', 'profile_url'], unique=True)

    # india_locations
    op.create_table(
        'india_locations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('state', sa.String(length=100), nullable=False),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('locality', sa.String(length=255), nullable=True),
        sa.Column('pincode', sa.String(length=10), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
    )
    op.create_index('ix_india_locations_state', 'india_locations', ['state'])
    op.create_index('ix_india_locations_city', 'india_locations', ['city'])
    op.create_index('idx_india_loc_city_state', 'india_locations', ['city', 'state'])
    op.create_index('idx_india_loc_pincode', 'india_locations', ['pincode'])

    # discovery_jobs
    op.create_table(
        'discovery_jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('location_input', sa.String(length=255), nullable=False),
        sa.Column('resolved_city', sa.String(length=100), nullable=False),
        sa.Column('resolved_state', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('max_leads', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('source_code', sa.String(length=50), nullable=False, server_default='demo_fixture'),
        sa.Column('filters_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_discovered', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_eligible', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_inserted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_duplicates_flagged', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_jobs_org_id', 'discovery_jobs', ['organization_id'])
    op.create_index('ix_jobs_status', 'discovery_jobs', ['status'])
    op.create_index('ix_jobs_city', 'discovery_jobs', ['resolved_city'])

    # discovery_job_items
    op.create_table(
        'discovery_job_items',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('job_id', sa.String(length=36), sa.ForeignKey('discovery_jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('business_name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=100), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('is_eligible_for_crm', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('rejection_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_job_items_job_id', 'discovery_job_items', ['job_id'])

    # enrichment_jobs
    op.create_table(
        'enrichment_jobs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('pages_crawled', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('phones_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('socials_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_enrich_branch_id', 'enrichment_jobs', ['branch_id'])

    # duplicate_candidates
    op.create_table(
        'duplicate_candidates',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('existing_branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('candidate_branch_id', sa.String(length=36), sa.ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_score', sa.Float(), nullable=False),
        sa.Column('match_reasons', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending_review'),
        sa.Column('resolved_by_user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_dup_existing_id', 'duplicate_candidates', ['existing_branch_id'])
    op.create_index('ix_dup_candidate_id', 'duplicate_candidates', ['candidate_branch_id'])
    op.create_index('ix_dup_status', 'duplicate_candidates', ['status'])
    op.create_index('idx_dup_pair', 'duplicate_candidates', ['existing_branch_id', 'candidate_branch_id'], unique=True)

    # exports
    op.create_table(
        'exports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_format', sa.String(length=10), nullable=False),
        sa.Column('filter_criteria', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('download_token', sa.String(length=100), nullable=False, unique=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_exports_org_id', 'exports', ['organization_id'])
    op.create_index('ix_exports_token', 'exports', ['download_token'])

    # audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.String(length=36), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_audit_org_id', 'audit_logs', ['organization_id'])
    op.create_index('ix_audit_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_entity', 'audit_logs', ['entity_type'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('exports')
    op.drop_table('duplicate_candidates')
    op.drop_table('enrichment_jobs')
    op.drop_table('discovery_job_items')
    op.drop_table('discovery_jobs')
    op.drop_table('india_locations')
    op.drop_table('social_profiles')
    op.drop_table('business_contacts')
    op.drop_table('branches')
    op.drop_table('source_permissions')
    op.drop_table('lead_sources')
    op.drop_table('companies')
    op.drop_table('users')
    op.drop_table('organizations')

