from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

ModelType = TypeVar("Model", bound=BaseModel)
ListRequestArgs = TypeVar("ListRequestArgs", bound=BaseModel)


class RealmSyncRetriever(ABC, Generic[ModelType, ListRequestArgs]):
    def __init__(self, resource_name: str):
        self.resource_name = resource_name

    @abstractmethod
    def get(self, id: str) -> ModelType:
        pass

    @abstractmethod
    def list(self, body: ListRequestArgs) -> list[ModelType]:
        pass

    @abstractmethod
    def create(self, data: ModelType) -> ModelType:
        pass

    @abstractmethod
    def update(self, id: str, data: ModelType) -> ModelType:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass
