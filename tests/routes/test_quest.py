from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.models import Quest
from realm_sync_api.routes.quest import ListRequestArgs, QuestRetriever, router


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


def test_quest_retriever_get_key(mock_redis):
    """Test that _get_key returns correct format."""
    set_redis_client(mock_redis)
    retriever = QuestRetriever()
    assert retriever._get_key("123") == "quest:123"


@pytest.mark.asyncio
async def test_quest_retriever_get_success(mock_redis):
    """Test getting a quest successfully."""
    set_redis_client(mock_redis)

    quest_data = Quest(id="1", name="Test Quest", description="Test", dependencies=[])
    mock_redis.get = AsyncMock(return_value=quest_data.model_dump_json())

    retriever = QuestRetriever()
    result = await retriever.get("1")

    assert result.id == "1"
    assert result.name == "Test Quest"
    mock_redis.get.assert_called_once_with("quest:1")


@pytest.mark.asyncio
async def test_quest_retriever_get_not_found(mock_redis):
    """Test getting a non-existent quest raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.get = AsyncMock(return_value=None)

    retriever = QuestRetriever()

    with pytest.raises(ValueError, match="Quest with id '1' not found"):
        await retriever.get("1")


@pytest.mark.asyncio
async def test_quest_retriever_list_empty(mock_redis):
    """Test listing quests when there are none."""
    set_redis_client(mock_redis)
    mock_redis.scan = AsyncMock(return_value=(0, []))

    retriever = QuestRetriever()
    result = await retriever.list(ListRequestArgs())

    assert result == []


@pytest.mark.asyncio
async def test_quest_retriever_list_with_quests(mock_redis):
    """Test listing quests."""
    set_redis_client(mock_redis)

    quest1 = Quest(id="1", name="Quest 1", description="Desc 1", dependencies=[])
    quest2 = Quest(id="2", name="Quest 2", description="Desc 2", dependencies=[])

    # Mock scan to return keys in batches
    mock_redis.scan = AsyncMock(side_effect=[(1, ["quest:1"]), (0, ["quest:2"])])
    mock_redis.get = AsyncMock(
        side_effect=[quest1.model_dump_json(), quest2.model_dump_json()]
    )

    retriever = QuestRetriever()
    result = await retriever.list(ListRequestArgs())

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"


@pytest.mark.asyncio
async def test_quest_retriever_create_success(mock_redis):
    """Test creating a quest successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    quest = Quest(id="1", name="Test Quest", description="Test", dependencies=[])

    retriever = QuestRetriever()
    result = await retriever.create(quest)

    assert result.id == "1"
    mock_redis.exists.assert_called_once_with("quest:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_quest_retriever_create_duplicate(mock_redis):
    """Test creating a duplicate quest raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    quest = Quest(id="1", name="Test Quest", description="Test", dependencies=[])

    retriever = QuestRetriever()

    with pytest.raises(ValueError, match="Quest with id '1' already exists"):
        await retriever.create(quest)


@pytest.mark.asyncio
async def test_quest_retriever_update_success(mock_redis):
    """Test updating a quest successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    quest = Quest(id="1", name="Updated Quest", description="Updated", dependencies=[])

    retriever = QuestRetriever()
    result = await retriever.update("1", quest)

    assert result.name == "Updated Quest"
    mock_redis.exists.assert_called_once_with("quest:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_quest_retriever_update_not_found(mock_redis):
    """Test updating a non-existent quest raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    quest = Quest(id="1", name="Test Quest", description="Test", dependencies=[])

    retriever = QuestRetriever()

    with pytest.raises(ValueError, match="Quest with id '1' not found"):
        await retriever.update("1", quest)


@pytest.mark.asyncio
async def test_quest_retriever_update_id_mismatch(mock_redis):
    """Test updating with mismatched id raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    quest = Quest(id="2", name="Test Quest", description="Test", dependencies=[])

    retriever = QuestRetriever()

    with pytest.raises(ValueError, match="Quest id mismatch"):
        await retriever.update("1", quest)


@pytest.mark.asyncio
async def test_quest_retriever_delete_success(mock_redis):
    """Test deleting a quest successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    retriever = QuestRetriever()
    await retriever.delete("1")

    mock_redis.exists.assert_called_once_with("quest:1")
    mock_redis.delete.assert_called_once_with("quest:1")


@pytest.mark.asyncio
async def test_quest_retriever_delete_not_found(mock_redis):
    """Test deleting a non-existent quest raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    retriever = QuestRetriever()

    with pytest.raises(ValueError, match="Quest with id '1' not found"):
        await retriever.delete("1")


def test_quest_router_endpoints(client, mock_redis):
    """Test that quest router endpoints work correctly."""
    set_redis_client(mock_redis)

    # Test POST /quest/
    quest_data = {
        "id": "1",
        "name": "Test Quest",
        "description": "Test",
        "dependencies": [],
    }
    mock_redis.exists.return_value = 0

    response = client.post("/quest/", json=quest_data)
    assert response.status_code == 200

    # Test GET /quest/1
    mock_redis.get.return_value = Quest(**quest_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/quest/1")
    assert response.status_code == 200
    assert response.json()["id"] == "1"

    # Test PUT /quest/1
    updated_data = {**quest_data, "name": "Updated Quest"}
    mock_redis.exists.return_value = 1
    response = client.put("/quest/1", json=updated_data)
    assert response.status_code == 200

    # Test DELETE /quest/1
    mock_redis.get.return_value = Quest(**quest_data).model_dump_json()
    mock_redis.exists.return_value = 1
    response = client.delete("/quest/1")
    assert response.status_code == 200

    # Test GET /quest/ (list)
    mock_redis.scan.return_value = (0, ["quest:1"])
    mock_redis.get.return_value = Quest(**quest_data).model_dump_json()
    response = client.get("/quest/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

