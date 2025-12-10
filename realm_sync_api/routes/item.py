from pydantic import BaseModel

from ..dependencies.redis import get_redis_client
from ..models import Item
from ..realm_sync_retriever import RealmSyncRetriever
from ..realm_sync_router import RealmSyncRouter


class ListRequestArgs(BaseModel):
    pass


class ItemRetriever(RealmSyncRetriever[Item, ListRequestArgs]):
    def __init__(self):
        super().__init__("item")

    def _get_key(self, id: str) -> str:
        return f"item:{id}"

    async def get(self, id: str) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = await redis_client.get(key)
        if data is None:
            raise ValueError(f"Item with id '{id}' not found")
        return Item.model_validate_json(data)

    async def list(self, body: ListRequestArgs = ListRequestArgs()) -> list[Item]:
        redis_client = get_redis_client()
        items = []
        # Scan for all keys matching the item pattern
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="item:*", count=100)
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    items.append(Item.model_validate_json(data))
            if cursor == 0:
                break
        return items

    async def create(self, data: Item) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if item already exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) > 0:
            raise ValueError(f"Item with id '{data.id}' already exists")
        # Store item as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def update(self, id: str, data: Item) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if item exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Item with id '{id}' not found")
        # Update item data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"Item id mismatch: expected '{id}', got '{data.id}'")
        # Store updated item as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if item exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Item with id '{id}' not found")
        await redis_client.delete(key)


router = RealmSyncRouter(prefix="/item", tags=["item"])
router.register_retriever(ItemRetriever())

__all__ = ["router"]
