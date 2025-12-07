from realm_sync_api.models._base import RealmSyncModel


class Location(RealmSyncModel):
    location: str
    x: float
    y: float
    z: float
