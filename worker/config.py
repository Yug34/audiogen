import os


def get_redis_url() -> str:
    # return os.getenv("REDIS_URL", "redis://redis:6379/0")
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_queue_names() -> list[str]:
    return [q.strip() for q in os.getenv("RQ_QUEUES", "audio,default").split(",") if q.strip()]


def get_job_timeout_seconds() -> int:
    # Audio ML can be long-running; default to one hour
    return int(os.getenv("RQ_JOB_TIMEOUT", "3600"))


