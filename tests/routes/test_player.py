from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.hooks import RealmSyncHook, add_hook, get_hooks
from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.models import Location, Player
from realm_sync_api.routes.player import PlayerRetriever, router


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_redis = MagicMock(spec=RealmSyncRedis)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.scan = AsyncMock(return_value=(0, []))
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    return mock_redis


@pytest.fixture
def app_with_redis(mock_redis):
    """Create a FastAPI app with mocked Redis."""
    set_redis_client(mock_redis)
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app_with_redis):
    """Create a test client."""
    return TestClient(app_with_redis)


def test_player_retriever_get_key():
    """Test that _get_key returns correct format."""
    retriever = PlayerRetriever()
    assert retriever._get_key("123") == "player:123"


@pytest.mark.asyncio
async def test_player_retriever_get_success(mock_redis):
    """Test getting a player successfully."""
    set_redis_client(mock_redis)

    player_data = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )
    mock_redis.get = AsyncMock(return_value=player_data.model_dump_json())

    retriever = PlayerRetriever()
    result = await retriever.get("1")

    assert result.id == "1"
    assert result.name == "Test Player"
    mock_redis.get.assert_called_once_with("player:1")


@pytest.mark.asyncio
async def test_player_retriever_get_not_found(mock_redis):
    """Test getting a non-existent player raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.get = AsyncMock(return_value=None)

    retriever = PlayerRetriever()

    with pytest.raises(ValueError, match="Player with id '1' not found"):
        await retriever.get("1")


@pytest.mark.asyncio
async def test_player_retriever_list_empty(mock_redis):
    """Test listing players when there are none."""
    set_redis_client(mock_redis)
    mock_redis.scan = AsyncMock(return_value=(0, []))

    retriever = PlayerRetriever()
    result = await retriever.list(type(retriever).__orig_bases__[0].__args__[1]())

    assert result == []


@pytest.mark.asyncio
async def test_player_retriever_list_with_players(mock_redis):
    """Test listing players."""
    set_redis_client(mock_redis)

    player1 = Player(
        id="1",
        name="Player 1",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )
    player2 = Player(
        id="2",
        name="Player 2",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    # Mock scan to return keys in two iterations
    mock_redis.scan = AsyncMock(
        side_effect=[
            (1, ["player:1"]),
            (0, ["player:2"]),
        ]
    )
    mock_redis.get = AsyncMock(
        side_effect=[
            player1.model_dump_json(),
            player2.model_dump_json(),
        ]
    )

    retriever = PlayerRetriever()
    result = await retriever.list(type(retriever).__orig_bases__[0].__args__[1]())

    assert len(result) == 2
    assert {p.id for p in result} == {"1", "2"}


@pytest.mark.asyncio
async def test_player_retriever_create_success(mock_redis):
    """Test creating a player successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    player = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()
    result = await retriever.create(player)

    assert result.id == "1"
    mock_redis.exists.assert_called_once_with("player:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_player_retriever_create_duplicate(mock_redis):
    """Test creating a duplicate player raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    player = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()

    with pytest.raises(ValueError, match="Player with id '1' already exists"):
        await retriever.create(player)


@pytest.mark.asyncio
async def test_player_retriever_create_calls_hook(mock_redis):
    """Test that creating a player calls the PLAYER_CREATED hook."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    hooks = get_hooks()
    hooks.clear()

    mock_hook = MagicMock()
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_hook)

    player = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()
    await retriever.create(player)

    mock_hook.assert_called_once_with(player)


@pytest.mark.asyncio
async def test_player_retriever_update_success(mock_redis):
    """Test updating a player successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    player = Player(
        id="1",
        name="Updated Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()
    result = await retriever.update("1", player)

    assert result.name == "Updated Player"
    mock_redis.exists.assert_called_once_with("player:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_player_retriever_update_not_found(mock_redis):
    """Test updating a non-existent player raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    player = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()

    with pytest.raises(ValueError, match="Player with id '1' not found"):
        await retriever.update("1", player)


@pytest.mark.asyncio
async def test_player_retriever_update_id_mismatch(mock_redis):
    """Test updating with mismatched id raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    player = Player(
        id="2",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()

    with pytest.raises(ValueError, match="Player id mismatch"):
        await retriever.update("1", player)


@pytest.mark.asyncio
async def test_player_retriever_update_calls_hook(mock_redis):
    """Test that updating a player calls the PLAYER_UPDATED hook."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    hooks = get_hooks()
    hooks.clear()

    mock_hook = MagicMock()
    add_hook(RealmSyncHook.PLAYER_UPDATED, mock_hook)

    player = Player(
        id="1",
        name="Updated Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )

    retriever = PlayerRetriever()
    await retriever.update("1", player)

    mock_hook.assert_called_once_with(player)


@pytest.mark.asyncio
async def test_player_retriever_delete_success(mock_redis):
    """Test deleting a player successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    player_data = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )
    mock_redis.get = AsyncMock(return_value=player_data.model_dump_json())

    retriever = PlayerRetriever()
    await retriever.delete("1")

    mock_redis.exists.assert_called_once_with("player:1")
    mock_redis.get.assert_called_once_with("player:1")
    mock_redis.delete.assert_called_once_with("player:1")


@pytest.mark.asyncio
async def test_player_retriever_delete_not_found(mock_redis):
    """Test deleting a non-existent player raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    retriever = PlayerRetriever()

    with pytest.raises(ValueError, match="Player with id '1' not found"):
        await retriever.delete("1")


@pytest.mark.asyncio
async def test_player_retriever_delete_calls_hook(mock_redis):
    """Test that deleting a player calls the PLAYER_DELETED hook."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    player_data = Player(
        id="1",
        name="Test Player",
        server="s1",
        location=Location(location="test", x=1.0, y=2.0, z=3.0),
        faction="A",
    )
    mock_redis.get = AsyncMock(return_value=player_data.model_dump_json())

    hooks = get_hooks()
    hooks.clear()

    mock_hook = MagicMock()
    add_hook(RealmSyncHook.PLAYER_DELETED, mock_hook)

    retriever = PlayerRetriever()
    await retriever.delete("1")

    mock_hook.assert_called_once()
    # Check that the hook was called with a Player object
    call_args = mock_hook.call_args[0]
    assert len(call_args) == 1
    assert isinstance(call_args[0], Player)
    assert call_args[0].id == "1"


def test_player_router_endpoints(client, mock_redis):
    """Test that player router endpoints work correctly."""
    set_redis_client(mock_redis)

    # Test POST /player/
    player_data = {
        "id": "1",
        "name": "Test Player",
        "server": "s1",
        "location": {"location": "test", "x": 1.0, "y": 2.0, "z": 3.0},
        "faction": "A",
    }
    mock_redis.exists.return_value = 0

    response = client.post("/player/", json=player_data)
    assert response.status_code == 200

    # Test GET /player/1
    mock_redis.get.return_value = Player(**player_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/player/1")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    assert response.json()["id"] == "1"

    # Test PUT /player/1
    updated_data = {**player_data, "name": "Updated Player"}
    mock_redis.exists.return_value = 1
    response = client.put("/player/1", json=updated_data)
    assert response.status_code == 200

    # Test DELETE /player/1
    mock_redis.get.return_value = Player(**player_data).model_dump_json()
    mock_redis.exists.return_value = 1
    response = client.delete("/player/1")
    assert response.status_code == 200

    # Test GET /player/ (list)
    mock_redis.scan.return_value = (0, ["player:1"])
    mock_redis.get.return_value = Player(**player_data).model_dump_json()
    response = client.get("/player/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
