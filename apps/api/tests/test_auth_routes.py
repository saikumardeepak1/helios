import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models import ApiKey, Organization, User


async def _create_user(
    db_session: AsyncSession, email: str = "a@acme.com", password: str = "hunter2"
) -> User:
    org = Organization(name="Acme Corp")
    user = User(email=email, hashed_password=hash_password(password), role="admin")
    org.users.append(user)
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_login_with_valid_credentials_returns_tokens(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session, email="a@acme.com", password="hunter2")

    response = await client.post(
        "/v1/auth/login", json={"email": "a@acme.com", "password": "hunter2"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await _create_user(db_session, email="a@acme.com", password="hunter2")

    response = await client.post(
        "/v1/auth/login", json={"email": "a@acme.com", "password": "wrong"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_unknown_email_is_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/v1/auth/login", json={"email": "nobody@acme.com", "password": "hunter2"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_issues_new_token_pair(client: AsyncClient, db_session: AsyncSession) -> None:
    await _create_user(db_session, email="a@acme.com", password="hunter2")
    login_response = await client.post(
        "/v1/auth/login", json={"email": "a@acme.com", "password": "hunter2"}
    )
    refresh_token = login_response.json()["refresh_token"]

    response = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_refresh_rejects_an_access_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    access_token = create_access_token(str(user.id))

    response = await client.post("/v1/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_a_valid_session(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await _create_user(db_session, email="a@acme.com")
    token = create_access_token(str(user.id))

    response = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "a@acme.com"


@pytest.mark.asyncio
async def test_me_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_api_key_returns_raw_key_once_and_stores_only_hash(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await _create_user(db_session)
    token = create_access_token(str(user.id))

    response = await client.post(
        "/v1/auth/api-keys", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["key"].startswith("hel_live_")
    assert body["prefix"] == body["key"][: len(body["prefix"])]

    stored = await db_session.get(ApiKey, body["id"])
    assert stored is not None
    assert stored.hashed_key != body["key"]


@pytest.mark.asyncio
async def test_health_check_does_not_require_auth(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
