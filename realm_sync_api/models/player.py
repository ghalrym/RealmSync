from realm_sync_api.models._base import RealmSyncModel
from realm_sync_api.models.location import Location


class Player(RealmSyncModel):
    id: str
    name: str
    server: str
    location: Location
    faction: str
