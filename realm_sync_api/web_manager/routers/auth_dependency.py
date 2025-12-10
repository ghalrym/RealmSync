"""Authentication helper for web manager sub-routers."""

from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

from ...dependencies.auth import RealmSyncAuth
from .template import templates


async def check_auth(request: Request) -> RedirectResponse | None:
    """
    Check if user is authenticated for web manager routes.
    Returns RedirectResponse if not authenticated, None if authenticated.
    """
    # Get auth from template globals (set by WebManagerRouter)
    auth: RealmSyncAuth | None = templates.env.globals.get("web_auth")
    web_prefix: str = templates.env.globals.get("web_prefix", "/web")

    if not auth:
        # If no auth is configured, allow access
        return None

    try:
        await auth.validate_session(request)
        return None
    except HTTPException:
        # Redirect to login if not authenticated
        return RedirectResponse(url=f"{web_prefix}/login", status_code=status.HTTP_303_SEE_OTHER)
