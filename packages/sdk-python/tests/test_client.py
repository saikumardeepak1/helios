import httpx

from helios_sdk import HeliosClient


def test_send_posts_to_ingest_traces_with_bearer_auth() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(202, json={"run_id": "abc", "status": "completed", "span_count": 0})

    client = HeliosClient(
        api_key="hel_live_test",
        base_url="http://localhost:8000/",
        transport=httpx.MockTransport(handler),
    )

    client._send({"agent": {"name": "a"}, "run": {"status": "completed", "spans": []}})

    assert captured["url"] == "http://localhost:8000/v1/ingest/traces"
    assert captured["auth"] == "Bearer hel_live_test"

    client.close()
