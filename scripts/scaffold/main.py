"""Main application entry point."""

import os

from realm_sync_api import RealmSyncApi, RealmSyncDatabase, RealmSyncRedis
from realm_sync_api.dependencies.auth import RealmSyncAuth
from realm_sync_api.dependencies.web_manager import WebManager

auth = RealmSyncAuth()

app = RealmSyncApi(
    auth=auth,
    web_manager=WebManager(
        prefix="/admin",
        auth=auth,
    ),
    redis_client=RealmSyncRedis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
    ),
    postgres_client=RealmSyncDatabase(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "realm_sync"),
        password=os.getenv("POSTGRES_PASSWORD", "realm_sync_password"),
        database=os.getenv("POSTGRES_DB", "realm_sync_db"),
    ),
)
