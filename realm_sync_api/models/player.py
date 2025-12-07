from pydantic import BaseModel

from realm_sync_api.models.location import Location


class Player(BaseModel):
    id: str
    name: str
    server: str
    location: Location
    faction: str
