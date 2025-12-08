from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.models import Map
from realm_sync_api.routes.map import ListRequestArgs, MapRetriever, router


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


def test_map_retriever_get_key(mock_redis):
    """Test that _get_key returns correct format."""
    set_redis_client(mock_redis)
    retriever = MapRetriever()
    assert retriever._get_key("123") == "map:123"


@pytest.mark.asyncio
async def test_map_retriever_get_success(mock_redis):
    """Test getting a map successfully."""
    set_redis_client(mock_redis)

    map_data = Map(id="1", name="Test Map")
    mock_redis.get = AsyncMock(return_value=map_data.model_dump_json())

    retriever = MapRetriever()
    result = await retriever.get("1")

    assert result.id == "1"
    assert result.name == "Test Map"
    mock_redis.get.assert_called_once_with("map:1")


@pytest.mark.asyncio
async def test_map_retriever_get_not_found(mock_redis):
    """Test getting a non-existent map raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.get = AsyncMock(return_value=None)

    retriever = MapRetriever()

    with pytest.raises(ValueError, match="Map with id '1' not found"):
        await retriever.get("1")


@pytest.mark.asyncio
async def test_map_retriever_list_empty(mock_redis):
    """Test listing maps when there are none."""
    set_redis_client(mock_redis)
    mock_redis.scan = AsyncMock(return_value=(0, []))

    retriever = MapRetriever()
    result = await retriever.list(ListRequestArgs())

    assert result == []


@pytest.mark.asyncio
async def test_map_retriever_list_with_maps(mock_redis):
    """Test listing maps."""
    set_redis_client(mock_redis)

    map1 = Map(id="1", name="Map 1")
    map2 = Map(id="2", name="Map 2")

    # Mock scan to return keys in batches
    mock_redis.scan = AsyncMock(side_effect=[(1, ["map:1"]), (0, ["map:2"])])
    mock_redis.get = AsyncMock(side_effect=[map1.model_dump_json(), map2.model_dump_json()])

    retriever = MapRetriever()
    result = await retriever.list(ListRequestArgs())

    assert len(result) == 2
    assert result[0].id == "1"
    assert result[1].id == "2"


@pytest.mark.asyncio
async def test_map_retriever_create_success(mock_redis):
    """Test creating a map successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    map_obj = Map(id="1", name="Test Map")

    retriever = MapRetriever()
    result = await retriever.create(map_obj)

    assert result.id == "1"
    mock_redis.exists.assert_called_once_with("map:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_map_retriever_create_duplicate(mock_redis):
    """Test creating a duplicate map raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    map_obj = Map(id="1", name="Test Map")

    retriever = MapRetriever()

    with pytest.raises(ValueError, match="Map with id '1' already exists"):
        await retriever.create(map_obj)


@pytest.mark.asyncio
async def test_map_retriever_update_success(mock_redis):
    """Test updating a map successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    map_obj = Map(id="1", name="Updated Map")

    retriever = MapRetriever()
    result = await retriever.update("1", map_obj)

    assert result.name == "Updated Map"
    mock_redis.exists.assert_called_once_with("map:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_map_retriever_update_not_found(mock_redis):
    """Test updating a non-existent map raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    map_obj = Map(id="1", name="Test Map")

    retriever = MapRetriever()

    with pytest.raises(ValueError, match="Map with id '1' not found"):
        await retriever.update("1", map_obj)


@pytest.mark.asyncio
async def test_map_retriever_update_id_mismatch(mock_redis):
    """Test updating with mismatched id raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    map_obj = Map(id="2", name="Test Map")

    retriever = MapRetriever()

    with pytest.raises(ValueError, match="Map id mismatch"):
        await retriever.update("1", map_obj)


@pytest.mark.asyncio
async def test_map_retriever_delete_success(mock_redis):
    """Test deleting a map successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    retriever = MapRetriever()
    await retriever.delete("1")

    mock_redis.exists.assert_called_once_with("map:1")
    mock_redis.delete.assert_called_once_with("map:1")


@pytest.mark.asyncio
async def test_map_retriever_delete_not_found(mock_redis):
    """Test deleting a non-existent map raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    retriever = MapRetriever()

    with pytest.raises(ValueError, match="Map with id '1' not found"):
        await retriever.delete("1")


def test_map_router_endpoints(client, mock_redis):
    """Test that map router endpoints work correctly."""
    set_redis_client(mock_redis)

    # Test POST /map/
    map_data = {"id": "1", "name": "Test Map"}
    mock_redis.exists.return_value = 0

    response = client.post("/map/", json=map_data)
    assert response.status_code == 200

    # Test GET /map/1
    mock_redis.get.return_value = Map(**map_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/map/1")
    assert response.status_code == 200
    assert response.json()["id"] == "1"

    # Test PUT /map/1
    updated_data = {**map_data, "name": "Updated Map"}
    mock_redis.exists.return_value = 1
    response = client.put("/map/1", json=updated_data)
    assert response.status_code == 200

    # Test DELETE /map/1
    mock_redis.get.return_value = Map(**map_data).model_dump_json()
    mock_redis.exists.return_value = 1
    response = client.delete("/map/1")
    assert response.status_code == 200

    # Test GET /map/ (list)
    mock_redis.scan.return_value = (0, ["map:1"])
    mock_redis.get.return_value = Map(**map_data).model_dump_json()
    response = client.get("/map/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
