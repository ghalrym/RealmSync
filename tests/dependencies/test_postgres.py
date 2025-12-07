import pytest

from realm_sync_api.dependencies.postgres import (
    RealmSyncPostgres,
    get_postgres_client,
    set_postgres_client,
)


def test_realm_sync_postgres_is_class():
    """Test that RealmSyncPostgres is a class."""
    assert isinstance(RealmSyncPostgres, type)


def test_set_and_get_postgres_client():
    """Test setting and getting postgres client."""
    postgres_client = RealmSyncPostgres()
    set_postgres_client(postgres_client)

    retrieved_client = get_postgres_client()
    assert retrieved_client is postgres_client


def test_get_postgres_client_raises_when_not_set():
    """Test that get_postgres_client raises ValueError when client is not set."""
    # Clear the client
    set_postgres_client(None)  # type: ignore

    with pytest.raises(ValueError, match="Postgres client not found"):
        get_postgres_client()
