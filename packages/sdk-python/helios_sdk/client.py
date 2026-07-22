import httpx

from helios_sdk.tracing import RunContext


class HeliosApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        super().__init__(f"Helios API returned {status_code}: {detail}")


class HeliosClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.api_key = api_key
        self._http = httpx.Client(
            base_url=base_url.rstrip("/"), timeout=timeout, transport=transport
        )

    def trace_run(self, agent_name: str, agent_version: str = "0.1.0") -> RunContext:
        return RunContext(self, agent_name, agent_version)

    def close(self) -> None:
        self._http.close()

    def _send(self, payload: dict) -> dict:
        try:
            response = self._http.post(
                "/v1/ingest/traces",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
        except httpx.HTTPError as exc:
            raise HeliosApiError(0, str(exc)) from exc

        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except ValueError:
                pass
            raise HeliosApiError(response.status_code, detail)

        result: dict = response.json()
        return result
