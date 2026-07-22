from functools import lru_cache

import redis
from rq import Queue

from app.core.config import get_settings


@lru_cache
def get_queue() -> Queue:
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    return Queue("default", connection=connection)
