from ._base import RealmSyncModel


class Quest(RealmSyncModel):
    id: str
    name: str
    description: str
    dependencies: list[str]
