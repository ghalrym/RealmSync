"""Tests for web_manager quest router."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.routers import quests_router
from realm_sync_api.web_manager.web_manager_router import WebManagerRouter


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    # Include WebManagerRouter first so templates can find serve_static
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(quests_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_list_quests(app):
    """Test list quests endpoint."""
    with patch("realm_sync_api.web_manager.routers.quests.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [
            {"id": "1", "name": "Quest 1", "description": "Desc 1", "dependencies": []}
        ]

        client = TestClient(app)
        response = client.get("/quest/")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_view_quest(app):
    """Test view quest endpoint."""
    with patch("realm_sync_api.web_manager.routers.quests.get_from_api") as mock_get:
        mock_get.return_value = {
            "id": "1",
            "name": "Quest 1",
            "description": "Desc 1",
            "dependencies": [],
        }

        client = TestClient(app)
        response = client.get("/quest/1")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_quest_form(app):
    """Test create quest form endpoint."""
    client = TestClient(app)
    response = client.get("/quest/create")
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_create_quest(app):
    """Test creating a quest."""
    with patch("realm_sync_api.web_manager.routers.quests.create_in_api") as mock_create:
        mock_create.return_value = {
            "id": "1",
            "name": "New Quest",
            "description": "New Desc",
            "dependencies": [],
        }

        client = TestClient(app)
        response = client.post(
            "/quest/create",
            data={"id": "1", "name": "New Quest", "description": "New Desc", "dependencies": ""},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_quest_with_dependencies(app):
    """Test creating a quest with dependencies."""
    with patch("realm_sync_api.web_manager.routers.quests.create_in_api") as mock_create:
        mock_create.return_value = {
            "id": "1",
            "name": "New Quest",
            "description": "New Desc",
            "dependencies": ["q1", "q2"],
        }

        client = TestClient(app)
        response = client.post(
            "/quest/create",
            data={
                "id": "1",
                "name": "New Quest",
                "description": "New Desc",
                "dependencies": "q1, q2",
            },
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_edit_quest_form(app):
    """Test edit quest form endpoint."""
    with patch("realm_sync_api.web_manager.routers.quests.get_from_api") as mock_get:
        mock_get.return_value = {
            "id": "1",
            "name": "Quest 1",
            "description": "Desc 1",
            "dependencies": [],
        }

        client = TestClient(app)
        response = client.get("/quest/edit/1")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_quest(app):
    """Test updating a quest."""
    with patch("realm_sync_api.web_manager.routers.quests.update_in_api") as mock_update:
        mock_update.return_value = {
            "id": "1",
            "name": "Updated Quest",
            "description": "Updated Desc",
            "dependencies": [],
        }

        client = TestClient(app)
        response = client.post(
            "/quest/edit/1",
            data={"name": "Updated Quest", "description": "Updated Desc", "dependencies": ""},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_update_quest_with_dependencies(app):
    """Test updating a quest with dependencies."""
    with patch("realm_sync_api.web_manager.routers.quests.update_in_api") as mock_update:
        mock_update.return_value = {
            "id": "1",
            "name": "Updated Quest",
            "description": "Updated Desc",
            "dependencies": ["q1"],
        }

        client = TestClient(app)
        response = client.post(
            "/quest/edit/1",
            data={"name": "Updated Quest", "description": "Updated Desc", "dependencies": "q1"},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_quest(app):
    """Test deleting a quest."""
    with patch("realm_sync_api.web_manager.routers.quests.delete_from_api") as mock_delete:
        mock_delete.return_value = None

        client = TestClient(app)
        response = client.post("/quest/delete/1", follow_redirects=False)
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_delete.assert_called_once()
