"""Custom PostgreSQL client class extending RealmSyncDatabase."""

import os

from realm_sync_api import RealmSyncDatabase


class Postgres(RealmSyncDatabase):
    """Custom PostgreSQL client with configuration from environment variables."""

    def __init__(self, **kwargs):
        """
        Initialize PostgreSQL client.

        Args:
            **kwargs: Additional arguments passed to RealmSyncDatabase
        """
        super().__init__(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "realm_sync"),
            password=os.getenv("POSTGRES_PASSWORD", "realm_sync_password"),
            database=os.getenv("POSTGRES_DB", "realm_sync_db"),
            **kwargs,
        )
