from typing import Any

from redis.asyncio import Redis


class RealmSyncRedis(Redis):
    def __init__(self, host: str, port: int, db: int, **kwargs: Any) -> None:
        super().__init__(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            **kwargs,
        )


REDIS_CLIENT: RealmSyncRedis | None = None


def set_redis_client(redis_client: RealmSyncRedis) -> None:
    global REDIS_CLIENT
    REDIS_CLIENT = redis_client


def get_redis_client() -> RealmSyncRedis:
    global REDIS_CLIENT
    if REDIS_CLIENT is None:
        raise ValueError("Redis client not found")
    return REDIS_CLIENT
