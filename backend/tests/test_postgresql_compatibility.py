import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import psycopg2

from app.core.config import Settings
from app.models import (
    Base, Organization, User, Company, Branch, BusinessContact,
    SocialProfile, DiscoveryJob, DiscoveryJobItem, LeadSource,
    IndiaLocation
)
from app.core.security import verify_password, get_password_hash
from app.services.auth.bootstrap import bootstrap_initial_admin
from app.services.exports.excel_export import ExcelExportService
from app.services.exports.csv_export import CsvExportService

PG_TEST_URL = os.environ.get("PG_TEST_URL", "postgresql://postgres@127.0.0.1:5433/test_india_leads")


@pytest.fixture(scope="module")
def pg_engine():
    """
    Connects to the test PostgreSQL instance. Skips tests if PostgreSQL is unreachable.
    """
    try:
        engine = create_engine(PG_TEST_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            pass
        yield engine
        engine.dispose()
    except Exception as e:
        pytest.skip(f"PostgreSQL test database not reachable at {PG_TEST_URL}: {e}")


@pytest.fixture(scope="module")
def pg_session(pg_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=pg_engine)
    session = TestingSession()
    yield session
    session.close()


def test_postgresql_driver_and_dialect(pg_engine):
    assert pg_engine.dialect.name == "postgresql"


def test_postgresql_admin_and_org_bootstrap(pg_session):
    admin = pg_session.query(User).filter(User.email == "admin@indialeads.internal").first()
    if not admin:
        org = Organization(id="pg-test-org-1", name="Postgres Test Org", slug="pg-test-org")
        pg_session.add(org)
        pg_session.flush()

        admin = User(
            id="pg-test-admin-1",
            organization_id=org.id,
            email="admin@indialeads.internal",
            hashed_password=get_password_hash("NeonSecure123!"),
            full_name="Postgres Admin",
            is_active=True,
            is_superuser=True
        )
        pg_session.add(admin)
        pg_session.commit()

    assert admin is not None
    assert admin.organization is not None
    assert verify_password("NeonSecure123!", admin.hashed_password) or verify_password("NeonSecurePassword123!", admin.hashed_password)


def test_postgresql_leads_and_contact_types(pg_session):
    admin = pg_session.query(User).filter(User.email == "admin@indialeads.internal").first()
    assert admin is not None

    company = Company(
        organization_id=admin.organization_id,
        legal_name="City Care Clinic Mohali",
        normalized_name="city care clinic",
        primary_category="Clinic"
    )
    pg_session.add(company)
    pg_session.flush()

    branch = Branch(
        company_id=company.id,
        branch_name="City Care Clinic Sector 70",
        normalized_branch_name="city care clinic sector 70",
        city="Mohali",
        state="Punjab",
        country="India",
        is_active=True,
        is_demo=False
    )
    pg_session.add(branch)
    pg_session.flush()

    contact_mobile = BusinessContact(
        branch_id=branch.id,
        contact_type="mobile",
        original_value="+91 9888877777",
        normalized_value="+919888877777",
        is_primary=True,
        is_verified=True,
        source="overpass"
    )
    contact_landline = BusinessContact(
        branch_id=branch.id,
        contact_type="phone",
        original_value="0172-5000000",
        normalized_value="+911725000000",
        is_primary=False,
        is_verified=True,
        source="website"
    )
    pg_session.add_all([contact_mobile, contact_landline])
    pg_session.commit()

    # Query back
    saved_branch = pg_session.query(Branch).filter(Branch.id == branch.id).first()
    assert saved_branch is not None
    assert len(saved_branch.contacts) == 2

    # Verify export generation works from PostgreSQL
    xlsx_bytes = ExcelExportService.generate_xlsx_bytes([saved_branch])
    assert len(xlsx_bytes) > 1000

    csv_stream = list(CsvExportService.generate_csv_stream([saved_branch]))
    csv_str = "".join(csv_stream)
    assert "+919888877777" in csv_str


def test_database_url_normalization_postgres_prefix():
    # Render & Neon often provide postgres://...
    cfg = Settings(DATABASE_URL="postgres://user:pass@host:5432/dbname?sslmode=require")
    assert cfg.DATABASE_URL.startswith("postgresql://")
    assert cfg.is_postgres is True
    assert cfg.is_sqlite is False

