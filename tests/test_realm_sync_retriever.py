from unittest.mock import MagicMock

import pytest
from pydantic import BaseModel

from realm_sync_api.dependencies.hooks import add_hook
from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.realm_sync_retriever import RealmSyncRetriever


class TestModel(BaseModel):
    id: str
    name: str


class TestListRequestArgs(BaseModel):
    pass


class ConcreteRetriever(RealmSyncRetriever[TestModel, TestListRequestArgs]):
    def __init__(self):
        super().__init__("test")
        self._data: dict[str, TestModel] = {}

    def get(self, id: str) -> TestModel:
        if id not in self._data:
            raise ValueError(f"Not found: {id}")
        return self._data[id]

    def list(self, body: TestListRequestArgs) -> list[TestModel]:
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


def test_realm_sync_retriever_initialization():
    """Test that RealmSyncRetriever initializes with resource_name."""
    retriever = ConcreteRetriever()
    assert retriever.resource_name == "test"


def test_call_hooks_calls_registered_hooks():
    """Test that call_hooks calls all registered hooks."""
    # Clear hooks
    from realm_sync_api.dependencies.hooks import get_hooks

    hooks = get_hooks()
    hooks.clear()

    # Register a hook
    mock_func = MagicMock()
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_func)

    # Create retriever and call hooks
    retriever = ConcreteRetriever()
    test_data = TestModel(id="1", name="Test")
    retriever.call_hooks(RealmSyncHook.PLAYER_CREATED, test_data)

    # Verify hook was called
    mock_func.assert_called_once_with(test_data)


def test_call_hooks_calls_multiple_hooks():
    """Test that call_hooks calls all registered hooks for a hook type."""
    from realm_sync_api.dependencies.hooks import get_hooks

    hooks = get_hooks()
    hooks.clear()

    mock_func1 = MagicMock()
    mock_func2 = MagicMock()
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_func1)
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_func2)

    retriever = ConcreteRetriever()
    test_data = TestModel(id="1", name="Test")
    retriever.call_hooks(RealmSyncHook.PLAYER_CREATED, test_data)

    mock_func1.assert_called_once_with(test_data)
    mock_func2.assert_called_once_with(test_data)


def test_call_hooks_with_kwargs():
    """Test that call_hooks passes kwargs to hooks."""
    from realm_sync_api.dependencies.hooks import get_hooks

    hooks = get_hooks()
    hooks.clear()

    mock_func = MagicMock()
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_func)

    retriever = ConcreteRetriever()
    retriever.call_hooks(RealmSyncHook.PLAYER_CREATED, "arg1", key="value")

    mock_func.assert_called_once_with("arg1", key="value")


def test_call_hooks_with_no_registered_hooks():
    """Test that call_hooks doesn't fail when no hooks are registered."""
    from realm_sync_api.dependencies.hooks import get_hooks

    hooks = get_hooks()
    hooks.clear()

    retriever = ConcreteRetriever()
    # Should not raise an error
    retriever.call_hooks(RealmSyncHook.PLAYER_CREATED, "test")
