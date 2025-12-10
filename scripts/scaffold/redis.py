"""Custom Redis client class extending RealmSyncRedis."""

import os

from realm_sync_api import RealmSyncRedis


class Redis(RealmSyncRedis):
    """Custom Redis client with configuration from environment variables."""

    def __init__(self, **kwargs):
        """
        Initialize Redis client.

        Args:
            **kwargs: Additional arguments passed to RealmSyncRedis
        """
        super().__init__(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            **kwargs,
        )
