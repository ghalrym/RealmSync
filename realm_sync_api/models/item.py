from ._base import RealmSyncModel


class Item(RealmSyncModel):
    id: str
    name: str
    type: str
