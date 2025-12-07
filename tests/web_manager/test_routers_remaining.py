"""Tests for web_manager map, npc, and quest routers."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.routers import map_router, npc_router, quests_router


@pytest.mark.asyncio
async def test_map_router_endpoints():
    """Test map router endpoints."""
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(map_router)
    client = TestClient(app)

    with patch("realm_sync_api.web_manager.routers.map.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [{"id": "1", "name": "Map 1"}]
        response = client.get("/map/")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.map.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "Map 1"}
        response = client.get("/map/1")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.map.create_in_api") as mock_create:
        mock_create.return_value = {"id": "1", "name": "New Map"}
        response = client.post("/map/create", data={"id": "1", "name": "New Map"})
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.map.update_in_api") as mock_update:
        mock_update.return_value = {"id": "1", "name": "Updated Map"}
        response = client.post("/map/1/edit", data={"name": "Updated Map"})
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.map.delete_from_api") as mock_delete:
        mock_delete.return_value = None
        response = client.post("/map/1/delete")
        assert response.status_code == 303


@pytest.mark.asyncio
async def test_npc_router_endpoints():
    """Test npc router endpoints."""
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(npc_router)
    client = TestClient(app)

    with patch("realm_sync_api.web_manager.routers.npc.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [{"id": "1", "name": "NPC 1"}]
        response = client.get("/npc/")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.npc.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "NPC 1"}
        response = client.get("/npc/1")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.npc.create_in_api") as mock_create:
        mock_create.return_value = {"id": "1", "name": "New NPC"}
        response = client.post(
            "/npc/create",
            data={"id": "1", "name": "New NPC", "faction": "A", "quests": "[]"},
        )
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.npc.update_in_api") as mock_update:
        mock_update.return_value = {"id": "1", "name": "Updated NPC"}
        response = client.post(
            "/npc/1/edit",
            data={"name": "Updated NPC", "faction": "B", "quests": "[]"},
        )
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.npc.delete_from_api") as mock_delete:
        mock_delete.return_value = None
        response = client.post("/npc/1/delete")
        assert response.status_code == 303


@pytest.mark.asyncio
async def test_quest_router_endpoints():
    """Test quest router endpoints."""
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(quests_router)
    client = TestClient(app)

    with patch("realm_sync_api.web_manager.routers.quests.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [{"id": "1", "name": "Quest 1"}]
        response = client.get("/quest/")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.quests.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "Quest 1"}
        response = client.get("/quest/1")
        assert response.status_code == 200

    with patch("realm_sync_api.web_manager.routers.quests.create_in_api") as mock_create:
        mock_create.return_value = {"id": "1", "name": "New Quest"}
        response = client.post(
            "/quest/create",
            data={"id": "1", "name": "New Quest", "description": "Test", "dependencies": "[]"},
        )
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.quests.update_in_api") as mock_update:
        mock_update.return_value = {"id": "1", "name": "Updated Quest"}
        response = client.post(
            "/quest/1/edit",
            data={"name": "Updated Quest", "description": "Updated", "dependencies": "[]"},
        )
        assert response.status_code == 303

    with patch("realm_sync_api.web_manager.routers.quests.delete_from_api") as mock_delete:
        mock_delete.return_value = None
        response = client.post("/quest/1/delete")
        assert response.status_code == 303
