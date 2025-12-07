from pydantic import BaseModel


class Quest(BaseModel):
    id: str
    name: str
    description: str
    dependencies: list[str]
