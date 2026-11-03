from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.refresh_token import RefreshToken
from backend.app.schemas.user import UserCreate, UserResponse
from backend.app.schemas.auth import Token, LoginRequest, RefreshResponse
from backend.app.api.deps import get_current_user
from typing import Optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role or "analyst",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _issue_tokens(user: User, db: Session, response: Response) -> Token:
    """Create a new access token and refresh token pair, set refresh cookie."""
    access_token = create_access_token(subject=user.id)
    raw_refresh = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    expires = refresh_token_expiry()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires,
        revoked=False,
    )
    db.add(rt)
    db.commit()

    # Update last login timestamp
    from datetime import datetime, timezone
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Set HttpOnly cookie for browser clients
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,   # Set True in production (HTTPS)
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth",
    )

    return Token(access_token=access_token, token_type="bearer", refresh_token=raw_refresh)


@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return _issue_tokens(user, db, response)


@router.post("/login/json", response_model=Token)
def login_json(
    credentials: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return _issue_tokens(user, db, response)


@router.post("/refresh", response_model=RefreshResponse)
def refresh_access_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """Exchange a valid refresh token for a new access token (and rotate the refresh token)."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
        )

    token_hash = hash_refresh_token(refresh_token)
    rt = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
        )
        .first()
    )
    if not rt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked refresh token",
        )

    from datetime import datetime, timezone
    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        rt.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )

    # Revoke old token (rotation)
    rt.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == rt.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Issue new pair
    token_response = _issue_tokens(user, db, response)
    return RefreshResponse(access_token=token_response.access_token, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke the current refresh token and clear the session cookie."""
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if rt:
            rt.revoked = True
            db.commit()

    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    return None


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
