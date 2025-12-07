"""Tests for body parsing in realm_sync_router list endpoint."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
from realm_sync_api.realm_sync_router import RealmSyncRouter


class TestModel(BaseModel):
    id: str
    name: str


class TestListRequestArgs(BaseModel):
    limit: int = 10
    offset: int = 0


class TestRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
    def __init__(self):
        super().__init__("test")
        self._data: dict[str, TestModel] = {}
        self._list_calls: list[TestListRequestArgs] = []

    def get(self, id: str) -> TestModel:
        if id not in self._data:
            raise ValueError(f"Not found: {id}")
        return self._data[id]

    def list(self, body: TestListRequestArgs) -> list[TestModel]:
        self._list_calls.append(body)
        return list(self._data.values())

    def create(self, data: TestModel) -> TestModel:
        self._data[data.id] = data
        return data

    def update(self, id: str, data: TestModel) -> TestModel:
        if id not in self._data:
            raise ValueError(f"Not found: {id}")
        self._data[id] = data
        return data

    def delete(self, id: str) -> None:
        if id not in self._data:
            raise ValueError(f"Not found: {id}")
        del self._data[id]


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    retriever = TestRetriever()
    router.register_retriever(retriever)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


async def test_list_endpoint_with_valid_json_body():
    """Test list endpoint with valid JSON body."""
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    retriever = TestRetriever()
    router.register_retriever(retriever)
    app.include_router(router)

    # Create a mock request with body
    mock_request = MagicMock(spec=Request)
    body_data = {"limit": 5, "offset": 10}
    mock_request.body = AsyncMock(return_value=json.dumps(body_data).encode())

    # Get the list endpoint
    list_endpoint = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/test/":
            list_endpoint = route.endpoint
            break

    if list_endpoint:
        result = await list_endpoint(mock_request)
        assert isinstance(result, list)
        # Verify the body was parsed
        assert len(retriever._list_calls) == 1
        assert retriever._list_calls[0].limit == 5
        assert retriever._list_calls[0].offset == 10


async def test_list_endpoint_with_invalid_json_body():
    """Test list endpoint with invalid JSON body falls back to default."""
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    retriever = TestRetriever()
    router.register_retriever(retriever)
    app.include_router(router)

    # Create a mock request with invalid JSON body
    mock_request = MagicMock(spec=Request)
    mock_request.body = AsyncMock(return_value=b"invalid json{")

    # Get the list endpoint
    list_endpoint = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/test/":
            list_endpoint = route.endpoint
            break

    if list_endpoint:
        result = await list_endpoint(mock_request)
        assert isinstance(result, list)
        # Should use default args
        assert len(retriever._list_calls) == 1
        assert retriever._list_calls[0].limit == 10
        assert retriever._list_calls[0].offset == 0


async def test_list_endpoint_with_empty_body():
    """Test list endpoint with empty body uses default."""
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    retriever = TestRetriever()
    router.register_retriever(retriever)
    app.include_router(router)

    # Create a mock request with empty body
    mock_request = MagicMock(spec=Request)
    mock_request.body = AsyncMock(return_value=b"")

    # Get the list endpoint
    list_endpoint = None
    for route in app.routes:
        if hasattr(route, "path") and route.path == "/test/":
            list_endpoint = route.endpoint
            break

    if list_endpoint:
        result = await list_endpoint(mock_request)
        assert isinstance(result, list)
        # Should use default args
        assert len(retriever._list_calls) == 1
        assert retriever._list_calls[0].limit == 10
        assert retriever._list_calls[0].offset == 0
