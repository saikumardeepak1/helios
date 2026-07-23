import json
import logging

from app.core.logging import JsonFormatter, configure_logging, correlation_id_var

configure_logging()  # installs the correlation-id record factory for this process


def _make_record(message: str = "hello", level: int = logging.INFO) -> logging.LogRecord:
    return logging.getLogger("app.test").makeRecord(
        "app.test", level, __file__, 1, message, (), None
    )


def test_json_formatter_produces_valid_json_with_expected_fields() -> None:
    record = _make_record("something happened")
    formatted = JsonFormatter().format(record)

    payload = json.loads(formatted)
    assert payload["message"] == "something happened"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert "timestamp" in payload


def test_json_formatter_omits_correlation_id_when_not_set() -> None:
    payload = json.loads(JsonFormatter().format(_make_record()))
    assert "correlation_id" not in payload


def test_record_factory_stamps_the_current_correlation_id() -> None:
    token = correlation_id_var.set("ctx-xyz")
    try:
        record = _make_record()
        assert record.correlation_id == "ctx-xyz"  # type: ignore[attr-defined]
        payload = json.loads(JsonFormatter().format(record))
        assert payload["correlation_id"] == "ctx-xyz"
    finally:
        correlation_id_var.reset(token)


def test_record_factory_stamps_none_outside_any_context() -> None:
    record = _make_record()
    assert record.correlation_id is None  # type: ignore[attr-defined]
