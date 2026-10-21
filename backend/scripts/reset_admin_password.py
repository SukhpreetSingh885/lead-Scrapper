#!/usr/bin/env python3
"""
Secure Admin Password Reset Utility for India Leads Platform.
Requirements: 10, 11, 12, 14

Usage:
  # Interactive mode (prompts for password without echoing)
  python scripts/reset_admin_password.py --email admin@indialeads.internal

  # Command line mode (e.g. automated setup or scripting)
  python scripts/reset_admin_password.py --email admin@indialeads.internal --password "NewSecurePassword123"

Security Guarantees:
- Hashes password using Argon2id (RFC 9106 parameters).
- Never prints or echoes plaintext passwords in output.
- Stores only the cryptographic Argon2id hash in SQLite.
- Preserves all existing database records, leads, and search jobs.
"""

import sys
import os
import argparse
import getpass
import uuid

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, Organization


def reset_admin_password(email: str, password: str) -> bool:
    """
    Safely resets the admin password in the SQLite database using Argon2id.
    """
    if not email or "@" not in email:
        print("[-] Error: A valid email address is required.", file=sys.stderr)
        return False

    if not password or len(password) < 8:
        print("[-] Error: Password must be at least 8 characters long.", file=sys.stderr)
        return False

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()

        hashed = get_password_hash(password)

        if user:
            user.hashed_password = hashed
            user.is_active = True
            user.is_superuser = True
            db.commit()
            print(f"[+] Success: Password for admin '{user.email}' updated successfully.")
            print("[+] Algorithm: Argon2id (RFC 9106)")
            print("[+] Status: Active / Superuser")
            return True
        else:
            # If user does not exist, check organization and create the admin
            org = db.query(Organization).first()
            if not org:
                org = Organization(
                    id=str(uuid.uuid4()),
                    name="Default Organization",
                    slug="default-org"
                )
                db.add(org)
                db.flush()

            new_user = User(
                id=str(uuid.uuid4()),
                organization_id=org.id,
                email=email.strip().lower(),
                hashed_password=hashed,
                full_name=settings.ADMIN_FULL_NAME or "Principal Lead Admin",
                is_active=True,
                is_superuser=True
            )
            db.add(new_user)
            db.commit()
            print(f"[+] Success: Admin user '{new_user.email}' created and activated.")
            print("[+] Algorithm: Argon2id (RFC 9106)")
            return True
    except Exception as e:
        db.rollback()
        print(f"[-] Database error while updating password: {e}", file=sys.stderr)
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Securely reset or create administrator account password."
    )
    parser.add_argument(
        "--email",
        type=str,
        default=settings.ADMIN_EMAIL or "admin@indialeads.internal",
        help="Email address of administrator account"
    )
    parser.add_argument(
        "--password",
        type=str,
        default=None,
        help="New password (optional; if omitted, prompt will ask interactively)"
    )

    args = parser.parse_args()

    email = args.email.strip()
    password = args.password

    if not password:
        # Secure interactive prompt without echoing
        try:
            p1 = getpass.getpass(f"Enter new password for [{email}]: ")
            if not p1:
                print("[-] Password cannot be empty.", file=sys.stderr)
                sys.exit(1)
            p2 = getpass.getpass("Confirm new password: ")
            if p1 != p2:
                print("[-] Passwords do not match.", file=sys.stderr)
                sys.exit(1)
            password = p1
        except (KeyboardInterrupt, EOFError):
            print("\n[-] Cancelled by user.", file=sys.stderr)
            sys.exit(1)

    success = reset_admin_password(email=email, password=password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
