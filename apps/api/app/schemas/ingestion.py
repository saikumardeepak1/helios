import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ToolCallIn(BaseModel):
    tool_name: str
    arguments: dict | None = None
    result: dict | None = None


class SpanIn(BaseModel):
    local_id: str = Field(
        description="Client-assigned id, used only to link parent/child spans within this payload"
    )
    parent_local_id: str | None = None
    kind: str
    model: str | None = None
    input: dict | None = None
    output: dict | None = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    started_at: datetime
    ended_at: datetime | None = None
    tool_calls: list[ToolCallIn] = Field(default_factory=list)


class AgentIn(BaseModel):
    name: str
    version: str = "0.1.0"


class RunIn(BaseModel):
    status: str = "completed"
    started_at: datetime
    ended_at: datetime | None = None
    spans: list[SpanIn] = Field(default_factory=list)


class IngestTraceRequest(BaseModel):
    agent: AgentIn
    run: RunIn


class IngestTraceResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    span_count: int
