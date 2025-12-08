from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.models import NPC
from realm_sync_api.routes.npc import ListRequestArgs, NPCRetriever, router


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


def test_npc_retriever_get_key(mock_redis):
    """Test that _get_key returns correct format."""
    set_redis_client(mock_redis)
    retriever = NPCRetriever()
    assert retriever._get_key("123") == "npc:123"


@pytest.mark.asyncio
async def test_npc_retriever_get_success(mock_redis):
    """Test getting an NPC successfully."""
    set_redis_client(mock_redis)

    npc_data = NPC(id="1", name="Test NPC", faction="A", quests=[])
    mock_redis.get = AsyncMock(return_value=npc_data.model_dump_json())

    retriever = NPCRetriever()
    result = await retriever.get("1")

    assert result.id == "1"
    assert result.name == "Test NPC"
    mock_redis.get.assert_called_once_with("npc:1")


@pytest.mark.asyncio
async def test_npc_retriever_get_not_found(mock_redis):
    """Test getting a non-existent NPC raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.get = AsyncMock(return_value=None)

    retriever = NPCRetriever()

    with pytest.raises(ValueError, match="NPC with id '1' not found"):
        await retriever.get("1")


@pytest.mark.asyncio
async def test_npc_retriever_list_empty(mock_redis):
    """Test listing NPCs when there are none."""
    set_redis_client(mock_redis)
    mock_redis.scan = AsyncMock(return_value=(0, []))

    retriever = NPCRetriever()
    result = await retriever.list(ListRequestArgs())

    assert result == []


@pytest.mark.asyncio
async def test_npc_retriever_list_with_npcs(mock_redis):
    """Test listing NPCs."""
    set_redis_client(mock_redis)

    npc1 = NPC(id="1", name="NPC 1", faction="A", quests=[])
    npc2 = NPC(id="2", name="NPC 2", faction="B", quests=[])

    # Mock scan to return keys in batches
    mock_redis.scan = AsyncMock(side_effect=[(1, ["npc:1"]), (0, ["npc:2"])])
    mock_redis.get = AsyncMock(side_effect=[npc1.model_dump_json(), npc2.model_dump_json()])

    retriever = NPCRetriever()
    result = await retriever.list(ListRequestArgs())

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"


@pytest.mark.asyncio
async def test_npc_retriever_create_success(mock_redis):
    """Test creating an NPC successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    npc = NPC(id="1", name="Test NPC", faction="A", quests=[])

    retriever = NPCRetriever()
    result = await retriever.create(npc)

    assert result.id == "1"
    mock_redis.exists.assert_called_once_with("npc:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_npc_retriever_create_duplicate(mock_redis):
    """Test creating a duplicate NPC raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    npc = NPC(id="1", name="Test NPC", faction="A", quests=[])

    retriever = NPCRetriever()

    with pytest.raises(ValueError, match="NPC with id '1' already exists"):
        await retriever.create(npc)


@pytest.mark.asyncio
async def test_npc_retriever_update_success(mock_redis):
    """Test updating an NPC successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    npc = NPC(id="1", name="Updated NPC", faction="B", quests=[])

    retriever = NPCRetriever()
    result = await retriever.update("1", npc)

    assert result.name == "Updated NPC"
    mock_redis.exists.assert_called_once_with("npc:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_npc_retriever_update_not_found(mock_redis):
    """Test updating a non-existent NPC raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    npc = NPC(id="1", name="Test NPC", faction="A", quests=[])

    retriever = NPCRetriever()

    with pytest.raises(ValueError, match="NPC with id '1' not found"):
        await retriever.update("1", npc)


@pytest.mark.asyncio
async def test_npc_retriever_update_id_mismatch(mock_redis):
    """Test updating with mismatched id raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    npc = NPC(id="2", name="Test NPC", faction="A", quests=[])

    retriever = NPCRetriever()

    with pytest.raises(ValueError, match="NPC id mismatch"):
        await retriever.update("1", npc)


@pytest.mark.asyncio
async def test_npc_retriever_delete_success(mock_redis):
    """Test deleting an NPC successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    retriever = NPCRetriever()
    await retriever.delete("1")

    mock_redis.exists.assert_called_once_with("npc:1")
    mock_redis.delete.assert_called_once_with("npc:1")


@pytest.mark.asyncio
async def test_npc_retriever_delete_not_found(mock_redis):
    """Test deleting a non-existent NPC raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    retriever = NPCRetriever()

    with pytest.raises(ValueError, match="NPC with id '1' not found"):
        await retriever.delete("1")


def test_npc_router_endpoints(client, mock_redis):
    """Test that NPC router endpoints work correctly."""
    set_redis_client(mock_redis)

    # Test POST /npc/
    npc_data = {"id": "1", "name": "Test NPC", "faction": "A", "quests": []}
    mock_redis.exists.return_value = 0

    response = client.post("/npc/", json=npc_data)
    assert response.status_code == 200

    # Test GET /npc/1
    mock_redis.get.return_value = NPC(**npc_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/npc/1")
    assert response.status_code == 200
    assert response.json()["id"] == "1"

    # Test PUT /npc/1
    updated_data = {**npc_data, "name": "Updated NPC"}
    mock_redis.exists.return_value = 1
    response = client.put("/npc/1", json=updated_data)
    assert response.status_code == 200

    # Test DELETE /npc/1
    mock_redis.get.return_value = NPC(**npc_data).model_dump_json()
    mock_redis.exists.return_value = 1
    response = client.delete("/npc/1")
    assert response.status_code == 200

    # Test GET /npc/ (list)
    mock_redis.scan.return_value = (0, ["npc:1"])
    mock_redis.get.return_value = NPC(**npc_data).model_dump_json()
    response = client.get("/npc/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
