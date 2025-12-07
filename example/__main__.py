import os

from realm_sync_api import RealmSyncApi
from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.models import Player
from realm_sync_api.setup.redis import RealmSyncRedis

app = RealmSyncApi(web_manager_perfix="/admin")

# Get Redis connection details from environment variables, with defaults for local development
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", "6379"))
redis_db = int(os.getenv("REDIS_DB", "0"))

app.set_redis_client(RealmSyncRedis(host=redis_host, port=redis_port, db=redis_db))


@app.hook(RealmSyncHook.PLAYER_CREATED)
def player_created(player: Player):
    print(f"Player created: {player.name}")
