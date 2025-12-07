from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from realm_sync_api.web_manager.routers import (
    item_router,
    logs_router,
    map_router,
    npc_router,
    players_router,
    quests_router,
)
from realm_sync_api.web_manager.routers.tempate import templates

router = APIRouter(prefix="/web", tags=["web_manager"])

# Get the base directory


class WebManagerRouter(APIRouter):
    def __init__(self, *args: Any, **kwargs: Any):
        # Get prefix before calling super() so we can use it
        prefix = kwargs.get("prefix", "/web")
        # Exclude from Swagger UI
        kwargs.setdefault("include_in_schema", False)
        super().__init__(*args, **kwargs)

        # Store the prefix for use in templates (use the actual prefix from the router)
        self.prefix = self.prefix if hasattr(self, "prefix") and self.prefix else prefix

        # Set up template context processor to make prefix available globally
        templates.env.globals["web_prefix"] = self.prefix

        # Set routes using add_api_route (excluded from Swagger UI)
        self.add_api_route(
            "/static/{filename}",
            self.serve_static,
            methods=["GET"],
            response_class=FileResponse,
            name="serve_static",
            include_in_schema=False,
        )
        self.add_api_route(
            "/",
            self.dashboard,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        # Include sub-routers (they will inherit exclude from parent)
        self.include_router(players_router, include_in_schema=False)
        self.include_router(quests_router, include_in_schema=False)
        self.include_router(map_router, include_in_schema=False)
        self.include_router(npc_router, include_in_schema=False)
        self.include_router(item_router, include_in_schema=False)
        self.include_router(logs_router, include_in_schema=False)

    async def serve_static(self, filename: str):
        """Serve static files."""
        # __file__ is web_manager/web_manager_router.py
        # parent is web_manager/
        base_dir = Path(__file__).parent
        file_path = base_dir / "static" / filename
        file_path = file_path.resolve()
        # Security check: ensure the file is within the static directory
        static_dir = (base_dir / "static").resolve()
        if not str(file_path).startswith(str(static_dir)):
            raise HTTPException(status_code=403, detail="Access denied")
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {filename} at {file_path}",
            )
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail=f"Not a file: {filename}")
        return FileResponse(file_path)

    async def dashboard(self, request: Request):
        """Dashboard showing all available models."""
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "models": ["player", "quest", "map", "npc", "item"]},
        )
