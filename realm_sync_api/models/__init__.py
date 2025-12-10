from .item import Item
from .location import Location
from .map import Map
from .npc import NPC
from .player import Player
from .quest import Quest
from .token import Token
from .user import User

__all__ = [
    "Item",
    "Location",
    "Map",
    "NPC",
    "Player",
    "Quest",
    "Token",
    "User",
    "register_all_models",
]

# All models that should be registered
_ALL_MODELS = [
    Item,
    Location,
    Map,
    NPC,
    Player,
    Quest,
    Token,
    User,
]


async def register_all_models(database) -> None:
    """
    Register all RealmSync models with the database.

    Args:
        database: RealmSyncDatabase instance to register models with
    """
    for model in _ALL_MODELS:
        await database.register_model(model)
