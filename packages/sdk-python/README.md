# helios-sdk

Python client for instrumenting AI agents with Helios tracing.

## Install

```bash
pip install -e packages/sdk-python
```

## Usage

```python
from helios_sdk import HeliosClient

client = HeliosClient(api_key="hel_live_...", base_url="https://helios.example.com")

with client.trace_run(agent_name="support-bot", agent_version="1.0.0") as run:
    with run.span(kind="llm_call", input={"prompt": "Where is order 123?"}) as span:
        span.record_tokens(prompt_tokens=42, completion_tokens=18)
        span.set_output({"text": "Order 123 shipped yesterday."})

        with span.tool_call("lookup_order", arguments={"order_id": "123"}) as tc:
            tc.set_result({"status": "shipped"})
```

The trace (agent, run, spans, and tool calls) is sent to Helios when the outer `with client.trace_run(...)` block exits. If the block raises, the run is still sent, recorded with `status="failed"`, and the exception propagates as normal.

Spans opened while another span's `with` block is still open are recorded as children of it automatically — nesting `run.span(...)` blocks builds the parent/child hierarchy for you.
