import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ToolCallOut(BaseModel):
    id: uuid.UUID
    tool_name: str
    arguments: dict | None
    result: dict | None

    model_config = ConfigDict(from_attributes=True)


class SpanOut(BaseModel):
    id: uuid.UUID
    parent_span_id: uuid.UUID | None = Field(
        description="Id of this span's parent, or null for a top-level span."
    )
    kind: str
    model: str | None = Field(description="LLM model used, if this span was an LLM call.")
    input: dict | None
    output: dict | None
    prompt_tokens: int
    completion_tokens: int
    started_at: datetime
    ended_at: datetime | None
    tool_calls: list[ToolCallOut]

    model_config = ConfigDict(from_attributes=True)


class RunSummaryOut(BaseModel):
    id: uuid.UUID
    agent_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    span_count: int
    risk_score: int = Field(description="0-100; see docs/TDD.md for how this is computed.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "6c1e4f2b-2435-43fc-882b-e0a9beb8165c",
                    "agent_name": "support-bot",
                    "status": "completed",
                    "started_at": "2026-01-01T00:00:00Z",
                    "ended_at": "2026-01-01T00:00:05Z",
                    "span_count": 3,
                    "risk_score": 0,
                }
            ]
        }
    )


class RunDetailOut(BaseModel):
    id: uuid.UUID
    agent_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    risk_score: int
    spans: list[SpanOut]


class AgentCostOut(BaseModel):
    agent_name: str
    cost_usd: Decimal


class DailyCostOut(BaseModel):
    day: date
    cost_usd: Decimal


class CostSummaryOut(BaseModel):
    total_usd: Decimal
    by_agent: list[AgentCostOut]
    by_day: list[DailyCostOut]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "total_usd": "12.4500",
                    "by_agent": [{"agent_name": "support-bot", "cost_usd": "12.4500"}],
                    "by_day": [{"day": "2026-01-01", "cost_usd": "12.4500"}],
                }
            ]
        }
    )


class AlertOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID = Field(description="The run this alert was raised for.")
    agent_name: str
    category: str = Field(description="'pii' or 'prompt_injection'.")
    severity: str = Field(description="'medium', 'high', or 'critical'.")
    detail: str = Field(description="Human-readable summary of what was detected.")
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "0a893895-11cd-46c9-9d0b-d144216a501b",
                    "run_id": "6c1e4f2b-2435-43fc-882b-e0a9beb8165c",
                    "agent_name": "support-bot",
                    "category": "pii",
                    "severity": "high",
                    "detail": "Detected 1 PII finding(s): ssn",
                    "created_at": "2026-01-01T00:00:05Z",
                }
            ]
        }
    )
