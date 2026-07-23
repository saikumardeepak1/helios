import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import InvalidTokenError, TokenType, decode_token, hash_api_key
from app.models import ApiKey, Organization, User

_bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")

    hashed = hash_api_key(credentials.credentials)
    result = await db.execute(
        select(ApiKey).where(ApiKey.hashed_key == hashed, ApiKey.revoked_at.is_(None))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API key")

    org_result = await db.execute(
        select(Organization).where(Organization.id == api_key.organization_id)
    )
    organization = org_result.scalar_one_or_none()
    if organization is None:  # pragma: no cover
        # Unreachable in practice: api_keys.organization_id is a foreign key
        # with ON DELETE CASCADE, so an ApiKey row can't outlive its
        # Organization. Kept as defense-in-depth against DB-level corruption
        # rather than trusting the constraint unconditionally in auth code.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")

    return organization


async def require_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing session token")

    try:
        subject = decode_token(credentials.credentials, TokenType.ACCESS)
        user_id = uuid.UUID(subject)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session token") from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")

    return user
