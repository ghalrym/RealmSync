from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

from realm_sync_api.hooks import RealmSyncHook
from realm_sync_api.setup.hooks import get_hooks

ModelType = TypeVar("Model", bound=BaseModel)
ListRequestArgs = TypeVar("ListRequestArgs", bound=BaseModel)


class RealmSyncRetriever(ABC, Generic[ModelType, ListRequestArgs]):
    def __init__(self, resource_name: str):
        self.resource_name = resource_name

    def call_hooks(self, hook: RealmSyncHook, *args, **kwargs) -> None:
        """Call all registered hooks for the given hook type."""
        hooks = get_hooks()
        for func in hooks[hook]:
            func(*args, **kwargs)

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
