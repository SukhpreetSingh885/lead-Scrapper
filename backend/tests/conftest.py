import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.main import app
from app.models import (
    Base,
    Organization,
    User,
    LeadSource,
    SourcePermission,
    IndiaLocation,
    Company,
    Branch,
    BusinessContact,
)
from app.core.security import get_password_hash, create_access_token

# Setup test in-memory SQLite database with StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal.configure(bind=engine_test)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine_test)
    db = SessionLocal()

    # Seed baseline fixtures
    org = Organization(id="test-org-1", name="Test Org", slug="test-org")
    db.add(org)
    db.flush()

    user = User(
        id="test-user-1",
        organization_id=org.id,
        email="test@indialeads.internal",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        is_active=True,
        is_superuser=True
    )
    db.add(user)

    demo_source = LeadSource(
        id="source-demo",
        name="Deterministic Demo Fixture",
        code="demo_fixture",
        is_active=True
    )
    db.add(demo_source)
    db.flush()

    perm = SourcePermission(
        source_id=demo_source.id,
        license_name="Demo Test License",
        permitted_storage=True,
        permitted_export=True,
        permitted_enrichment=True
    )
    db.add(perm)

    licensed_source = LeadSource(
        id="source-licensed",
        name="Licensed Commercial Dataset",
        code="licensed_csv",
        is_active=True
    )
    db.add(licensed_source)
    db.flush()

    perm_lic = SourcePermission(
        source_id=licensed_source.id,
        license_name="B2B Commercial Directory License",
        permitted_storage=True,
        permitted_export=True,
        permitted_enrichment=True
    )
    db.add(perm_lic)

    overpass_source = LeadSource(
        id="source-overpass",
        name="OpenStreetMap Overpass API",
        code="overpass",
        is_active=True
    )
    db.add(overpass_source)
    db.flush()

    perm_overpass = SourcePermission(
        source_id=overpass_source.id,
        license_name="Open Database License (ODbL) 1.0",
        permitted_storage=True,
        permitted_export=True,
        permitted_enrichment=True
    )
    db.add(perm_overpass)

    # Seed India locations for validation
    locs = [
        IndiaLocation(city="Mohali", state="Punjab", district="SAS Nagar", locality="Phase 7", pincode="160062"),
        IndiaLocation(city="Mohali", state="Punjab", district="SAS Nagar", locality="Phase 3B2", pincode="160059"),
        IndiaLocation(city="Chandigarh", state="Chandigarh", district="Chandigarh", locality="Sector 17", pincode="160017"),
        IndiaLocation(city="Delhi", state="Delhi", district="New Delhi", locality="Connaught Place", pincode="110001"),
        IndiaLocation(city="Ludhiana", state="Punjab", district="Ludhiana", locality="Civil Lines", pincode="141001"),
        IndiaLocation(city="Mumbai", state="Maharashtra", district="Mumbai Suburban", locality="Andheri West", pincode="400058"),
        IndiaLocation(city="Bengaluru", state="Karnataka", district="Bengaluru Urban", locality="Koramangala", pincode="560034"),
        IndiaLocation(city="Jaipur", state="Rajasthan", district="Jaipur", locality="C-Scheme", pincode="302001"),
        IndiaLocation(city="Pune", state="Maharashtra", district="Pune", locality="Koregaon Park", pincode="411001"),
    ]
    for l in locs:
        db.add(l)

    db.commit()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def unauthenticated_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token(subject="test-user-1")
    with TestClient(
        app,
        cookies={"access_token": token},
        headers={"Authorization": f"Bearer {token}"}
    ) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(client):
    return client

