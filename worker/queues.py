from typing import List, Optional

from redis import Redis
from rq import Queue

from worker.config import get_redis_url, get_queue_names


def get_redis_connection() -> Redis:
    return Redis.from_url(get_redis_url())


def get_queues(connection: Optional[Redis] = None) -> List[Queue]:
    conn = connection or get_redis_connection()
    return [Queue(name, connection=conn) for name in get_queue_names()]


