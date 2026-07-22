from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_api_key, require_session
from app.core.security import create_access_token, generate_api_key, hash_password
from app.models import ApiKey, Organization, User


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_require_api_key_resolves_organization(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    raw_key, prefix, hashed_key = generate_api_key()
    org.api_keys.append(ApiKey(prefix=prefix, hashed_key=hashed_key))
    db_session.add(org)
    await db_session.commit()

    resolved = await require_api_key(credentials=_bearer(raw_key), db=db_session)

    assert resolved.name == "Acme Corp"


@pytest.mark.asyncio
async def test_require_api_key_rejects_unknown_key(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(credentials=_bearer("hel_live_does-not-exist"), db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_api_key_rejects_revoked_key(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    raw_key, prefix, hashed_key = generate_api_key()
    org.api_keys.append(
        ApiKey(prefix=prefix, hashed_key=hashed_key, revoked_at=datetime.now(UTC))
    )
    db_session.add(org)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(credentials=_bearer(raw_key), db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_api_key_rejects_missing_credentials(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(credentials=None, db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_session_resolves_user(db_session: AsyncSession) -> None:
    org = Organization(name="Acme Corp")
    user = User(email="a@acme.com", hashed_password=hash_password("x"))
    org.users.append(user)
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(str(user.id))
    resolved = await require_session(credentials=_bearer(token), db=db_session)

    assert resolved.email == "a@acme.com"


@pytest.mark.asyncio
async def test_require_session_rejects_garbage_token(db_session: AsyncSession) -> None:
    with pytest.raises(HTTPException) as exc_info:
        await require_session(credentials=_bearer("not-a-token"), db=db_session)

    assert exc_info.value.status_code == 401
