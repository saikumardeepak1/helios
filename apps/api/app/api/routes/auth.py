import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.db import get_db
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    verify_password,
)
from app.models import ApiKey, User
from app.schemas.auth import (
    ApiKeyCreateResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Log in with email and password")
async def login(
    payload: LoginRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Exchange dashboard credentials for a JWT access/refresh token pair.
    Use the access token as `Authorization: Bearer <token>` on every other
    `/v1/*` dashboard route (everything except `/v1/ingest/*`, which uses
    an API key instead).
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    subject = str(user.id)
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Get a new token pair")
async def refresh(
    payload: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Trade a refresh token for a new access/refresh pair once the access
    token has expired. Issues a fresh refresh token on every call rather
    than reusing the one passed in — see docs/TDD.md for why the old one
    isn't explicitly revoked server-side yet.
    """
    try:
        subject = decode_token(payload.refresh_token, TokenType.REFRESH)
        user_id = uuid.UUID(subject)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc

    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.get("/me", response_model=UserResponse, summary="Get the current user")
async def me(current_user: User = Depends(require_session)) -> User:
    """Returns the user identified by the bearer token — a quick way to
    check a session is still valid and see which organization it belongs to.
    """
    return current_user


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an ingestion API key",
)
async def create_api_key(
    current_user: User = Depends(require_session), db: AsyncSession = Depends(get_db)
) -> ApiKeyCreateResponse:
    """Generate a new API key for the current user's organization, for use
    with `helios-sdk` / `POST /v1/ingest/traces`. The raw key is only ever
    returned in this response — store it now, since it can't be retrieved
    again afterward.
    """
    raw_key, prefix, hashed_key = generate_api_key()
    api_key = ApiKey(
        organization_id=current_user.organization_id, prefix=prefix, hashed_key=hashed_key
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreateResponse(id=api_key.id, prefix=api_key.prefix, key=raw_key)
