"""Tests for RealmSyncApi class."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from realm_sync_api.dependencies.hooks import RealmSyncHook, get_hooks
from realm_sync_api.dependencies.postgres import RealmSyncPostgres
from realm_sync_api.dependencies.redis import RealmSyncRedis
from realm_sync_api.models import Location, Player
from realm_sync_api.realm_sync_api import RealmSyncApi


def test_realm_sync_api_init_without_web_manager():
    """Test RealmSyncApi initialization without web manager."""
    app = RealmSyncApi()
    assert app.title == "RealmSync API"
    # Check that docs_url is None (line 26)
    assert app.docs_url is None


def test_realm_sync_api_init_with_web_manager():
    """Test RealmSyncApi initialization with web manager prefix."""
    app = RealmSyncApi(web_manager_perfix="/admin")
    assert app.title == "RealmSync API"
    # Check that docs_url is None (line 26)
    assert app.docs_url is None


def test_realm_sync_api_init_with_custom_title():
    """Test RealmSyncApi initialization with custom title."""
    app = RealmSyncApi(title="Custom API")
    assert app.title == "Custom API"


@patch("realm_sync_api.realm_sync_api.fsd")
def test_add_dark_mode_to_swagger(mock_fsd):
    """Test that _add_dark_mode_to_swagger installs dark mode Swagger UI."""
    # Create app - this will call _add_dark_mode_to_swagger once during init
    app = RealmSyncApi()
    # Verify it was called during init
    assert mock_fsd.install.call_count >= 1
    # Call it again to test the method directly
    app._add_dark_mode_to_swagger()
    # Now it should have been called at least twice (once in init, once directly)
    assert mock_fsd.install.call_count >= 2


def test_realm_sync_api_hook_decorator():
    """Test that hook decorator registers a function."""
    app = RealmSyncApi()
    hooks_before = len(get_hooks()[RealmSyncHook.PLAYER_CREATED])

    @app.hook(RealmSyncHook.PLAYER_CREATED)
    def test_hook(player: Player):
        pass

    hooks_after = len(get_hooks()[RealmSyncHook.PLAYER_CREATED])
    assert hooks_after == hooks_before + 1


def test_realm_sync_api_set_redis_client():
    """Test setting Redis client."""
    app = RealmSyncApi()
    redis_client = MagicMock(spec=RealmSyncRedis)
    app.set_redis_client(redis_client)
    # The method should not raise an exception
    assert True


def test_realm_sync_api_set_postgres_client():
    """Test setting PostgreSQL client."""
    app = RealmSyncApi()
    postgres_client = MagicMock(spec=RealmSyncPostgres)
    app.set_postgres_client(postgres_client)
    # The method should not raise an exception
    assert True


def test_realm_sync_api_call_hooks():
    """Test calling hooks."""
    app = RealmSyncApi()
    hook_called = False

    @app.hook(RealmSyncHook.PLAYER_CREATED)
    def test_hook(player: Player):
        nonlocal hook_called
        hook_called = True

    player = Player(
        id="1",
        name="Test",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )
    app.call_hooks(RealmSyncHook.PLAYER_CREATED, player)
    assert hook_called


def test_realm_sync_api_get_method():
    """Test that get method works as decorator."""
    app = RealmSyncApi()

    @app.get("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_realm_sync_api_post_method():
    """Test that post method works as decorator."""
    app = RealmSyncApi()

    @app.post("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.post("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_realm_sync_api_put_method():
    """Test that put method works as decorator."""
    app = RealmSyncApi()

    @app.put("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.put("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}


def test_realm_sync_api_delete_method():
    """Test that delete method works as decorator."""
    app = RealmSyncApi()

    @app.delete("/test")
    def test_endpoint():
        return {"message": "test"}

    client = TestClient(app)
    response = client.delete("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "test"}
