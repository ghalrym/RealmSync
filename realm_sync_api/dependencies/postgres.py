from typing import Any, Protocol, runtime_checkable

import asyncpg


@runtime_checkable
class _RealmSyncPostgresProtocol(Protocol):
    """Protocol for PostgreSQL client implementations."""

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row from the database."""
        ...

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Fetch all rows from the database."""
        ...

    async def execute(self, query: str, *args: Any) -> None:
        """Execute a query without returning results."""
        ...


class RealmSyncPostgres:
    """PostgreSQL client implementation using asyncpg."""

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        **kwargs: Any,
    ) -> None:
        """
        Initialize PostgreSQL client.

        Args:
            host: Database host
            port: Database port
            user: Database user
            password: Database password
            database: Database name
            **kwargs: Additional arguments passed to asyncpg.create_pool
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.kwargs = kwargs
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                **self.kwargs,
            )

    async def close(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """
        Fetch a single row from the database.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters

        Returns:
            Dictionary with row data or None if no row found
        """
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        row = await self._pool.fetchrow(query, *args)
        if row is None:
            return None
        return dict(row)

    async def fetch_all(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """
        Fetch all rows from the database.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters

        Returns:
            List of dictionaries with row data
        """
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        rows = await self._pool.fetch(query, *args)
        return [dict(row) for row in rows]

    async def execute(self, query: str, *args: Any) -> None:
        """
        Execute a query without returning results.

        Args:
            query: SQL query with $1, $2, etc. placeholders
            *args: Query parameters
        """
        if self._pool is None:
            await self.connect()

        assert self._pool is not None
        await self._pool.execute(query, *args)


POSTGRES_CLIENT: _RealmSyncPostgresProtocol | None = None


def set_postgres_client(postgres_client: _RealmSyncPostgresProtocol) -> None:
    global POSTGRES_CLIENT
    POSTGRES_CLIENT = postgres_client


def get_postgres_client() -> _RealmSyncPostgresProtocol:
    global POSTGRES_CLIENT
    if POSTGRES_CLIENT is None:
        raise ValueError("Postgres client not found")
    return POSTGRES_CLIENT
