from realm_sync_api.models._base import RealmSyncModel


class NPC(RealmSyncModel):
    id: str
    name: str
    faction: str
    quests: list[str]
