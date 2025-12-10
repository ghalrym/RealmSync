from typing import Any

from pydantic import BaseModel, Field


class RealmSyncModel(BaseModel):
    id: str | None = None
    soft_deleted: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
