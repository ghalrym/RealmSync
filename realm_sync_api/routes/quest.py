from pydantic import BaseModel

from ..dependencies.redis import get_redis_client
from ..models import Quest
from ..realm_sync_retriever import RealmSyncRetriever
from ..realm_sync_router import RealmSyncRouter


class ListRequestArgs(BaseModel):
    pass


class QuestRetriever(RealmSyncRetriever[Quest, ListRequestArgs]):
    def __init__(self):
        super().__init__("quest")

    def _get_key(self, id: str) -> str:
        return f"quest:{id}"

    async def get(self, id: str) -> Quest:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = await redis_client.get(key)
        if data is None:
            raise ValueError(f"Quest with id '{id}' not found")
        return Quest.model_validate_json(data)

    async def list(self, body: ListRequestArgs = ListRequestArgs()) -> list[Quest]:
        redis_client = get_redis_client()
        quests = []
        # Scan for all keys matching the quest pattern
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="quest:*", count=100)
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    quests.append(Quest.model_validate_json(data))
            if cursor == 0:
                break
        return quests

    async def create(self, data: Quest) -> Quest:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if quest already exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) > 0:
            raise ValueError(f"Quest with id '{data.id}' already exists")
        # Store quest as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def update(self, id: str, data: Quest) -> Quest:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if quest exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Quest with id '{id}' not found")
        # Update quest data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"Quest id mismatch: expected '{id}', got '{data.id}'")
        # Store updated quest as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if quest exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Quest with id '{id}' not found")
        await redis_client.delete(key)


router = RealmSyncRouter(prefix="/quest", tags=["quest"])
router.register_retriever(QuestRetriever())

__all__ = ["router"]
