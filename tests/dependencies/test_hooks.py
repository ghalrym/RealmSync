from collections import defaultdict
from unittest.mock import MagicMock

from realm_sync_api.dependencies import hooks as hooks_module
from realm_sync_api.dependencies.hooks import (
    HOOKS,
    RealmSyncApiHook,
    RealmSyncHook,
    add_hook,
    get_hooks,
)


def test_get_hooks_returns_defaultdict():
    """Test that get_hooks returns the hooks dictionary."""
    hooks = get_hooks()
    assert isinstance(hooks, dict)
    assert hooks == get_hooks()  # Should return the same instance


def test_add_hook_adds_function_to_hooks():
    """Test that add_hook adds a function to the hooks dictionary."""
    # Clear hooks first
    hooks = get_hooks()
    hooks.clear()

    # Create a mock function
    mock_func = MagicMock()

    # Add hook
    add_hook(RealmSyncHook.PLAYER_CREATED, mock_func)

    # Verify it was added
    assert mock_func in hooks[RealmSyncHook.PLAYER_CREATED]
    assert len(hooks[RealmSyncHook.PLAYER_CREATED]) == 1


def test_add_hook_multiple_functions():
    """Test that multiple functions can be added to the same hook."""
    hooks = get_hooks()
    hooks.clear()

    func1 = MagicMock()
    func2 = MagicMock()

    add_hook(RealmSyncHook.PLAYER_CREATED, func1)
    add_hook(RealmSyncHook.PLAYER_CREATED, func2)

    assert len(hooks[RealmSyncHook.PLAYER_CREATED]) == 2
    assert func1 in hooks[RealmSyncHook.PLAYER_CREATED]
    assert func2 in hooks[RealmSyncHook.PLAYER_CREATED]


def test_add_hook_different_hook_types():
    """Test that functions can be added to different hook types."""
    hooks = get_hooks()
    hooks.clear()

    func1 = MagicMock()
    func2 = MagicMock()

    add_hook(RealmSyncHook.PLAYER_CREATED, func1)
    add_hook(RealmSyncHook.PLAYER_UPDATED, func2)

    assert func1 in hooks[RealmSyncHook.PLAYER_CREATED]
    assert func2 in hooks[RealmSyncHook.PLAYER_UPDATED]
    assert func1 not in hooks[RealmSyncHook.PLAYER_UPDATED]
    assert func2 not in hooks[RealmSyncHook.PLAYER_CREATED]


def test_hooks_module_imports():
    """Test that hooks module can be imported and has expected attributes."""
    assert hasattr(hooks_module, "HOOKS")
    assert hasattr(hooks_module, "RealmSyncApiHook")
    assert hasattr(hooks_module, "get_hooks")
    assert hasattr(hooks_module, "add_hook")


def test_hooks_global_variable():
    """Test that HOOKS is accessible and is a defaultdict."""
    assert isinstance(HOOKS, defaultdict)
    assert HOOKS is get_hooks()  # Should be the same instance


def test_realm_sync_api_hook_type():
    """Test that RealmSyncApiHook is defined."""
    # RealmSyncApiHook is just a type alias, so we just check it exists
    assert RealmSyncApiHook is not None
