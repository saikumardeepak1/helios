"""RQ worker entrypoint: `python -m app.workers.worker`.

Configures structured JSON logging the same way the API process does
(app.main) before starting the worker loop — without this, jobs run with
Python's unconfigured default logging and never get correlation ids or
JSON formatting.
"""

from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    configure_logging()

    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([Queue("default", connection=connection)], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
