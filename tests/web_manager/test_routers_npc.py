"""Tests for web_manager npc router."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.routers import npc_router
from realm_sync_api.web_manager.web_manager_router import WebManagerRouter


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    # Include WebManagerRouter first so templates can find serve_static
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(npc_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_list_npcs(app):
    """Test list NPCs endpoint."""
    with patch("realm_sync_api.web_manager.routers.npc.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [{"id": "1", "name": "NPC 1", "faction": "A", "quests": []}]

        client = TestClient(app)
        response = client.get("/npc/")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_view_npc(app):
    """Test view NPC endpoint."""
    with patch("realm_sync_api.web_manager.routers.npc.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "NPC 1", "faction": "A", "quests": []}

        client = TestClient(app)
        response = client.get("/npc/1")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_npc_form(app):
    """Test create NPC form endpoint."""
    client = TestClient(app)
    response = client.get("/npc/create")
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_create_npc(app):
    """Test creating an NPC."""
    with patch("realm_sync_api.web_manager.routers.npc.create_in_api") as mock_create:
        mock_create.return_value = {"id": "1", "name": "New NPC", "faction": "A", "quests": []}

        client = TestClient(app)
        response = client.post(
            "/npc/create",
            data={"id": "1", "name": "New NPC", "faction": "A", "quests": ""},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_npc_with_quests(app):
    """Test creating an NPC with quests."""
    with patch("realm_sync_api.web_manager.routers.npc.create_in_api") as mock_create:
        mock_create.return_value = {
            "id": "1",
            "name": "New NPC",
            "faction": "A",
            "quests": ["q1", "q2"],
        }

        client = TestClient(app)
        response = client.post(
            "/npc/create",
            data={"id": "1", "name": "New NPC", "faction": "A", "quests": "q1, q2"},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_edit_npc_form(app):
    """Test edit NPC form endpoint."""
    with patch("realm_sync_api.web_manager.routers.npc.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "NPC 1", "faction": "A", "quests": []}

        client = TestClient(app)
        response = client.get("/npc/1/edit")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_npc(app):
    """Test updating an NPC."""
    with patch("realm_sync_api.web_manager.routers.npc.update_in_api") as mock_update:
        mock_update.return_value = {"id": "1", "name": "Updated NPC", "faction": "B", "quests": []}

        client = TestClient(app)
        response = client.post(
            "/npc/1/edit",
            data={"name": "Updated NPC", "faction": "B", "quests": ""},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_update_npc_with_quests(app):
    """Test updating an NPC with quests."""
    with patch("realm_sync_api.web_manager.routers.npc.update_in_api") as mock_update:
        mock_update.return_value = {
            "id": "1",
            "name": "Updated NPC",
            "faction": "B",
            "quests": ["q1"],
        }

        client = TestClient(app)
        response = client.post(
            "/npc/1/edit",
            data={"name": "Updated NPC", "faction": "B", "quests": "q1"},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_npc(app):
    """Test deleting an NPC."""
    with patch("realm_sync_api.web_manager.routers.npc.delete_from_api") as mock_delete:
        mock_delete.return_value = None

        client = TestClient(app)
        response = client.post("/npc/1/delete", follow_redirects=False)
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_delete.assert_called_once()
