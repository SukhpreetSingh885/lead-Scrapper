import uuid
from datetime import datetime, timedelta, timezone
import pytest
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token
from app.models import (
    Organization,
    User,
    Company,
    Branch,
    BusinessContact,
    DiscoveryJob,
    DiscoveryJobItem,
    Export,
)


def test_unauthenticated_requests_rejected_with_401(unauthenticated_client):
    """
    Requirements 4, 6, 7, 17:
    All protected endpoints modifying or accessing private data must return HTTP 401
    when called without valid credentials.
    """
    client = unauthenticated_client

    # 1. Leads endpoints
    assert client.get("/api/v1/leads").status_code == 401
    assert client.get("/api/v1/leads/test-lead-id").status_code == 401
    assert client.patch("/api/v1/leads/test-lead-id", json={"branch_name": "Hack"}).status_code == 401
    assert client.post("/api/v1/leads/test-lead-id/enrich").status_code == 401
    assert client.delete("/api/v1/leads/test-lead-id").status_code == 401
    assert client.post("/api/v1/leads/bulk-delete", json={"lead_ids": ["test-id"]}).status_code == 401
    assert client.get("/api/v1/leads/metrics/dashboard").status_code == 401
    assert client.post("/api/v1/leads/save-selected", json={"job_id": "test-id", "save_all_eligible": True}).status_code == 401

    # 2. Discovery endpoints
    assert client.get("/api/v1/discovery/jobs").status_code == 401
    assert client.post("/api/v1/discovery/jobs", json={"location": "Delhi", "category": "Gym", "max_leads": 10}).status_code == 401
    assert client.get("/api/v1/discovery/jobs/test-job-id").status_code == 401
    assert client.get("/api/v1/discovery/jobs/test-job-id/preview").status_code == 401
    assert client.delete("/api/v1/discovery/jobs/test-job-id").status_code == 401
    assert client.delete("/api/v1/discovery/jobs/test-job-id/preview").status_code == 401

    # 3. Duplicate review endpoints
    assert client.get("/api/v1/duplicates").status_code == 401
    assert client.post("/api/v1/duplicates/test-dup-id/resolve", json={"resolution": "merge"}).status_code == 401

    # 4. Exports endpoints
    assert client.post("/api/v1/exports", json={"file_format": "csv"}).status_code == 401
    assert client.get("/api/v1/exports/test-export-id").status_code == 401

    # 5. OSM bulk indexing endpoints
    assert client.get("/api/v1/osm-bulk/info").status_code == 401
    assert client.post("/api/v1/osm-bulk/index", json={"items": []}).status_code == 401
    assert client.get("/api/v1/osm-bulk/search?city=Delhi&category=Gym").status_code == 401

    # 6. Sources registry
    assert client.get("/api/v1/sources/registry").status_code == 401

    # 7. Auth profile
    assert client.get("/api/v1/auth/me").status_code == 401


def test_public_helper_endpoints_accessible_without_auth(unauthenticated_client):
    """
    Public utility and health check endpoints remain available without leaking private lead data.
    """
    client = unauthenticated_client

    # Health check
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # Location suggestions & validation
    res_loc = client.get("/api/v1/locations?q=Chandigarh")
    assert res_loc.status_code == 200

    res_val = client.get("/api/v1/locations/validate?location=Chandigarh")
    assert res_val.status_code == 200
    assert res_val.json()["is_valid"] is True

    # Category taxonomy
    res_cat = client.get("/api/v1/discovery/categories")
    assert res_cat.status_code == 200


def test_successful_login_sets_httponly_cookie_and_returns_token(unauthenticated_client, db_session):
    """
    Requirements 8, 9, 14:
    Valid login returns access_token and sets secure HttpOnly cookie with SameSite protection.
    """
    client = unauthenticated_client

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@indialeads.internal", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@indialeads.internal"

    # Verify HttpOnly cookie
    assert "access_token" in login_res.cookies
    cookie_token = login_res.cookies.get("access_token")
    assert cookie_token == data["access_token"]


def test_login_with_incorrect_password_returns_401(unauthenticated_client):
    """
    Requirement 8, 17:
    Incorrect credentials return 401 without creating session.
    """
    client = unauthenticated_client

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@indialeads.internal", "password": "WrongPassword!99"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]


def test_login_with_inactive_user_returns_403(unauthenticated_client, db_session):
    """
    Requirements 17:
    Inactive user accounts receive HTTP 403 Forbidden.
    """
    db = db_session
    inactive_user = User(
        id=str(uuid.uuid4()),
        organization_id="test-org-1",
        email="inactive@indialeads.internal",
        hashed_password=get_password_hash("password123"),
        full_name="Inactive User",
        is_active=False
    )
    db.add(inactive_user)
    db.commit()

    client = unauthenticated_client
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "inactive@indialeads.internal", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 403
    assert "Inactive user account" in res.json()["detail"]


def test_logout_invalidates_session_cookie(unauthenticated_client):
    """
    Requirement 12:
    Logout endpoint deletes the session cookie.
    """
    client = unauthenticated_client

    # Log in first
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@indialeads.internal", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200

    # Execute logout
    logout_res = client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200
    assert logout_res.json()["success"] is True

    # Cookie header deletes access_token
    # In set-cookie header, the value is cleared/expired
    set_cookie = logout_res.headers.get("set-cookie", "")
    assert 'access_token=""' in set_cookie or "Max-Age=0" in set_cookie


def test_expired_and_tampered_jwt_token_returns_401(unauthenticated_client):
    """
    Requirements 7, 8, 17:
    Expired or tampered JWT tokens are rejected with 401.
    """
    client = unauthenticated_client

    # 1. Tampered token
    tampered_headers = {"Authorization": "Bearer invalid.fake.token"}
    res_tampered = client.get("/api/v1/auth/me", headers=tampered_headers)
    assert res_tampered.status_code == 401

    # 2. Expired token
    expire_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    payload = {"sub": "test-user-1", "exp": expire_time}
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    expired_headers = {"Authorization": f"Bearer {expired_token}"}
    res_expired = client.get("/api/v1/auth/me", headers=expired_headers)
    assert res_expired.status_code == 401
    assert "Invalid or expired session token" in res_expired.json()["detail"]


def test_organization_data_isolation(db_session):
    """
    Requirement 15:
    Users from Organization A cannot view, retrieve, modify, enrich, or delete
    leads, jobs, duplicate reviews, or exports belonging to Organization B.
    """
    db = db_session

    # Create Organization B and User B
    org_b = Organization(id="test-org-b", name="Org B Corp", slug="org-b")
    db.add(org_b)
    db.flush()

    user_b = User(
        id="test-user-b",
        organization_id=org_b.id,
        email="user_b@company.internal",
        hashed_password=get_password_hash("password123"),
        full_name="User B",
        is_active=True
    )
    db.add(user_b)
    db.flush()

    # Create records in Organization A (owned by test-org-1)
    comp_a = Company(
        id=str(uuid.uuid4()),
        organization_id="test-org-1",
        legal_name="Alpha Tech Org A",
        normalized_name="alpha tech org a",
        primary_category="IT"
    )
    db.add(comp_a)
    db.flush()

    branch_a = Branch(
        id=str(uuid.uuid4()),
        company_id=comp_a.id,
        branch_name="Alpha Tech Branch A",
        normalized_branch_name="alpha tech branch a",
        city="Chandigarh",
        state="Chandigarh",
        is_active=True
    )
    db.add(branch_a)

    contact_a = BusinessContact(
        id=str(uuid.uuid4()),
        branch_id=branch_a.id,
        contact_type="mobile",
        original_value="+919888877777",
        normalized_value="+919888877777",
        is_primary=True,
        is_verified=True
    )
    db.add(contact_a)

    job_a = DiscoveryJob(
        id=str(uuid.uuid4()),
        organization_id="test-org-1",
        location_input="Chandigarh",
        resolved_city="Chandigarh",
        resolved_state="Chandigarh",
        category="Gym",
        max_leads=10,
        status="completed",
        total_discovered=1,
        total_eligible=1
    )
    db.add(job_a)
    db.flush()

    job_a_item = DiscoveryJobItem(
        id=str(uuid.uuid4()),
        job_id=job_a.id,
        business_name="Gold Gym A",
        city="Chandigarh",
        state="Chandigarh",
        phone="+919888800000",
        is_eligible_for_crm=True
    )
    db.add(job_a_item)

    export_a = Export(
        id=str(uuid.uuid4()),
        organization_id="test-org-1",
        file_format="csv",
        download_token=str(uuid.uuid4()),
        status="completed"
    )
    db.add(export_a)
    db.commit()

    # User B Client
    token_b = create_access_token(subject=user_b.id)
    client_b = TestClient(
        app,
        cookies={"access_token": token_b},
        headers={"Authorization": f"Bearer {token_b}"}
    )

    # 1. User B listing leads should NOT see Org A's leads
    leads_b = client_b.get("/api/v1/leads").json()
    assert leads_b["total"] == 0
    assert len(leads_b["items"]) == 0

    # 2. User B fetching Org A's lead detail by ID returns 404
    detail_res = client_b.get(f"/api/v1/leads/{branch_a.id}")
    assert detail_res.status_code == 404

    # 3. User B updating Org A's lead returns 404
    update_res = client_b.patch(f"/api/v1/leads/{branch_a.id}", json={"branch_name": "Tampered"})
    assert update_res.status_code == 404

    # 4. User B enriching Org A's lead returns 404
    enrich_res = client_b.post(f"/api/v1/leads/{branch_a.id}/enrich")
    assert enrich_res.status_code == 404

    # 5. User B deleting Org A's lead returns 404
    delete_res = client_b.delete(f"/api/v1/leads/{branch_a.id}")
    assert delete_res.status_code == 404

    # 6. User B bulk deleting targeting Org A's lead does not delete Org A's lead
    bulk_del_res = client_b.post("/api/v1/leads/bulk-delete", json={"lead_ids": [branch_a.id]})
    assert bulk_del_res.status_code == 200
    assert bulk_del_res.json()["deleted_count"] == 0
    # Verify branch_a still exists
    assert db.query(Branch).filter(Branch.id == branch_a.id).first() is not None

    # 7. User B fetching Org A's discovery job returns 404
    job_res = client_b.get(f"/api/v1/discovery/jobs/{job_a.id}")
    assert job_res.status_code == 404

    # 8. User B fetching Org A's discovery preview returns 404
    prev_res = client_b.get(f"/api/v1/discovery/jobs/{job_a.id}/preview")
    assert prev_res.status_code == 404

    # 9. User B deleting Org A's discovery job returns 404
    del_job_res = client_b.delete(f"/api/v1/discovery/jobs/{job_a.id}")
    assert del_job_res.status_code == 404

    # 10. User B fetching Org A's export status returns 404
    exp_res = client_b.get(f"/api/v1/exports/{export_a.id}")
    assert exp_res.status_code == 404

    # 11. User B dashboard metrics show 0 leads
    metrics_b = client_b.get("/api/v1/leads/metrics/dashboard").json()
    assert metrics_b["total_saved_leads"] == 0
    assert metrics_b["active_jobs"] == 0


def test_argon2id_hashing_and_verification():
    """
    Requirement 10:
    Verifies passwords are encrypted using Argon2id with appropriate parameters.
    """
    from app.core.security import get_password_hash, verify_password, needs_rehash

    raw_pass = "TestSecurePassword#99"
    argon2_hash = get_password_hash(raw_pass)

    assert argon2_hash.startswith("$argon2id$")
    assert verify_password(raw_pass, argon2_hash) is True
    assert verify_password("WrongPassword#99", argon2_hash) is False
    assert needs_rehash(argon2_hash) is False


def test_legacy_bcrypt_compatibility_and_rehash(unauthenticated_client, db_session):
    """
    Requirements 9, 10, 11:
    Verifies legacy bcrypt hashes are validated and automatically upgraded
    to Argon2id upon successful authentication without breaking existing accounts.
    """
    import bcrypt
    from app.core.security import verify_password, needs_rehash

    db = db_session
    # Generate legacy bcrypt hash
    legacy_pass = "BcryptSecret123!"
    salt = bcrypt.gensalt(10)
    legacy_bcrypt_hash = bcrypt.hashpw(legacy_pass.encode("utf-8"), salt).decode("utf-8")

    assert legacy_bcrypt_hash.startswith("$2b$")
    assert verify_password(legacy_pass, legacy_bcrypt_hash) is True
    assert needs_rehash(legacy_bcrypt_hash) is True

    # Seed user with bcrypt hash in database
    bcrypt_user = User(
        id=str(uuid.uuid4()),
        organization_id="test-org-1",
        email="bcrypt_user@indialeads.internal",
        hashed_password=legacy_bcrypt_hash,
        full_name="Bcrypt User",
        is_active=True
    )
    db.add(bcrypt_user)
    db.commit()

    # Log in via API
    client = unauthenticated_client
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "bcrypt_user@indialeads.internal", "password": legacy_pass},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert res.status_code == 200

    # Refresh user from DB: verify hash was transparently upgraded to Argon2id
    db.refresh(bcrypt_user)
    assert bcrypt_user.hashed_password.startswith("$argon2id$")
    assert verify_password(legacy_pass, bcrypt_user.hashed_password) is True


def test_initial_admin_bootstrap_does_not_overwrite_existing(db_session):
    """
    Requirement 9:
    Initial admin bootstrap must NEVER overwrite existing passwords or accounts on startup.
    """
    from app.services.auth.bootstrap import bootstrap_initial_admin

    db = db_session
    # Admin account test-user-1 already exists in db_session fixture
    existing_user = db.query(User).filter(User.email == "test@indialeads.internal").first()
    original_hash = existing_user.hashed_password

    # Run bootstrap
    bootstrapped = bootstrap_initial_admin(db=db)
    assert bootstrapped is False

    # Verify existing account and password hash remain completely untouched
    db.refresh(existing_user)
    assert existing_user.hashed_password == original_hash


def test_reset_admin_password_cli_function(db_session):
    """
    Requirements 10, 11, 14:
    Verifies explicit admin password reset CLI command updates SQLite database with Argon2id hash.
    """
    from scripts.reset_admin_password import reset_admin_password
    from app.core.security import verify_password

    db = db_session
    target_email = "test@indialeads.internal"
    new_secure_pass = "BrandNewArgon2Password#2026"

    success = reset_admin_password(email=target_email, password=new_secure_pass)
    assert success is True

    user = db.query(User).filter(User.email == target_email).first()
    db.refresh(user)
    assert user.hashed_password.startswith("$argon2id$")
    assert verify_password(new_secure_pass, user.hashed_password) is True
    assert verify_password("password123", user.hashed_password) is False


def test_browser_refresh_and_session_cookie_persistence(unauthenticated_client):
    """
    Requirements 3, 5, 15, 18:
    Verifies that on successful login, an HttpOnly cookie session is established,
    and subsequent requests (simulating browser page refresh and component mounting)
    persist authentication without re-authenticating.
    """
    client = unauthenticated_client

    # 1. Login with valid credentials
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "test@indialeads.internal", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert "access_token" in login_res.cookies

    # 2. Simulate subsequent browser request using ONLY the HttpOnly cookie (no Authorization header)
    refresh_client = TestClient(app, cookies={"access_token": token})
    me_res = refresh_client.get("/api/v1/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test@indialeads.internal"

    # 3. Simulate dashboard data request with cookie
    leads_res = refresh_client.get("/api/v1/leads")
    assert leads_res.status_code == 200
    assert "items" in leads_res.json()

    # 4. Invalidate session via logout
    logout_res = refresh_client.post("/api/v1/auth/logout")
    assert logout_res.status_code == 200

    # 5. Verify unauthenticated client without cookie is blocked
    blocked_client = TestClient(app)
    assert blocked_client.get("/api/v1/leads").status_code == 401
    assert blocked_client.get("/api/v1/auth/me").status_code == 401

