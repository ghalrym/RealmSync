from pydantic import BaseModel

from realm_sync_api.dependencies.redis import get_redis_client
from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.models import Player
from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
from realm_sync_api.realm_sync_router import RealmSyncRouter


class ListRequestArgs(BaseModel): ...


class PlayerRetriever(RealmSyncRetriever[Player, ListRequestArgs]):
    def __init__(self):
        super().__init__("player")

    def _get_key(self, id: str) -> str:
        return f"player:{id}"

    def get(self, id: str) -> Player:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = redis_client.get(key)
        if data is None:
            raise ValueError(f"Player with id '{id}' not found")
        return Player.model_validate_json(data)

    def list(self, body: ListRequestArgs) -> list[Player]:
        redis_client = get_redis_client()
        players = []
        # Scan for all keys matching the player pattern
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="player:*", count=100)
            for key in keys:
                data = redis_client.get(key)
                if data:
                    players.append(Player.model_validate_json(data))
            if cursor == 0:
                break
        return players

    def create(self, data: Player) -> Player:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if player already exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) > 0:
            raise ValueError(f"Player with id '{data.id}' already exists")
        # Store player as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        # Call player_created hook
        self.call_hooks(RealmSyncHook.PLAYER_CREATED, data)
        return data

    def update(self, id: str, data: Player) -> Player:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if player exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"Player with id '{id}' not found")
        # Update player data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"Player id mismatch: expected '{id}', got '{data.id}'")
        # Store updated player as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        # Call player_updated hook
        self.call_hooks(RealmSyncHook.PLAYER_UPDATED, data)
        return data

    def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if player exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"Player with id '{id}' not found")
        # Get player data before deletion for hook
        player_data = self.get(id)
        redis_client.delete(key)
        # Call player_deleted hook
        self.call_hooks(RealmSyncHook.PLAYER_DELETED, player_data)


router = RealmSyncRouter(prefix="/player", tags=["player"])
router.register_retriever(PlayerRetriever())

__all__ = ["router"]
