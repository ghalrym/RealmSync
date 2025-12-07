from pydantic import BaseModel


class NPC(BaseModel):
    id: str
    name: str
    faction: str
    quests: list[str]
