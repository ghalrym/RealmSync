from collections import defaultdict
from collections.abc import Callable
from enum import Enum


class RealmSyncHook(Enum):
    PLAYER_CREATED = "player_created"
    PLAYER_UPDATED = "player_updated"
    PLAYER_DELETED = "player_deleted"


RealmSyncApiHook = Callable[..., None]
HOOKS: dict[RealmSyncHook, list[RealmSyncApiHook]] = defaultdict(list)


def get_hooks() -> dict[RealmSyncHook, list[RealmSyncApiHook]]:
    return HOOKS


def add_hook(hook: RealmSyncHook, func: RealmSyncApiHook) -> None:
    """Add a hook function to the hooks dictionary."""
    HOOKS[hook].append(func)
