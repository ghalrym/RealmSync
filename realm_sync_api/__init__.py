"""RealmSync API - A FastAPI-based API framework for managing game data."""

from . import models
from .dependencies.auth import RealmSyncAuth
from .dependencies.hooks import RealmSyncHook
from .dependencies.postgres import RealmSyncPostgres
from .dependencies.redis import RealmSyncRedis
from .dependencies.web_manager import WebManager
from .realm_sync_api import RealmSyncApi

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
