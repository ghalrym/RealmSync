from typing import Any

import pytest

from realm_sync_api.dependencies import database
from realm_sync_api.dependencies.database import (
    POSTGRES_CLIENT,
    RealmSyncDatabase,
    get_postgres_client,
    set_postgres_client,
)


class MockRealmSyncDatabase:
    """Concrete implementation of RealmSyncPostgres for testing."""

    async def fetch_one(self, query: str, *args: Any) -> dict[str, Any] | None:
        """Fetch a single row from the database."""
        return None

    async def execute(self, query: str, *args: Any) -> None:
        """Execute a query without returning results."""
        pass


def test_realm_sync_postgres_is_protocol():
    """Test that RealmSyncDatabase is a Protocol."""
    # Protocols are types in Python
    assert isinstance(RealmSyncDatabase, type)


def test_set_and_get_postgres_client():
    """Test setting and getting postgres client."""
    postgres_client = MockRealmSyncDatabase()
    set_postgres_client(postgres_client)

    retrieved_client = get_postgres_client()
    assert retrieved_client is postgres_client


def test_get_postgres_client_raises_when_not_set():
    """Test that get_postgres_client raises ValueError when client is not set."""
    # Clear the client
    set_postgres_client(None)  # type: ignore

    with pytest.raises(ValueError, match="Postgres client not found"):
        get_postgres_client()


def test_postgres_module_imports():
    """Test that database module can be imported and has expected attributes."""
    assert hasattr(database, "RealmSyncDatabase")
    assert hasattr(database, "POSTGRES_CLIENT")
    assert hasattr(database, "set_postgres_client")
    assert hasattr(database, "get_postgres_client")


def test_postgres_client_initial_state():
    """Test that POSTGRES_CLIENT starts as None."""
    # Reset to None
    set_postgres_client(None)  # type: ignore
    # The module-level variable should exist
    assert POSTGRES_CLIENT is None
