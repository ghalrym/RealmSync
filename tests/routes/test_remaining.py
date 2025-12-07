"""Tests for map, npc, and quest routes."""

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.routes import map as map_route
from realm_sync_api.routes import npc as npc_route
from realm_sync_api.routes import quest as quest_route


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock_redis = MagicMock(spec=RealmSyncRedis)
    mock_redis.get.return_value = None
    mock_redis.exists.return_value = 0
    mock_redis.scan.return_value = (0, [])
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    return mock_redis


def test_map_retriever_operations(mock_redis):
    """Test map retriever CRUD operations."""
    from realm_sync_api.models import Map

    set_redis_client(mock_redis)
    retriever = map_route.MapRetriever()

    assert retriever._get_key("123") == "map:123"

    # Test get
    map_data = Map(id="1", name="Test Map")
    mock_redis.get.return_value = map_data.model_dump_json()
    result = retriever.get("1")
    assert result.id == "1"

    # Test get not found
    mock_redis.get.return_value = None
    with pytest.raises(ValueError, match="Map with id '2' not found"):
        retriever.get("2")

    # Test list empty
    mock_redis.scan.return_value = (0, [])
    from realm_sync_api.routes.map import ListRequestArgs

    result = retriever.list(ListRequestArgs())
    assert result == []

    # Test list with items
    map1 = Map(id="1", name="Map 1")
    map2 = Map(id="2", name="Map 2")
    mock_redis.scan.side_effect = [(1, ["map:1"]), (0, ["map:2"])]
    mock_redis.get.side_effect = [map1.model_dump_json(), map2.model_dump_json()]
    result = retriever.list(ListRequestArgs())
    assert len(result) == 2

    # Test create
    mock_redis.exists.return_value = 0
    mock_redis.scan.return_value = (0, [])
    result = retriever.create(map_data)
    assert result.id == "1"

    # Test create duplicate
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="Map with id '1' already exists"):
        retriever.create(map_data)

    # Test update
    mock_redis.exists.return_value = 1
    updated_map = Map(id="1", name="Updated Map")
    result = retriever.update("1", updated_map)
    assert result.name == "Updated Map"

    # Test update not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="Map with id '2' not found"):
        retriever.update("2", updated_map)

    # Test update id mismatch
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="Map id mismatch"):
        retriever.update("1", Map(id="2", name="Test"))

    # Test delete
    mock_redis.exists.return_value = 1
    retriever.delete("1")
    mock_redis.delete.assert_called()

    # Test delete not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="Map with id '2' not found"):
        retriever.delete("2")


def test_npc_retriever_operations(mock_redis):
    """Test npc retriever CRUD operations."""
    from realm_sync_api.models import NPC

    set_redis_client(mock_redis)
    retriever = npc_route.NPCRetriever()

    assert retriever._get_key("123") == "npc:123"

    # Test get
    npc_data = NPC(id="1", name="Test NPC", faction="A", quests=[])
    mock_redis.get.return_value = npc_data.model_dump_json()
    result = retriever.get("1")
    assert result.id == "1"

    # Test get not found
    mock_redis.get.return_value = None
    with pytest.raises(ValueError, match="NPC with id '2' not found"):
        retriever.get("2")

    # Test list with items
    npc1 = NPC(id="1", name="NPC 1", faction="A", quests=[])
    npc2 = NPC(id="2", name="NPC 2", faction="B", quests=[])
    mock_redis.scan.side_effect = [(1, ["npc:1"]), (0, ["npc:2"])]
    mock_redis.get.side_effect = [npc1.model_dump_json(), npc2.model_dump_json()]
    from realm_sync_api.routes.npc import ListRequestArgs

    result = retriever.list(ListRequestArgs())
    assert len(result) == 2

    # Test create
    mock_redis.exists.return_value = 0
    mock_redis.scan.return_value = (0, [])
    result = retriever.create(npc_data)
    assert result.id == "1"

    # Test create duplicate
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="NPC with id '1' already exists"):
        retriever.create(npc_data)

    # Test update
    mock_redis.exists.return_value = 1
    updated_npc = NPC(id="1", name="Updated NPC", faction="B", quests=[])
    result = retriever.update("1", updated_npc)
    assert result.name == "Updated NPC"

    # Test update not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="NPC with id '2' not found"):
        retriever.update("2", updated_npc)

    # Test update id mismatch
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="NPC id mismatch"):
        retriever.update("1", NPC(id="2", name="Test", faction="A", quests=[]))

    # Test delete
    mock_redis.exists.return_value = 1
    retriever.delete("1")
    mock_redis.delete.assert_called()

    # Test delete not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="NPC with id '2' not found"):
        retriever.delete("2")


def test_quest_retriever_operations(mock_redis):
    """Test quest retriever CRUD operations."""
    from realm_sync_api.models import Quest

    set_redis_client(mock_redis)
    retriever = quest_route.QuestRetriever()

    assert retriever._get_key("123") == "quest:123"

    # Test get
    quest_data = Quest(id="1", name="Test Quest", description="Test", dependencies=[])
    mock_redis.get.return_value = quest_data.model_dump_json()
    result = retriever.get("1")
    assert result.id == "1"

    # Test get not found
    mock_redis.get.return_value = None
    with pytest.raises(ValueError, match="Quest with id '2' not found"):
        retriever.get("2")

    # Test list with items
    quest1 = Quest(id="1", name="Quest 1", description="Desc 1", dependencies=[])
    quest2 = Quest(id="2", name="Quest 2", description="Desc 2", dependencies=[])
    mock_redis.scan.side_effect = [(1, ["quest:1"]), (0, ["quest:2"])]
    mock_redis.get.side_effect = [quest1.model_dump_json(), quest2.model_dump_json()]
    from realm_sync_api.routes.quest import ListRequestArgs

    result = retriever.list(ListRequestArgs())
    assert len(result) == 2

    # Test create
    mock_redis.exists.return_value = 0
    mock_redis.scan.return_value = (0, [])
    result = retriever.create(quest_data)
    assert result.id == "1"

    # Test create duplicate
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="Quest with id '1' already exists"):
        retriever.create(quest_data)

    # Test update
    mock_redis.exists.return_value = 1
    updated_quest = Quest(id="1", name="Updated Quest", description="Updated", dependencies=[])
    result = retriever.update("1", updated_quest)
    assert result.name == "Updated Quest"

    # Test update not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="Quest with id '2' not found"):
        retriever.update("2", updated_quest)

    # Test update id mismatch
    mock_redis.exists.return_value = 1
    with pytest.raises(ValueError, match="Quest id mismatch"):
        retriever.update("1", Quest(id="2", name="Test", description="Test", dependencies=[]))

    # Test delete
    mock_redis.exists.return_value = 1
    retriever.delete("1")
    mock_redis.delete.assert_called()

    # Test delete not found
    mock_redis.exists.return_value = 0
    with pytest.raises(ValueError, match="Quest with id '2' not found"):
        retriever.delete("2")


def test_map_router_endpoints(mock_redis):
    """Test map router HTTP endpoints."""
    set_redis_client(mock_redis)
    app = FastAPI()
    app.include_router(map_route.router)
    client = TestClient(app)

    map_data = {"id": "1", "name": "Test Map"}
    mock_redis.exists.return_value = 0

    response = client.post("/map/", json=map_data)
    assert response.status_code == 200

    from realm_sync_api.models import Map

    mock_redis.get.return_value = Map(**map_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/map/1")
    assert response.status_code == 200


def test_npc_router_endpoints(mock_redis):
    """Test npc router HTTP endpoints."""
    set_redis_client(mock_redis)
    app = FastAPI()
    app.include_router(npc_route.router)
    client = TestClient(app)

    npc_data = {"id": "1", "name": "Test NPC", "faction": "A", "quests": []}
    mock_redis.exists.return_value = 0

    response = client.post("/npc/", json=npc_data)
    assert response.status_code == 200

    from realm_sync_api.models import NPC

    mock_redis.get.return_value = NPC(**npc_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/npc/1")
    assert response.status_code == 200


def test_quest_router_endpoints(mock_redis):
    """Test quest router HTTP endpoints."""
    set_redis_client(mock_redis)
    app = FastAPI()
    app.include_router(quest_route.router)
    client = TestClient(app)

    quest_data = {"id": "1", "name": "Test Quest", "description": "Test", "dependencies": []}
    mock_redis.exists.return_value = 0

    response = client.post("/quest/", json=quest_data)
    assert response.status_code == 200

    from realm_sync_api.models import Quest

    mock_redis.get.return_value = Quest(**quest_data).model_dump_json()
    mock_redis.exists.return_value = 1

    response = client.get("/quest/1")
    assert response.status_code == 200
