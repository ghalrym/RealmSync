"""Main application entry point."""

from example.auth import Auth
from example.postgres import Postgres
from example.redis import Redis
from realm_sync_api import RealmSyncApi
from realm_sync_api.dependencies.web_manager import WebManager

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
