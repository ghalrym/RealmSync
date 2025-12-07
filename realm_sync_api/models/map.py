from pydantic import BaseModel


class Map(BaseModel):
    id: str
    name: str
