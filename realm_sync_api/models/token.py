from datetime import datetime

from ._base import RealmSyncModel


class Token(RealmSyncModel):
    id: str  # The token string itself
    user_id: str
    expires_at: datetime
