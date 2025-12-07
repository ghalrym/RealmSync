from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
from realm_sync_api.realm_sync_router import RealmSyncRouter


class MockModel(BaseModel):
    id: str
    name: str


class MockListRequestArgs(BaseModel):
    limit: int = 10
    offset: int = 0


class MockRetriever(RealmSyncRetriever[MockModel, MockListRequestArgs]):
    def __init__(self):
        super().__init__("test")
        self._data: dict[str, MockModel] = {}
        self._list_calls: list[MockListRequestArgs] = []

    def get(self, id: str) -> MockModel:
        if id not in self._data:
            raise ValueError(f"MockModel with id '{id}' not found")
        return self._data[id]

    def list(self, body: MockListRequestArgs) -> list[MockModel]:
        self._list_calls.append(body)
        return list(self._data.values())

    def create(self, data: MockModel) -> MockModel:
        if data.id in self._data:
            raise ValueError(f"MockModel with id '{data.id}' already exists")
        self._data[data.id] = data
        return data

    def update(self, id: str, data: MockModel) -> MockModel:
        if id not in self._data:
            raise ValueError(f"MockModel with id '{id}' not found")
        if data.id != id:
            raise ValueError(f"MockModel id mismatch: expected '{id}', got '{data.id}'")
        self._data[id] = data
        return data

    def delete(self, id: str) -> None:
        if id not in self._data:
            raise ValueError(f"TestModel with id '{id}' not found")
        del self._data[id]


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    retriever = MockRetriever()
    router.register_retriever(retriever)
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def retriever():
    """Create a mock retriever instance."""
    return MockRetriever()


def test_register_retriever_creates_endpoints(app):
    """Test that registering a retriever creates all CRUD endpoints."""
    client = TestClient(app)

    # Check that endpoints exist by trying to access them
    # GET /test/ should return 200 (even if empty)
    response = client.get("/test/")
    assert response.status_code == 200

    # POST /test/ should accept data
    # GET /test/{key} should return 404 for non-existent
    response = client.get("/test/nonexistent")
    assert response.status_code == 404

    # PUT /test/{key} should return 400 for non-existent (ValueError becomes 400)
    response = client.put("/test/nonexistent", json={"id": "nonexistent", "name": "test"})
    assert response.status_code == 400

    # DELETE /test/{key} should return 404 for non-existent
    response = client.delete("/test/nonexistent")
    assert response.status_code == 404


def test_register_retriever_with_invalid_type_raises_error():
    """Test that registering a retriever without proper type parameters raises an error."""
    router = RealmSyncRouter()

    # Create a retriever that doesn't properly inherit from RealmSyncRetriever with types
    class InvalidRetriever:
        pass

    with pytest.raises(ValueError, match="Could not extract type parameters"):
        router.register_retriever(InvalidRetriever())


def test_list_empty(client):
    """Test listing when there are no items."""
    response = client.get("/test/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_with_items(client):
    """Test listing when there are items."""
    # Create some items
    client.post("/test/", json={"id": "1", "name": "Item 1"})
    client.post("/test/", json={"id": "2", "name": "Item 2"})

    response = client.get("/test/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["id"] for item in data} == {"1", "2"}


def test_list_with_default_args(client):
    """Test list endpoint uses default ListRequestArgs when no body provided."""
    # Create items
    client.post("/test/", json={"id": "1", "name": "Item 1"})

    # List without body should use default ListRequestArgs
    response = client.get("/test/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_create_success(client):
    """Test creating an item successfully."""
    response = client.post("/test/", json={"id": "1", "name": "Test Item"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["name"] == "Test Item"


def test_create_duplicate_raises_error(client):
    """Test creating a duplicate item raises an error."""
    client.post("/test/", json={"id": "1", "name": "Test Item"})

    response = client.post("/test/", json={"id": "1", "name": "Duplicate"})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_create_with_invalid_data(client):
    """Test creating with invalid data."""
    response = client.post("/test/", json={"id": "1"})  # Missing required 'name'
    assert response.status_code == 422  # Validation error from FastAPI


def test_get_success(client):
    """Test getting an item successfully."""
    client.post("/test/", json={"id": "1", "name": "Test Item"})

    response = client.get("/test/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["name"] == "Test Item"


def test_get_not_found(client):
    """Test getting a non-existent item."""
    response = client.get("/test/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_success(client):
    """Test updating an item successfully."""
    client.post("/test/", json={"id": "1", "name": "Original"})

    response = client.put("/test/1", json={"id": "1", "name": "Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"

    # Verify it was updated
    get_response = client.get("/test/1")
    assert get_response.json()["name"] == "Updated"


def test_update_not_found(client):
    """Test updating a non-existent item."""
    response = client.put("/test/nonexistent", json={"id": "nonexistent", "name": "Test"})
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_update_id_mismatch(client):
    """Test updating with mismatched id."""
    client.post("/test/", json={"id": "1", "name": "Original"})

    response = client.put("/test/1", json={"id": "2", "name": "Updated"})
    assert response.status_code == 400
    assert "mismatch" in response.json()["detail"]


def test_delete_success(client):
    """Test deleting an item successfully."""
    client.post("/test/", json={"id": "1", "name": "Test Item"})

    response = client.delete("/test/1")
    assert response.status_code == 200

    # Verify it was deleted
    get_response = client.get("/test/1")
    assert get_response.status_code == 404


def test_delete_not_found(client):
    """Test deleting a non-existent item."""
    response = client.delete("/test/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_generic_exception_returns_500():
    """Test that generic exceptions return 500."""
    retriever = MockRetriever()

    # Mock the get method to raise a generic exception
    retriever.get = MagicMock(side_effect=Exception("Unexpected error"))

    # Re-register with the mocked retriever
    app = FastAPI()
    router = RealmSyncRouter(prefix="/test", tags=["test"])
    router.register_retriever(retriever)
    app.include_router(router)
    test_client = TestClient(app)

    response = test_client.get("/test/1")
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_value_error_returns_appropriate_status(client):
    """Test that ValueError returns appropriate status codes."""
    # Create endpoint should return 400 for ValueError
    client.post("/test/", json={"id": "1", "name": "Test"})
    response = client.post("/test/", json={"id": "1", "name": "Duplicate"})
    assert response.status_code == 400

    # Get endpoint should return 404 for ValueError
    response = client.get("/test/nonexistent")
    assert response.status_code == 404

    # Delete endpoint should return 404 for ValueError
    response = client.delete("/test/nonexistent")
    assert response.status_code == 404


def test_list_endpoint_value_error_handling(app):
    """Test that list endpoint handles ValueError correctly."""
    from unittest.mock import MagicMock

    from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
    from realm_sync_api.realm_sync_router import RealmSyncRouter

    class TestModel(BaseModel):
        id: str
        name: str

    class TestListRequestArgs(BaseModel):
        pass

    class ErrorRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
        def __init__(self):
            super().__init__("test")

        def get(self, id: str) -> TestModel:
            pass

        def list(self, body: TestListRequestArgs) -> list[TestModel]:
            raise ValueError("List error")

        def create(self, data: TestModel) -> TestModel:
            pass

        def update(self, id: str, data: TestModel) -> TestModel:
            pass

        def delete(self, id: str) -> None:
            pass

    router = RealmSyncRouter(prefix="/error", tags=["error"])
    router.register_retriever(ErrorRetriever())
    app.include_router(router)

    client = TestClient(app)
    response = client.get("/error/")
    assert response.status_code == 400
    assert "List error" in response.json()["detail"]


def test_list_endpoint_generic_exception_handling(app):
    """Test that list endpoint handles generic exceptions correctly."""
    from unittest.mock import MagicMock

    from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
    from realm_sync_api.realm_sync_router import RealmSyncRouter

    class TestModel(BaseModel):
        id: str
        name: str

    class TestListRequestArgs(BaseModel):
        pass

    class ErrorRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
        def __init__(self):
            super().__init__("test")

        def get(self, id: str) -> TestModel:
            pass

        def list(self, body: TestListRequestArgs) -> list[TestModel]:
            raise Exception("Generic error")

        def create(self, data: TestModel) -> TestModel:
            pass

        def update(self, id: str, data: TestModel) -> TestModel:
            pass

        def delete(self, id: str) -> None:
            pass

    router = RealmSyncRouter(prefix="/error", tags=["error"])
    router.register_retriever(ErrorRetriever())
    app.include_router(router)

    client = TestClient(app)
    response = client.get("/error/")
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_create_endpoint_generic_exception_handling(app):
    """Test that create endpoint handles generic exceptions correctly."""
    from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
    from realm_sync_api.realm_sync_router import RealmSyncRouter

    class TestModel(BaseModel):
        id: str
        name: str

    class TestListRequestArgs(BaseModel):
        pass

    class ErrorRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
        def __init__(self):
            super().__init__("test")

        def get(self, id: str) -> TestModel:
            pass

        def list(self, body: TestListRequestArgs) -> list[TestModel]:
            return []

        def create(self, data: TestModel) -> TestModel:
            raise Exception("Generic error")

        def update(self, id: str, data: TestModel) -> TestModel:
            pass

        def delete(self, id: str) -> None:
            pass

    router = RealmSyncRouter(prefix="/error", tags=["error"])
    router.register_retriever(ErrorRetriever())
    app.include_router(router)

    client = TestClient(app)
    response = client.post("/error/", json={"id": "1", "name": "Test"})
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_update_endpoint_generic_exception_handling(app):
    """Test that update endpoint handles generic exceptions correctly."""
    from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
    from realm_sync_api.realm_sync_router import RealmSyncRouter

    class TestModel(BaseModel):
        id: str
        name: str

    class TestListRequestArgs(BaseModel):
        pass

    class ErrorRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
        def __init__(self):
            super().__init__("test")

        def get(self, id: str) -> TestModel:
            pass

        def list(self, body: TestListRequestArgs) -> list[TestModel]:
            return []

        def create(self, data: TestModel) -> TestModel:
            pass

        def update(self, id: str, data: TestModel) -> TestModel:
            raise Exception("Generic error")

        def delete(self, id: str) -> None:
            pass

    router = RealmSyncRouter(prefix="/error", tags=["error"])
    router.register_retriever(ErrorRetriever())
    app.include_router(router)

    client = TestClient(app)
    response = client.put("/error/1", json={"id": "1", "name": "Test"})
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


def test_delete_endpoint_generic_exception_handling(app):
    """Test that delete endpoint handles generic exceptions correctly."""
    from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
    from realm_sync_api.realm_sync_router import RealmSyncRouter

    class TestModel(BaseModel):
        id: str
        name: str

    class TestListRequestArgs(BaseModel):
        pass

    class ErrorRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
        def __init__(self):
            super().__init__("test")

        def get(self, id: str) -> TestModel:
            pass

        def list(self, body: TestListRequestArgs) -> list[TestModel]:
            return []

        def create(self, data: TestModel) -> TestModel:
            pass

        def update(self, id: str, data: TestModel) -> TestModel:
            pass

        def delete(self, id: str) -> None:
            raise Exception("Generic error")

    router = RealmSyncRouter(prefix="/error", tags=["error"])
    router.register_retriever(ErrorRetriever())
    app.include_router(router)

    client = TestClient(app)
    response = client.delete("/error/1")
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]
