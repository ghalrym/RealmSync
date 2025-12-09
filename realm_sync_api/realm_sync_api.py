from collections.abc import Callable
from typing import Any, Protocol

import fastapi_swagger_dark as fsd
from fastapi import APIRouter, FastAPI

from realm_sync_api.dependencies.hooks import RealmSyncHook, add_hook, get_hooks
from realm_sync_api.dependencies.postgres import RealmSyncPostgres, set_postgres_client
from realm_sync_api.dependencies.redis import RealmSyncRedis, set_redis_client
from realm_sync_api.dependencies.web_manager import WebManager
from realm_sync_api.routes import router


class RealmSyncApiHook(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> None: ...


class RealmSyncApi(FastAPI):
    def __init__(
        self,
        web_manager: WebManager | None = None,
        title: str = "RealmSync API",
        redis_client: RealmSyncRedis | None = None,
        postgres_client: RealmSyncPostgres | None = None,
        **kwargs: Any,
    ) -> None:
        # Disable default docs to use dark mode version
        kwargs.setdefault("docs_url", None)

        super().__init__(
            title=title,
            **kwargs,
        )

        self.include_router(router)
        if web_manager:
            self.include_router(web_manager.create_router())

        # Install dark mode Swagger UI
        self._add_dark_mode_to_swagger()

        # Set clients if provided
        if redis_client is not None:
            set_redis_client(redis_client)
        if postgres_client is not None:
            set_postgres_client(postgres_client)

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
            add_hook(hook, func)
            return func

        return decorator

    def call_hooks(self, hook: RealmSyncHook, *args: Any, **kwargs: Any) -> None:
        hooks = get_hooks()
        for func in hooks[hook]:
            func(*args, **kwargs)

    def get(  # type: ignore[override]
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
        return super().get(path, **kwargs)

    def post(  # type: ignore[override]
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
        return super().post(path, **kwargs)

    def put(  # type: ignore[override]
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
        return super().put(path, **kwargs)

    def delete(  # type: ignore[override]
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
        return super().delete(path, **kwargs)
