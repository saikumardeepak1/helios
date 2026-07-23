import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Set for the duration of one API request (by CorrelationIdMiddleware) or one
# worker job (by app.workers.tasks), so every log line emitted while handling
# that request/job carries the same id without threading it through every
# function call.
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_base_record_factory = logging.getLogRecordFactory()


def _correlation_id_record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
    """Stamps every record with the current correlation id at creation time.

    Filters attached to a specific handler (or even a logger) only run for
    log calls that actually reach that handler through the normal
    propagation path — a handler attached directly to a submodule logger
    (as pytest's caplog does) never sees them. Replacing the record factory
    instead guarantees every LogRecord, from any logger, carries the field
    before any filter or handler even runs.
    """
    record = _base_record_factory(*args, **kwargs)
    record.correlation_id = correlation_id_var.get()  # type: ignore[attr-defined]
    return record


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        correlation_id = getattr(record, "correlation_id", None)
        if correlation_id:
            payload["correlation_id"] = correlation_id
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


UVICORN_LOGGER_NAMES = ("uvicorn", "uvicorn.access", "uvicorn.error")


def configure_logging(level: str = "INFO") -> None:
    logging.setLogRecordFactory(_correlation_id_record_factory)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Uvicorn configures its own loggers with their own handlers and
    # propagate=False by default, so its access/error logs would otherwise
    # bypass our JSON formatter (and never carry a correlation id) entirely.
    # Clearing their handlers and re-enabling propagation routes them
    # through root's handler like every other log line in the process.
    for uvicorn_logger_name in UVICORN_LOGGER_NAMES:
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
