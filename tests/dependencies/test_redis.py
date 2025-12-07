import pytest

from realm_sync_api.dependencies.redis import (
    RealmSyncRedis,
    get_redis_client,
    set_redis_client,
)


def test_realm_sync_redis_initialization():
    """Test that RealmSyncRedis initializes with correct parameters."""
    redis_client = RealmSyncRedis(host="localhost", port=6379, db=0)
    assert redis_client.connection_pool.connection_kwargs["host"] == "localhost"
    assert redis_client.connection_pool.connection_kwargs["port"] == 6379
    assert redis_client.connection_pool.connection_kwargs["db"] == 0
    assert redis_client.connection_pool.connection_kwargs["decode_responses"] is True


def test_set_and_get_redis_client():
    """Test setting and getting redis client."""
    redis_client = RealmSyncRedis(host="localhost", port=6379, db=0)
    set_redis_client(redis_client)

    retrieved_client = get_redis_client()
    assert retrieved_client is redis_client


def test_get_redis_client_raises_when_not_set():
    """Test that get_redis_client raises ValueError when client is not set."""
    # Clear the client
    set_redis_client(None)  # type: ignore

    with pytest.raises(ValueError, match="Redis client not found"):
        get_redis_client()


def test_realm_sync_redis_with_kwargs():
    """Test that RealmSyncRedis accepts additional kwargs."""
    redis_client = RealmSyncRedis(host="localhost", port=6379, db=0, socket_timeout=5.0)
    assert redis_client.connection_pool.connection_kwargs["socket_timeout"] == 5.0
