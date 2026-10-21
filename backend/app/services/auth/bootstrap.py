import logging
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models import Organization, User

logger = logging.getLogger("india_leads_platform.auth.bootstrap")


def bootstrap_initial_admin(db: Optional[Session] = None) -> bool:
    """
    Bootstraps the initial administrator account ONLY when no admin user exists in the database.
    
    Guarantees (Requirements 7, 8, 9, 10, 11, 12):
    - Reads initial credentials from backend/.env (settings.ADMIN_EMAIL, settings.ADMIN_INITIAL_PASSWORD).
    - NEVER overwrites existing administrator accounts or passwords on startup.
    - Hashes password with Argon2id; stores ONLY password hashes in SQLite.
    - Never logs or prints plaintext credentials.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        from sqlalchemy import or_

        admin_email = (settings.ADMIN_EMAIL or "").strip().lower()
        initial_password = settings.ADMIN_INITIAL_PASSWORD

        # Check if an administrator or any user with admin email already exists
        existing_admin = db.query(User).filter(
            or_(
                User.is_superuser == True,
                User.email == admin_email
            )
        ).first() if admin_email else db.query(User).filter(User.is_superuser == True).first()

        if existing_admin:
            logger.debug("Existing administrator account found. Skipping initial admin bootstrap.")
            return False

        # If no initial password is configured, cannot bootstrap
        if not admin_email or not initial_password:
            logger.info("No admin user found and ADMIN_INITIAL_PASSWORD not configured. Skipping admin bootstrap.")
            return False

        # Ensure default organization exists
        org = db.query(Organization).first()
        if not org:
            org = Organization(
                id=str(uuid.uuid4()),
                name="Default Organization",
                slug="default-org"
            )
            db.add(org)
            db.flush()

        # Hash password securely with Argon2id
        hashed_password = get_password_hash(initial_password)

        new_admin = User(
            id=str(uuid.uuid4()),
            organization_id=org.id,
            email=admin_email,
            hashed_password=hashed_password,
            full_name=settings.ADMIN_FULL_NAME or "Principal Lead Admin",
            is_active=True,
            is_superuser=True
        )
        db.add(new_admin)
        db.commit()
        logger.info(f"Initial administrator account '{admin_email}' successfully bootstrapped with Argon2id.")
        return True
    except Exception as e:
        logger.error(f"Error during initial admin bootstrap: {e}")
        db.rollback()
        return False
    finally:
        if close_session:
            db.close()
