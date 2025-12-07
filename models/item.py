from pydantic import BaseModel


class Item(BaseModel):
    id: str
    name: str
    type: str
