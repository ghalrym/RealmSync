from realm_sync_api.models._base import RealmSyncModel


class Item(RealmSyncModel):
    id: str
    name: str
    type: str
