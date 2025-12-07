from collections import defaultdict
from collections.abc import Callable
from typing import Any, Protocol

import fastapi_swagger_dark as fsd
from fastapi import APIRouter, FastAPI

from hooks import RealmSyncHook
from routes import router
from setup.postgres import RealmSyncPostgres, set_postgres_client
from setup.redis import RealmSyncRedis, set_redis_client
from web_manager.web_manager_router import WebManagerRouter


class RealmSyncApiHook(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> None: ...


class RealmSyncApi(FastAPI):
    def __init__(
        self,
        web_manager_perfix: str | None = None,
        title: str = "RealmSync API",
        **kwargs: Any,
    ) -> None:
        # Disable default docs to use dark mode version
        kwargs.setdefault("docs_url", None)

        super().__init__(
            title=title,
            **kwargs,
        )

        self.hooks: dict[RealmSyncHook, list[RealmSyncApiHook]] = defaultdict(list)

        self.include_router(router)
        if web_manager_perfix:
            self.include_router(WebManagerRouter(prefix=web_manager_perfix))

        # Install dark mode Swagger UI
        self._add_dark_mode_to_swagger()

    def _add_dark_mode_to_swagger(self) -> None:
        """Install dark mode Swagger UI using fastapi-swagger-dark."""
        # Create a router for the dark Swagger UI
        swagger_router = APIRouter()
        fsd.install(swagger_router)
        self.include_router(swagger_router)

    def hook(
        self,
        hook: RealmSyncHook,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Decorator to register a hook function.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.hooks[hook].append(func)
            return func

        return decorator

    def set_redis_client(self, redis_client: RealmSyncRedis) -> None:
        set_redis_client(redis_client)

    def set_postgres_client(self, postgres_client: RealmSyncPostgres) -> None:
        set_postgres_client(postgres_client)

    def call_hooks(self, hook: RealmSyncHook, *args: Any, **kwargs: Any) -> None:
        for func in self.hooks[hook]:
            func(*args, **kwargs)

    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a GET endpoint. Works as a decorator like FastAPI's get method.

        Usage:
            @api.get("/items/{item_id}")
            async def get_item(item_id: str):
                return {"item_id": item_id}
        """
        return super().get(path, self.call_hooks, **kwargs)

    def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a POST endpoint. Works as a decorator like FastAPI's post method.

        Usage:
            @api.post("/items")
            async def create_item(item: Item):
                return item
        """
        return super().post(path, self.call_hooks, **kwargs)

    def put(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a PUT endpoint. Works as a decorator like FastAPI's put method.

        Usage:
            @api.put("/items/{item_id}")
            async def update_item(item_id: str, item: Item):
                return item
        """
        return super().put(path, self.call_hooks, **kwargs)

    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """
        Register a DELETE endpoint. Works as a decorator like FastAPI's delete method.

        Usage:
            @api.delete("/items/{item_id}")
            async def delete_item(item_id: str):
                return {"message": "Item deleted"}
        """
        return super().delete(path, self.call_hooks, **kwargs)
