from pydantic import BaseModel

from realm_sync_api.dependencies.redis import get_redis_client
from realm_sync_api.models import Map
from realm_sync_api.realm_sync_retriever import RealmSyncRetriever
from realm_sync_api.realm_sync_router import RealmSyncRouter


class ListRequestArgs(BaseModel):
    pass


class MapRetriever(RealmSyncRetriever[Map, ListRequestArgs]):
    def __init__(self):
        super().__init__("map")

    def _get_key(self, id: str) -> str:
        return f"map:{id}"

    async def get(self, id: str) -> Map:
        redis_client = get_redis_client()
        key = self._get_key(id)
        data = await redis_client.get(key)
        if data is None:
            raise ValueError(f"Map with id '{id}' not found")
        return Map.model_validate_json(data)

    async def list(self, body: ListRequestArgs = ListRequestArgs()) -> list[Map]:
        redis_client = get_redis_client()
        maps = []
        # Scan for all keys matching the map pattern
        cursor = 0
        while True:
            cursor, keys = await redis_client.scan(cursor, match="map:*", count=100)
            for key in keys:
                data = await redis_client.get(key)
                if data:
                    maps.append(Map.model_validate_json(data))
            if cursor == 0:
                break
        return maps

    async def create(self, data: Map) -> Map:
        redis_client = get_redis_client()
        key = self._get_key(data.id)
        # Check if map already exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) > 0:
            raise ValueError(f"Map with id '{data.id}' already exists")
        # Store map as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def update(self, id: str, data: Map) -> Map:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if map exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Map with id '{id}' not found")
        # Update map data, ensuring the ID matches
        if data.id != id:
            raise ValueError(f"Map id mismatch: expected '{id}', got '{data.id}'")
        # Store updated map as JSON
        json_data = data.model_dump_json()
        await redis_client.set(key, json_data)
        return data

    async def delete(self, id: str) -> None:
        redis_client = get_redis_client()
        key = self._get_key(id)
        # Check if map exists (exists returns 0 or 1, not boolean)
        if await redis_client.exists(key) == 0:
            raise ValueError(f"Map with id '{id}' not found")
        await redis_client.delete(key)


router = RealmSyncRouter(prefix="/map", tags=["map"])
router.register_retriever(MapRetriever())

__all__ = ["router"]
