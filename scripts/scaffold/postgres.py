"""Custom PostgreSQL client class extending RealmSyncPostgres."""

import os

from realm_sync_api import RealmSyncPostgres


class Postgres(RealmSyncPostgres):
    """Custom PostgreSQL client with configuration from environment variables."""

    def __init__(self, **kwargs):
        """
        Initialize PostgreSQL client.

        Args:
            **kwargs: Additional arguments passed to RealmSyncPostgres
        """
        super().__init__(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "realm_sync"),
            password=os.getenv("POSTGRES_PASSWORD", "realm_sync_password"),
            database=os.getenv("POSTGRES_DB", "realm_sync_db"),
            **kwargs,
        )

