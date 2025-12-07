from collections import defaultdict
from typing import Any

from realm_sync_api.hooks import RealmSyncHook

RealmSyncApiHook = Any  # Protocol type for hook functions


HOOKS: dict[RealmSyncHook, list[RealmSyncApiHook]] = defaultdict(list)


def get_hooks() -> dict[RealmSyncHook, list[RealmSyncApiHook]]:
    return HOOKS


def add_hook(hook: RealmSyncHook, func: RealmSyncApiHook) -> None:
    """Add a hook function to the hooks dictionary."""
    HOOKS[hook].append(func)
