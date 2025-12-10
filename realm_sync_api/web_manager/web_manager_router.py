from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..dependencies.auth import RealmSyncAuth
from .routers import item_router, logs_router, map_router, npc_router, players_router, quests_router
from .routers.template import templates

router = APIRouter(prefix="/web", tags=["web_manager"])

# Get the base directory


class WebManagerAuthMiddleware(BaseHTTPMiddleware):
    """Middleware to protect web manager routes with authentication."""

    def __init__(self, app: Any, auth: RealmSyncAuth | None, prefix: str) -> None:
        super().__init__(app)
        self.auth = auth
        self.prefix = prefix

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip auth for public routes
        path = request.url.path
        public_paths = [
            f"{self.prefix}/login",
            f"{self.prefix}/signup",
            f"{self.prefix}/static/",
        ]

        is_public = any(path.startswith(public_path) for public_path in public_paths)

        if not is_public and self.auth:
            try:
                is_valid = await self.auth.validate_session(request)
                if not is_valid:
                    # Redirect to login if session validation returns False
                    return RedirectResponse(
                        url=f"{self.prefix}/login", status_code=status.HTTP_303_SEE_OTHER
                    )
            except HTTPException:
                # Redirect to login if not authenticated
                return RedirectResponse(
                    url=f"{self.prefix}/login", status_code=status.HTTP_303_SEE_OTHER
                )

        return await call_next(request)


class WebManagerRouter(APIRouter):
    def __init__(
        self,
        *args: Any,
        prefix: str = "/web",
        auth: RealmSyncAuth | None = None,
        https_enabled: bool = False,
        **kwargs: Any,
    ):
        # Get prefix and auth before calling super() so we can use them
        self.auth: RealmSyncAuth | None = auth
        self.https_enabled = https_enabled

        super().__init__(
            *args,
            **kwargs,
            prefix=prefix,
            include_in_schema=False,
        )

        # Store the prefix for use in templates (use the actual prefix from the router)
        self.prefix = self.prefix if hasattr(self, "prefix") and self.prefix else prefix

        # Set up template context processor to make prefix available globally
        templates.env.globals["web_prefix"] = self.prefix
        # Store auth in template globals so API helpers can access it
        templates.env.globals["web_auth"] = self.auth

        # Set routes using add_api_route (excluded from Swagger UI)
        self.add_api_route(
            "/static/{filename}",
            self.serve_static,
            methods=["GET"],
            response_class=FileResponse,
            name="serve_static",
            include_in_schema=False,
        )

        # Auth routes (public)
        self.add_api_route(
            "/login",
            self.login_page,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        self.add_api_route(
            "/login",
            self.login_post,
            methods=["POST"],
            response_class=RedirectResponse,
            include_in_schema=False,
        )
        self.add_api_route(
            "/signup",
            self.signup_page,
            methods=["GET"],
            response_class=HTMLResponse,
            include_in_schema=False,
        )
        self.add_api_route(
            "/signup",
            self.signup_post,
            methods=["POST"],
            response_class=RedirectResponse,
            include_in_schema=False,
        )
        self.add_api_route(
            "/logout",
            self.logout,
            methods=["POST"],
            response_class=RedirectResponse,
            include_in_schema=False,
        )

        # Protected routes
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

    async def _check_auth(self, request: Request) -> RedirectResponse | None:
        """Check if user is authenticated, return RedirectResponse if not."""
        if not self.auth:
            # If no auth is configured, allow access
            return None
        try:
            await self.auth.validate_session(request)
            return None
        except HTTPException:
            # Redirect to login if not authenticated
            return RedirectResponse(
                url=f"{self.prefix}/login", status_code=status.HTTP_303_SEE_OTHER
            )

    async def login_page(self, request: Request):
        """Show login page."""
        # If already authenticated, redirect to dashboard
        if self.auth:
            try:
                await self.auth.validate_session(request)
                return RedirectResponse(
                    url=f"{self.prefix}/", status_code=status.HTTP_303_SEE_OTHER
                )
            except HTTPException:
                pass
        return templates.TemplateResponse("login.html", {"request": request})

    async def login_post(
        self,
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
    ):
        """Handle login form submission."""
        if not self.auth:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured",
            )

        try:
            token = await self.auth.login(username, password)
            response = RedirectResponse(
                url=f"{self.prefix}/", status_code=status.HTTP_303_SEE_OTHER
            )
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=self.https_enabled,
                samesite="lax",
                max_age=60 * self.auth.access_token_expire_minutes,
            )
            return response
        except HTTPException as e:
            # Return to login page with error
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": e.detail},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

    async def signup_page(self, request: Request):
        """Show signup page."""
        # If already authenticated, redirect to dashboard
        if self.auth:
            try:
                await self.auth.validate_session(request)
                return RedirectResponse(
                    url=f"{self.prefix}/", status_code=status.HTTP_303_SEE_OTHER
                )
            except HTTPException:
                pass
        return templates.TemplateResponse("signup.html", {"request": request})

    async def signup_post(
        self,
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
    ):
        """Handle signup form submission."""
        if not self.auth:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured",
            )

        try:
            user_data = await self.auth.signup(username, email, password)
            # Auto-login after signup
            token = await self.auth.create_token(user_data["user_id"])
            response = RedirectResponse(
                url=f"{self.prefix}/", status_code=status.HTTP_303_SEE_OTHER
            )
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=self.https_enabled,
                samesite="lax",
                max_age=60 * self.auth.access_token_expire_minutes,
            )
            return response
        except HTTPException as e:
            # Return to signup page with error
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": e.detail},
                status_code=e.status_code,
            )

    async def logout(self, request: Request):
        """Handle logout."""
        response = RedirectResponse(
            url=f"{self.prefix}/login", status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie(key="access_token")

        # Revoke token if auth is configured
        if self.auth:
            token = self.auth._get_token_from_cookie(request)
            if token:
                try:
                    await self.auth.revoke_token(token)
                except Exception:
                    pass  # Ignore errors during logout

        return response

    async def dashboard(self, request: Request):
        """Dashboard showing all available models."""
        redirect = await self._check_auth(request)
        if redirect:
            return redirect
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "models": ["player", "quest", "map", "npc", "item"]},
        )
