import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ToolCallOut(BaseModel):
    id: uuid.UUID
    tool_name: str
    arguments: dict | None
    result: dict | None

    model_config = {"from_attributes": True}


class SpanOut(BaseModel):
    id: uuid.UUID
    parent_span_id: uuid.UUID | None
    kind: str
    model: str | None
    input: dict | None
    output: dict | None
    prompt_tokens: int
    completion_tokens: int
    started_at: datetime
    ended_at: datetime | None
    tool_calls: list[ToolCallOut]

    model_config = {"from_attributes": True}


class RunSummaryOut(BaseModel):
    id: uuid.UUID
    agent_name: str
    status: str
    started_at: datetime
    ended_at: datetime | None
    span_count: int
    risk_score: int


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
