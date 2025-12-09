from datetime import datetime

from realm_sync_api.models._base import RealmSyncModel


class User(RealmSyncModel):
    id: str
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None
