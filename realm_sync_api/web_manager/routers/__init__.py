from .item import router as item_router
from .logs import router as logs_router
from .map import router as map_router
from .npc import router as npc_router
from .players import router as players_router
from .quests import router as quests_router

__all__ = [
    "item_router",
    "logs_router",
    "map_router",
    "npc_router",
    "players_router",
    "quests_router",
]
