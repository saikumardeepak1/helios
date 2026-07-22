import json

import httpx
import pytest

from helios_sdk import HeliosApiError, HeliosClient


def _client(handler) -> HeliosClient:
    return HeliosClient(api_key="hel_live_test", transport=httpx.MockTransport(handler))


def test_trace_run_sends_a_single_span_with_tokens_and_output() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        return httpx.Response(202, json={"run_id": "abc", "status": "completed", "span_count": 1})

    client = _client(handler)
    with client.trace_run(agent_name="support-bot", agent_version="1.0.0") as run:
        with run.span(kind="llm_call", input={"prompt": "hi"}) as span:
            span.record_tokens(prompt_tokens=10, completion_tokens=5)
            span.set_output({"text": "hello"})

    payload = captured["json"]
    assert payload["agent"] == {"name": "support-bot", "version": "1.0.0"}
    assert payload["run"]["status"] == "completed"
    assert len(payload["run"]["spans"]) == 1

    sent_span = payload["run"]["spans"][0]
    assert sent_span["kind"] == "llm_call"
    assert sent_span["parent_local_id"] is None
    assert sent_span["prompt_tokens"] == 10
    assert sent_span["output"] == {"text": "hello"}
    assert run.result == {"run_id": "abc", "status": "completed", "span_count": 1}


def test_nested_spans_and_tool_calls_link_correctly() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        return httpx.Response(202, json={"run_id": "abc", "status": "completed", "span_count": 2})

    client = _client(handler)
    with client.trace_run(agent_name="support-bot") as run:
        with run.span(kind="llm_call") as parent:
            with parent.tool_call("lookup_order", arguments={"id": "1"}) as tc:
                tc.set_result({"status": "shipped"})
        with run.span(kind="tool_call"):
            pass

    spans = captured["json"]["run"]["spans"]
    parent_span = next(s for s in spans if s["kind"] == "llm_call")
    child_span = next(s for s in spans if s["kind"] == "tool_call")

    assert parent_span["tool_calls"] == [
        {"tool_name": "lookup_order", "arguments": {"id": "1"}, "result": {"status": "shipped"}}
    ]
    assert child_span["parent_local_id"] is None


def test_run_status_is_failed_when_the_block_raises() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["json"] = json.loads(request.content)
        return httpx.Response(202, json={"run_id": "abc", "status": "failed", "span_count": 0})

    client = _client(handler)
    with pytest.raises(ValueError):
        with client.trace_run(agent_name="support-bot"):
            raise ValueError("boom")

    assert captured["json"]["run"]["status"] == "failed"


def test_send_raises_helios_api_error_on_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Invalid or revoked API key"})

    client = _client(handler)
    with pytest.raises(HeliosApiError) as exc_info:
        with client.trace_run(agent_name="support-bot"):
            pass

    assert exc_info.value.status_code == 401
    assert "Invalid or revoked API key" in str(exc_info.value)
