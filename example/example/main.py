"""Main application entry point."""

from realm_sync_api import RealmSyncApi
from example.auth import Auth
from realm_sync_api.dependencies.web_manager import WebManager
from example.redis import Redis
from example.postgres import Postgres

auth = Auth()

redis_client = Redis()

postgres_client = Postgres()

app = RealmSyncApi(
    auth=auth,
    web_manager=WebManager(
        prefix="/admin",
        auth=auth,
    ),
    redis_client=redis_client,
    postgres_client=postgres_client,
)