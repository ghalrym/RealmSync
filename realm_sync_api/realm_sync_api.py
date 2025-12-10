import logging
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

import fastapi_swagger_dark as fsd
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi_csrf_jinja.jinja_processor import csrf_token_processor
from fastapi_csrf_jinja.middleware import FastAPICSRFJinjaMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .dependencies.auth import RealmSyncAuth
from .dependencies.database import RealmSyncDatabase, set_postgres_client
from .dependencies.hooks import RealmSyncHook, add_hook, get_hooks
from .dependencies.redis import RealmSyncRedis, set_redis_client
from .dependencies.web_manager import WebManager
from .models import register_all_models
from .routes import router
from .web_manager.routers.template import templates

logger = logging.getLogger(__name__)


class RealmSyncApiHook(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> None: ...


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware to validate sessions before API requests."""

    def __init__(
        self, app: FastAPI, auth: RealmSyncAuth, web_manager_prefix: str | None = None
    ) -> None:
        super().__init__(app)
        self.auth = auth
        self.web_manager_prefix = web_manager_prefix

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip auth for docs, openapi, and web manager routes
        path = request.url.path.lower()
        skip_auth = (
            path.startswith("/docs")
            or path.startswith("/openapi.json")
            or path.startswith("/redoc")
            or path.startswith("/dark_theme.css")
            or path.startswith("/static/")
            or (self.web_manager_prefix and path.startswith(self.web_manager_prefix.lower()))
        )
        if not skip_auth:
            try:
                valid = await self.auth.validate_session(request)
                if not valid:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
            except Exception:
                logger.exception("Unexpected error during session validation")
                return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
        return await call_next(request)


class RealmSyncApi(FastAPI):
    def __init__(
        self,
        web_manager: WebManager | None = None,
        auth: RealmSyncAuth | None = None,
        title: str = "RealmSync API",
        redis_client: RealmSyncRedis | None = None,
        postgres_client: RealmSyncDatabase | None = None,
        **kwargs: Any,
    ) -> None:
        # Disable default docs to use dark mode version
        kwargs.setdefault("docs_url", None)

        super().__init__(
            title=title,
            **kwargs,
        )

        self.include_router(router)
        web_manager_prefix = None
        if web_manager:
            web_manager_prefix = web_manager.prefix
            self.include_router(web_manager.create_router())
            # Add CSRF middleware - this automatically injects csrf_token into template context
            self.add_middleware(
                FastAPICSRFJinjaMiddleware,
                secret=web_manager.get_csrf_secret(),
                cookie_name="csrftoken",
                header_name="x-csrftoken",
                cookie_secure=web_manager.https_enabled,
            )
            # Add CSRF token processor to templates as a context processor
            # This makes csrf_token available in all template contexts
            processor = csrf_token_processor("csrftoken", "x-csrftoken")
            templates.env.globals["csrf_token"] = processor

        # Add auth middleware only if auth is explicitly provided
        # Skip web manager routes as they handle their own authentication
        if auth is not None:
            self.add_middleware(AuthMiddleware, auth=auth, web_manager_prefix=web_manager_prefix)  # type: ignore[arg-type]

        # Install dark mode Swagger UI
        self._add_dark_mode_to_swagger()

        # Set clients if provided
        if redis_client is not None:
            set_redis_client(redis_client)
        if postgres_client is not None:
            set_postgres_client(postgres_client)

            # Register all models with the database on startup
            @self.on_event("startup")
            async def register_models() -> None:
                await register_all_models(postgres_client)

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
