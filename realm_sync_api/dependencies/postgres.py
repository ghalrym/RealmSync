from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RealmSyncPostgres(Protocol):
    """Protocol for PostgreSQL client implementations."""

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row from the database."""
        ...

    async def execute(self, query: str, *args: Any) -> None:
        """Execute a query without returning results."""
        ...


class MockRealmSyncPostgres:
    """Concrete implementation of RealmSyncPostgres for testing."""

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row from the database."""
        return None

    async def execute(self, query: str, *args: Any) -> None:
        """Execute a query without returning results."""
        pass


POSTGRES_CLIENT: RealmSyncPostgres | None = None


def set_postgres_client(postgres_client: RealmSyncPostgres) -> None:
    global POSTGRES_CLIENT
    POSTGRES_CLIENT = postgres_client


def get_postgres_client() -> RealmSyncPostgres:
    global POSTGRES_CLIENT
    if POSTGRES_CLIENT is None:
        raise ValueError("Postgres client not found")
    return POSTGRES_CLIENT
