import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ToolCallIn(BaseModel):
    """A tool/function call made during a span, if any."""

    tool_name: str = Field(description="Name of the tool that was called.")
    arguments: dict | None = Field(
        default=None, description="Arguments passed to the tool, as a JSON object."
    )
    result: dict | None = Field(
        default=None, description="Value the tool returned, as a JSON object."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tool_name": "lookup_order",
                    "arguments": {"order_id": "123"},
                    "result": {"status": "shipped"},
                }
            ]
        }
    )


class SpanIn(BaseModel):
    """A single step (an LLM call, a tool call, etc.) within an agent run."""

    local_id: str = Field(
        description="Client-assigned id, used only to link parent/child spans within this payload"
    )
    parent_local_id: str | None = Field(
        default=None,
        description=(
            "local_id of this span's parent, if any. Omit or set null for a top-level span."
        ),
    )
    kind: str = Field(description="Type of step, e.g. 'llm_call' or 'tool_call'.")
    model: str | None = Field(
        default=None,
        description="Model used for this span, if it was an LLM call (e.g. 'gpt-4o-mini'). "
        "Required for the span to be included in cost analytics.",
    )
    input: dict | None = Field(default=None, description="Input to this step, as a JSON object.")
    output: dict | None = Field(
        default=None, description="Output from this step, as a JSON object."
    )
    prompt_tokens: int = Field(default=0, ge=0, description="Prompt tokens consumed, if any.")
    completion_tokens: int = Field(
        default=0, ge=0, description="Completion tokens generated, if any."
    )
    started_at: datetime = Field(description="When this step started.")
    ended_at: datetime | None = Field(default=None, description="When this step finished.")
    tool_calls: list[ToolCallIn] = Field(
        default_factory=list, description="Tool calls made during this span, if any."
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "local_id": "root",
                    "parent_local_id": None,
                    "kind": "llm_call",
                    "model": "gpt-4o-mini",
                    "input": {"prompt": "Where is my order?"},
                    "output": {"text": "Your order shipped yesterday."},
                    "prompt_tokens": 42,
                    "completion_tokens": 18,
                    "started_at": "2026-01-01T00:00:00Z",
                    "ended_at": "2026-01-01T00:00:01Z",
                    "tool_calls": [],
                }
            ]
        }
    )


class AgentIn(BaseModel):
    """Identifies the agent that produced this run. Looked up or created by
    (organization, name) — the version is updated in place on every ingest.
    """

    name: str = Field(description="Stable identifier for this agent, e.g. 'support-bot'.")
    version: str = Field(
        default="0.1.0", description="Version of the agent that produced this run."
    )

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"name": "support-bot", "version": "1.0.0"}]}
    )


class RunIn(BaseModel):
    """One end-to-end agent execution, made up of one or more spans."""

    status: str = Field(
        default="completed", description="Outcome of the run, e.g. 'completed' or 'failed'."
    )
    started_at: datetime = Field(description="When the run started.")
    ended_at: datetime | None = Field(default=None, description="When the run finished.")
    spans: list[SpanIn] = Field(
        default_factory=list, description="Steps taken during this run, in any order."
    )


class IngestTraceRequest(BaseModel):
    """Body for POST /v1/ingest/traces — sent by helios-sdk, not usually built by hand."""

    agent: AgentIn
    run: RunIn

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "agent": {"name": "support-bot", "version": "1.0.0"},
                    "run": {
                        "status": "completed",
                        "started_at": "2026-01-01T00:00:00Z",
                        "ended_at": "2026-01-01T00:00:01Z",
                        "spans": [
                            {
                                "local_id": "root",
                                "parent_local_id": None,
                                "kind": "llm_call",
                                "model": "gpt-4o-mini",
                                "input": {"prompt": "Where is my order?"},
                                "output": {"text": "Your order shipped yesterday."},
                                "prompt_tokens": 42,
                                "completion_tokens": 18,
                                "started_at": "2026-01-01T00:00:00Z",
                                "ended_at": "2026-01-01T00:00:01Z",
                                "tool_calls": [
                                    {
                                        "tool_name": "lookup_order",
                                        "arguments": {"order_id": "123"},
                                        "result": {"status": "shipped"},
                                    }
                                ],
                            }
                        ],
                    },
                }
            ]
        }
    )


class IngestTraceResponse(BaseModel):
    run_id: uuid.UUID = Field(description="Id assigned to the newly stored run.")
    status: str = Field(description="Echoes the run's reported status.")
    span_count: int = Field(description="Number of spans stored for this run.")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "run_id": "6c1e4f2b-2435-43fc-882b-e0a9beb8165c",
                    "status": "completed",
                    "span_count": 1,
                }
            ]
        }
    )
