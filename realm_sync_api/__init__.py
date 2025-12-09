"""RealmSync API - A FastAPI-based API framework for managing game data."""

from realm_sync_api import models
from realm_sync_api.dependencies.auth import RealmSyncAuth
from realm_sync_api.dependencies.hooks import RealmSyncHook
from realm_sync_api.dependencies.postgres import RealmSyncPostgres
from realm_sync_api.dependencies.redis import RealmSyncRedis
from realm_sync_api.dependencies.web_manager import WebManager
from realm_sync_api.realm_sync_api import RealmSyncApi

__all__ = [
    "RealmSyncApi",
    "RealmSyncHook",
    "models",
    "RealmSyncAuth",
    "RealmSyncRedis",
    "RealmSyncPostgres",
    "WebManager",
]
__version__ = "0.1.1"
