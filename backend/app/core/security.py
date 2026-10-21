from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings

ALGORITHM = "HS256"

# Argon2id password hasher (RFC 9106 recommended parameters)
_argon2_hasher = PasswordHasher(
    time_cost=3,        # 3 iterations
    memory_cost=65536,  # 64 MiB
    parallelism=4,      # 4 lanes
    hash_len=32,
    salt_len=16
)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against an Argon2id hash or legacy Bcrypt hash.
    Safely handles malformed hashes and protects against timing attacks.
    """
    if not plain_password or not hashed_password:
        return False

    # 1. Primary verification: Argon2id ($argon2id$ / $argon2i$ / $argon2d$)
    if hashed_password.startswith("$argon2"):
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError):
            return False
        except Exception:
            return False

    # 2. Backward-compatible verification: Legacy Bcrypt ($2a$, $2b$, $2y$)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            password_bytes = plain_password.encode("utf-8")
            hash_bytes = hashed_password.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False

    return False


def get_password_hash(password: str) -> str:
    """
    Hashes a password using Argon2id.
    """
    return _argon2_hasher.hash(password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Returns True if an existing hash is not using Argon2id or needs parameter upgrading.
    """
    if not hashed_password or not hashed_password.startswith("$argon2"):
        return True
    return _argon2_hasher.check_needs_rehash(hashed_password)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
