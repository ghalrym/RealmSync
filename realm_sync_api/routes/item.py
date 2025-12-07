from pydantic import BaseModel

from realm_sync_api.models import Item
from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
from realm_sync_api.realm_sync_router import RealmSyncRouter
from realm_sync_api.setup.redis import get_redis_client


class ListRequestArgs(BaseModel): ...


class ItemRetriever(RealmSyncRetriever[Item, ListRequestArgs]):
    def __init__(self):
        super().__init__("item")

    def _get_key(self, id: str) -> str:
        return f"item:{id}"

    def get(self, id: str) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = redis_client.get(key)
        if data is None:
            raise ValueError(f"Item with id '{id}' not found")
        return Item.model_validate_json(data)

    def list(self, body: ListRequestArgs) -> list[Item]:
        redis_client = get_redis_client()
        items = []
        # Scan for all keys matching the item pattern
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="item:*", count=100)
            for key in keys:
                data = redis_client.get(key)
                if data:
                    items.append(Item.model_validate_json(data))
            if cursor == 0:
                break
        return items

    def create(self, data: Item) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if item already exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) > 0:
            raise ValueError(f"Item with id '{data.id}' already exists")
        # Store item as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        return data

    def update(self, id: str, data: Item) -> Item:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if item exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"Item with id '{id}' not found")
        # Update item data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"Item id mismatch: expected '{id}', got '{data.id}'")
        # Store updated item as JSON
        json_data = data.model_dump_json()
        redis_client.set(key, json_data)
        return data

    def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if item exists (exists returns 0 or 1, not boolean)
        if redis_client.exists(key) == 0:
            raise ValueError(f"Item with id '{id}' not found")
        redis_client.delete(key)


router = RealmSyncRouter(prefix="/item", tags=["item"])
router.register_retriever(ItemRetriever())

__all__ = ["router"]
