import os

from realm_sync_api import RealmSyncApi, RealmSyncHook, RealmSyncRedis
from realm_sync_api.dependencies.web_manager import WebManager
from realm_sync_api.models import Player

app = RealmSyncApi(
    web_manager=WebManager(prefix="/admin"),
    redis_client=RealmSyncRedis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
    ),
)


@app.hook(RealmSyncHook.PLAYER_CREATED)
def player_created(player: Player):
    print(f"Player created: {player.name}")
