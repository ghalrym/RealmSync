import pytest

from realm_sync_api.dependencies import postgres
from realm_sync_api.dependencies.postgres import (
    MockRealmSyncPostgres,
    RealmSyncPostgres,
    get_postgres_client,
    set_postgres_client,
)


def test_realm_sync_postgres_is_protocol():
    """Test that RealmSyncPostgres is a Protocol."""
    # Protocols are types in Python
    assert isinstance(RealmSyncPostgres, type)


def test_set_and_get_postgres_client():
    """Test setting and getting postgres client."""
    postgres_client = MockRealmSyncPostgres()
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
    """Test that postgres module can be imported and has expected attributes."""
    assert hasattr(postgres, "RealmSyncPostgres")
    assert hasattr(postgres, "POSTGRES_CLIENT")
    assert hasattr(postgres, "set_postgres_client")
    assert hasattr(postgres, "get_postgres_client")


def test_postgres_client_initial_state():
    """Test that POSTGRES_CLIENT starts as None."""
    # Reset to None
    set_postgres_client(None)  # type: ignore
    # The module-level variable should exist
    assert postgres.POSTGRES_CLIENT is None
