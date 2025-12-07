from enum import Enum

class RealmSyncHook(Enum):
    PLAYER_CREATED = "player_created"
    PLAYER_UPDATED = "player_updated"
    PLAYER_DELETED = "player_deleted"