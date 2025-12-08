from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.models import Item
from realm_sync_api.routes.item import ItemRetriever, ListRequestArgs, router


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


def test_item_retriever_get_key(mock_redis):
    """Test that _get_key returns correct format."""
    set_redis_client(mock_redis)
    retriever = ItemRetriever()
    assert retriever._get_key("123") == "item:123"


@pytest.mark.asyncio
async def test_item_retriever_get_success(mock_redis):
    """Test getting an item successfully."""
    set_redis_client(mock_redis)

    item_data = Item(id="1", name="Test Item", type="weapon")
    mock_redis.get = AsyncMock(return_value=item_data.model_dump_json())

    retriever = ItemRetriever()
    result = await retriever.get("1")

    assert result.id == "1"
    assert result.name == "Test Item"
    mock_redis.get.assert_called_once_with("item:1")


@pytest.mark.asyncio
async def test_item_retriever_get_not_found(mock_redis):
    """Test getting a non-existent item raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.get = AsyncMock(return_value=None)

    retriever = ItemRetriever()

    with pytest.raises(ValueError, match="Item with id '1' not found"):
        await retriever.get("1")


@pytest.mark.asyncio
async def test_item_retriever_list_empty(mock_redis):
    """Test listing items when there are none."""
    set_redis_client(mock_redis)
    mock_redis.scan = AsyncMock(return_value=(0, []))

    retriever = ItemRetriever()
    result = await retriever.list(ListRequestArgs())

    assert result == []


@pytest.mark.asyncio
async def test_item_retriever_create_success(mock_redis):
    """Test creating an item successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    item = Item(id="1", name="Test Item", type="weapon")

    retriever = ItemRetriever()
    result = await retriever.create(item)

    assert result.id == "1"
    mock_redis.exists.assert_called_once_with("item:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_item_retriever_create_duplicate(mock_redis):
    """Test creating a duplicate item raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    item = Item(id="1", name="Test Item", type="weapon")

    retriever = ItemRetriever()

    with pytest.raises(ValueError, match="Item with id '1' already exists"):
        await retriever.create(item)


@pytest.mark.asyncio
async def test_item_retriever_update_success(mock_redis):
    """Test updating an item successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    item = Item(id="1", name="Updated Item", type="armor")

    retriever = ItemRetriever()
    result = await retriever.update("1", item)

    assert result.name == "Updated Item"
    mock_redis.exists.assert_called_once_with("item:1")
    mock_redis.set.assert_called_once()


@pytest.mark.asyncio
async def test_item_retriever_update_not_found(mock_redis):
    """Test updating a non-existent item raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    item = Item(id="1", name="Test Item", type="weapon")

    retriever = ItemRetriever()

    with pytest.raises(ValueError, match="Item with id '1' not found"):
        await retriever.update("1", item)


@pytest.mark.asyncio
async def test_item_retriever_update_id_mismatch(mock_redis):
    """Test updating with mismatched id raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    item = Item(id="2", name="Test Item", type="weapon")

    retriever = ItemRetriever()

    with pytest.raises(ValueError, match="Item id mismatch"):
        await retriever.update("1", item)


@pytest.mark.asyncio
async def test_item_retriever_delete_success(mock_redis):
    """Test deleting an item successfully."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=1)

    retriever = ItemRetriever()
    await retriever.delete("1")

    mock_redis.exists.assert_called_once_with("item:1")
    mock_redis.delete.assert_called_once_with("item:1")


@pytest.mark.asyncio
async def test_item_retriever_delete_not_found(mock_redis):
    """Test deleting a non-existent item raises ValueError."""
    set_redis_client(mock_redis)
    mock_redis.exists = AsyncMock(return_value=0)

    retriever = ItemRetriever()

    with pytest.raises(ValueError, match="Item with id '1' not found"):
        await retriever.delete("1")


def test_item_router_endpoints(client, mock_redis):
    """Test that item router endpoints work correctly."""
    set_redis_client(mock_redis)

    # Test POST /item/
    item_data = {"id": "1", "name": "Test Item", "type": "weapon"}
    mock_redis.exists.return_value = 0

    response = client.post("/item/", json=item_data)
    assert response.status_code == 200

    # Test GET /item/1
    mock_redis.get.return_value = Item(**item_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/item/1")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    assert response.json()["id"] == "1"

    # Test PUT /item/1
    updated_data = {**item_data, "name": "Updated Item"}
    mock_redis.exists.return_value = 1
    response = client.put("/item/1", json=updated_data)
    assert response.status_code == 200

    # Test DELETE /item/1
    mock_redis.get.return_value = Item(**item_data).model_dump_json()
    mock_redis.exists.return_value = 1
    response = client.delete("/item/1")
    assert response.status_code == 200

    # Test GET /item/ (list)
    mock_redis.scan.return_value = (0, ["item:1"])
    mock_redis.get.return_value = Item(**item_data).model_dump_json()
    response = client.get("/item/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
