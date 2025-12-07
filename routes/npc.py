from pydantic import BaseModel

from models import NPC
from realm_sync_retriever import RealmSyncRetriever
from realm_sync_router import RealmSyncRouter
from setup.redis import get_redis_client


class ListRequestArgs(BaseModel): ...


class NPCRetriever(RealmSyncRetriever[NPC, ListRequestArgs]):
    def __init__(self):
        super().__init__("npc")

    def _get_key(self, id: str) -> str:
        return f"npc:{id}"

    def get(self, id: str) -> NPC:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = redis_client.get(key)
        if data is None:
            raise ValueError(f"NPC with id '{id}' not found")
        return NPC.model_validate_json(data)

    def list(self, body: ListRequestArgs) -> list[NPC]:
        redis_client = get_redis_client()
        npcs = []
        # Scan for all keys matching the npc pattern
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="npc:*", count=100)
            for key in keys:
                data = redis_client.get(key)
                if data:
                    npcs.append(NPC.model_validate_json(data))
            if cursor == 0:
                break
        return npcs

    def create(self, data: NPC) -> NPC:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if npc already exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) > 0:
            raise ValueError(f"NPC with id '{data.id}' already exists")
        # Store npc as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        return data

    def update(self, id: str, data: NPC) -> NPC:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if npc exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"NPC with id '{id}' not found")
        # Update npc data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"NPC id mismatch: expected '{id}', got '{data.id}'")
        # Store updated npc as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        return data

    def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if npc exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"NPC with id '{id}' not found")
        redis_client.delete(key)


router = RealmSyncRouter(prefix="/npc", tags=["npc"])
router.register_retriever(NPCRetriever())

__all__ = ["router"]
