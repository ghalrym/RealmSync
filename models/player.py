from pydantic import BaseModel

from models.location import Location


class Player(BaseModel):
    id: str
    name: str
    server: str
    location: Location
    faction: str
