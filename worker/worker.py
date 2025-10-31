import os

from redis import Redis
from rq import Worker

from worker.queues import get_queues


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    # Ensure a connection is established for Worker via the first queue
    queues = get_queues(Redis.from_url(redis_url))
    Worker(queues).work(with_scheduler=True)


if __name__ == "__main__":
    main()


