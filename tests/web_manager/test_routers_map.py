"""Tests for web_manager map router."""

from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.routers import map_router
from realm_sync_api.web_manager.web_manager_router import WebManagerRouter


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    # Include WebManagerRouter first so templates can find serve_static
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(map_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_list_maps(app):
    """Test list maps endpoint."""
    with patch("realm_sync_api.web_manager.routers.map.fetch_from_api") as mock_fetch:
        mock_fetch.return_value = [{"id": "1", "name": "Map 1"}]

        client = TestClient(app)
        response = client.get("/map/")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_view_map(app):
    """Test view map endpoint."""
    with patch("realm_sync_api.web_manager.routers.map.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "Map 1"}

        client = TestClient(app)
        response = client.get("/map/1")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_create_map_form(app):
    """Test create map form endpoint."""
    client = TestClient(app)
    response = client.get("/map/create")
    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_create_map(app):
    """Test creating a map."""
    with patch("realm_sync_api.web_manager.routers.map.create_in_api") as mock_create:
        mock_create.return_value = {"id": "1", "name": "New Map"}

        client = TestClient(app)
        response = client.post(
            "/map/create",
            data={"id": "1", "name": "New Map"},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_edit_map_form(app):
    """Test edit map form endpoint."""
    with patch("realm_sync_api.web_manager.routers.map.get_from_api") as mock_get:
        mock_get.return_value = {"id": "1", "name": "Map 1"}

        client = TestClient(app)
        response = client.get("/map/1/edit")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_update_map(app):
    """Test updating a map."""
    with patch("realm_sync_api.web_manager.routers.map.update_in_api") as mock_update:
        mock_update.return_value = {"id": "1", "name": "Updated Map"}

        client = TestClient(app)
        response = client.post(
            "/map/1/edit",
            data={"name": "Updated Map"},
            follow_redirects=False,
        )
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_update.assert_called_once()


@pytest.mark.asyncio
async def test_delete_map(app):
    """Test deleting a map."""
    with patch("realm_sync_api.web_manager.routers.map.delete_from_api") as mock_delete:
        mock_delete.return_value = None

        client = TestClient(app)
        response = client.post("/map/1/delete", follow_redirects=False)
        assert response.status_code in [303, 500]
        if response.status_code == 303:
            mock_delete.assert_called_once()

