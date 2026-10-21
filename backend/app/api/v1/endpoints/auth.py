from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    needs_rehash,
    create_access_token,
    decode_access_token
)
from app.models import User, Organization
from app.schemas.user import UserLogin, Token, UserOut

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates authentication token from Authorization header or HttpOnly cookie.
    Guarantees:
    - Never automatically falls back to admin without credentials.
    - Rejects missing, malformed, or expired tokens with HTTP 401.
    - Rejects inactive user accounts with HTTP 403.
    """
    # 1. Check Bearer token in Authorization header
    auth_token = token

    # 2. If not provided in header, check HttpOnly session cookie
    if not auth_token:
        auth_token = request.cookies.get("access_token")

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Access forbidden.",
        )

    return user


@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticates user with email and password.
    Returns access token and sets secure HttpOnly cookie with SameSite protection.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account. Access forbidden."
        )

    # Transparently upgrade legacy password hashes (e.g. bcrypt -> Argon2id)
    if needs_rehash(user.hashed_password):
        user.hashed_password = get_password_hash(form_data.password)
        db.commit()

    access_token = create_access_token(subject=user.id)

    # Set secure HttpOnly cookie with SameSite protection for browser session
    cookie_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=cookie_max_age,
        expires=cookie_max_age,
        httponly=True,
        secure=False,  # Set to True when SSL/HTTPS is terminated
        samesite="lax",
        path="/"
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.post("/logout")
def logout(
    response: Response
):
    """
    Invalidates session by clearing HttpOnly authentication cookie.
    """
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        samesite="lax"
    )
    return {"success": True, "message": "Successfully logged out."}


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


