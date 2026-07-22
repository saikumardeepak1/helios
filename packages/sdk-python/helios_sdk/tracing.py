from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import TracebackType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from helios_sdk.client import HeliosClient


def _new_local_id() -> str:
    return uuid.uuid4().hex[:12]


class ToolCallContext:
    def __init__(self, span: SpanContext, tool_name: str, arguments: dict | None = None) -> None:
        self.tool_name = tool_name
        self.arguments = arguments
        self.result: dict | None = None
        self._span = span

    def set_result(self, result: dict) -> None:
        self.result = result

    def __enter__(self) -> ToolCallContext:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._span._tool_calls.append(
            {"tool_name": self.tool_name, "arguments": self.arguments, "result": self.result}
        )


class SpanContext:
    def __init__(
        self,
        run: RunContext,
        local_id: str,
        parent_local_id: str | None,
        kind: str,
        model: str | None = None,
        input: dict | None = None,
    ) -> None:
        self.local_id = local_id
        self.parent_local_id = parent_local_id
        self.kind = kind
        self.model = model
        self.input = input
        self.output: dict | None = None
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.started_at: datetime | None = None
        self.ended_at: datetime | None = None
        self._run = run
        self._tool_calls: list[dict[str, Any]] = []

    def set_output(self, output: dict) -> None:
        self.output = output

    def record_tokens(self, prompt_tokens: int = 0, completion_tokens: int = 0) -> None:
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens

    def tool_call(self, tool_name: str, arguments: dict | None = None) -> ToolCallContext:
        return ToolCallContext(self, tool_name, arguments)

    def __enter__(self) -> SpanContext:
        self.started_at = datetime.now(timezone.utc)
        self._run._span_stack.append(self.local_id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.ended_at = datetime.now(timezone.utc)
        self._run._span_stack.pop()
        self._run._spans.append(self._to_dict())

    def _to_dict(self) -> dict[str, Any]:
        return {
            "local_id": self.local_id,
            "parent_local_id": self.parent_local_id,
            "kind": self.kind,
            "model": self.model,
            "input": self.input,
            "output": self.output,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "tool_calls": self._tool_calls,
        }


class RunContext:
    def __init__(self, client: HeliosClient, agent_name: str, agent_version: str) -> None:
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.status = "completed"
        self.started_at: datetime | None = None
        self.ended_at: datetime | None = None
        self.result: dict | None = None
        self._client = client
        self._span_stack: list[str] = []
        self._spans: list[dict[str, Any]] = []

    def span(
        self, kind: str, model: str | None = None, input: dict | None = None
    ) -> SpanContext:
        parent_local_id = self._span_stack[-1] if self._span_stack else None
        return SpanContext(self, _new_local_id(), parent_local_id, kind, model, input)

    def __enter__(self) -> RunContext:
        self.started_at = datetime.now(timezone.utc)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.ended_at = datetime.now(timezone.utc)
        if exc_type is not None:
            self.status = "failed"

        payload = {
            "agent": {"name": self.agent_name, "version": self.agent_version},
            "run": {
                "status": self.status,
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "ended_at": self.ended_at.isoformat() if self.ended_at else None,
                "spans": self._spans,
            },
        }
        self.result = self._client._send(payload)
