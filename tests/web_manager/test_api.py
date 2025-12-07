"""Tests for web_manager api functions."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.api import (
    create_in_api,
    delete_from_api,
    fetch_from_api,
    get_base_url,
    get_from_api,
    update_in_api,
)


@pytest.fixture
def mock_request():
    """Create a mock request."""
    request = MagicMock(spec=Request)
    request.url.scheme = "http"
    request.url.netloc = "localhost:8000"
    return request


def test_get_base_url(mock_request):
    """Test that get_base_url returns correct URL."""
    result = get_base_url(mock_request)
    assert result == "http://localhost:8000"


@pytest.mark.asyncio
async def test_fetch_from_api_success(mock_request):
    """Test fetch_from_api successfully fetches data."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"id": "1", "name": "Test"}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        result = await fetch_from_api(mock_request, "/player/")
        assert result == [{"id": "1", "name": "Test"}]


@pytest.mark.asyncio
async def test_fetch_from_api_error(mock_request):
    """Test fetch_from_api handles HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.side_effect = httpx.HTTPError("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await fetch_from_api(mock_request, "/player/")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_from_api_success(mock_request):
    """Test get_from_api successfully gets data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "1", "name": "Test"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response

        result = await get_from_api(mock_request, "/player/1")
        assert result == {"id": "1", "name": "Test"}


@pytest.mark.asyncio
async def test_get_from_api_error(mock_request):
    """Test get_from_api handles HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.side_effect = httpx.HTTPError("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_from_api(mock_request, "/player/1")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_create_in_api_success(mock_request):
    """Test create_in_api successfully creates data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "1", "name": "Test"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.return_value = mock_response

        result = await create_in_api(mock_request, "/player/", {"name": "Test"})
        assert result == {"id": "1", "name": "Test"}


@pytest.mark.asyncio
async def test_create_in_api_http_status_error(mock_request):
    """Test create_in_api handles HTTPStatusError."""
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.reason_phrase = "Bad Request"
    mock_request_obj = MagicMock()
    mock_request_obj.url = "http://localhost:8000/player/"

    error = httpx.HTTPStatusError("Error", request=mock_request_obj, response=mock_response)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.side_effect = error

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_in_api(mock_request, "/player/", {"name": "Test"})
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_create_in_api_http_error(mock_request):
    """Test create_in_api handles HTTPError."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.post.side_effect = httpx.HTTPError("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await create_in_api(mock_request, "/player/", {"name": "Test"})
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_update_in_api_success(mock_request):
    """Test update_in_api successfully updates data."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "1", "name": "Updated"}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.put.return_value = mock_response

        result = await update_in_api(mock_request, "/player/1", {"name": "Updated"})
        assert result == {"id": "1", "name": "Updated"}


@pytest.mark.asyncio
async def test_update_in_api_error(mock_request):
    """Test update_in_api handles HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.put.side_effect = httpx.HTTPError("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await update_in_api(mock_request, "/player/1", {"name": "Updated"})
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_delete_from_api_success(mock_request):
    """Test delete_from_api successfully deletes data."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.delete.return_value = mock_response

        await delete_from_api(mock_request, "/player/1")
        mock_client_instance.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_from_api_error(mock_request):
    """Test delete_from_api handles HTTP errors."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = AsyncMock()
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        mock_client_instance.delete.side_effect = httpx.HTTPError("Connection error")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await delete_from_api(mock_request, "/player/1")
        assert exc_info.value.status_code == 500
