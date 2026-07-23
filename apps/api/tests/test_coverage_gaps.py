"""Targeted tests for edge-case branches identified by a coverage audit.

Each test here exists because a real code path wasn't exercised anywhere
else, not because the line count needed padding — see the PR description
for how each gap was found.
"""

import json
import logging
import sys
import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_session
from app.core.config import get_settings
from app.core.db import get_db
from app.core.logging import JsonFormatter
from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def _bearer(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.mark.asyncio
async def test_require_session_rejects_a_token_for_a_deleted_user(
    db_session: AsyncSession,
) -> None:
    # JWTs are stateless: a token stays valid until expiry even if the user
    # it names has since been deleted from the database.
    token = create_access_token(str(uuid.uuid4()))

    with pytest.raises(HTTPException) as exc_info:
        await require_session(credentials=_bearer(token), db=db_session)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_a_token_for_a_deleted_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token = create_refresh_token(str(uuid.uuid4()))

    response = await client.post("/v1/auth/refresh", json={"refresh_token": token})

    assert response.status_code == 401


def test_decode_token_rejects_a_validly_signed_token_missing_a_subject() -> None:
    # create_access_token always sets "sub", so this can only happen from a
    # malformed token — still worth guarding against, since it's signed with
    # our own secret and would otherwise pass signature verification.
    settings = get_settings()
    token = jwt.encode(
        {"type": TokenType.ACCESS.value}, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )

    with pytest.raises(InvalidTokenError, match="missing a subject"):
        decode_token(token, TokenType.ACCESS)


@pytest.mark.asyncio
async def test_get_db_yields_a_working_session() -> None:
    # Every route test overrides this dependency, so the real implementation
    # has never actually run end to end until now.
    agen = get_db()
    session = await anext(agen)
    try:
        assert session.bind is not None
    finally:
        await agen.aclose()


def test_json_formatter_includes_exception_traceback() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        record = logging.getLogger("app.test").makeRecord(
            "app.test", logging.ERROR, __file__, 1, "failed", (), sys.exc_info()
        )

    payload = json.loads(JsonFormatter().format(record))
    assert "ValueError: boom" in payload["exception"]
