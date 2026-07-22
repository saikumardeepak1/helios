from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key
from app.models import ApiKey, Organization, Run
from app.workers.queue import get_queue


async def _create_org_with_api_key(db_session: AsyncSession) -> tuple[Organization, str]:
    org = Organization(name="Acme Corp")
    raw_key, prefix, hashed_key = generate_api_key()
    org.api_keys.append(ApiKey(prefix=prefix, hashed_key=hashed_key))
    db_session.add(org)
    await db_session.commit()
    return org, raw_key


def _trace_payload() -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "agent": {"name": "support-bot", "version": "1.0.0"},
        "run": {
            "status": "completed",
            "started_at": now,
            "spans": [
                {
                    "local_id": "root",
                    "kind": "llm_call",
                    "started_at": now,
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "tool_calls": [],
                }
            ],
        },
    }


@pytest.mark.asyncio
async def test_ingest_trace_with_valid_api_key(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, raw_key = await _create_org_with_api_key(db_session)
    get_queue().empty()

    response = await client.post(
        "/v1/ingest/traces",
        headers={"Authorization": f"Bearer {raw_key}"},
        json=_trace_payload(),
    )

    assert response.status_code == 202
    body = response.json()
    assert body["span_count"] == 1
    assert body["status"] == "completed"

    run = await db_session.get(Run, body["run_id"])
    assert run is not None
    assert get_queue().count == 1


@pytest.mark.asyncio
async def test_ingest_trace_without_api_key_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/v1/ingest/traces", json=_trace_payload())
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ingest_trace_with_malformed_payload_is_rejected(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    _, raw_key = await _create_org_with_api_key(db_session)

    response = await client.post(
        "/v1/ingest/traces",
        headers={"Authorization": f"Bearer {raw_key}"},
        json={"agent": {"name": "support-bot"}},
    )

    assert response.status_code == 422
