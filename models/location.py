from pydantic import BaseModel


class Location(BaseModel):
    location: str
    x: float
    y: float
    z: float
