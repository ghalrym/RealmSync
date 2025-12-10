from ._base import RealmSyncModel
from .location import Location


class Player(RealmSyncModel):
    id: str
    name: str
    server: str
    location: Location
    faction: str
