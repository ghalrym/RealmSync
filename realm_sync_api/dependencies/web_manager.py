import secrets
from typing import Any

from ..web_manager.web_manager_router import WebManagerRouter
from .auth import RealmSyncAuth


class WebManager:
    def __init__(
        self,
        prefix: str = "/web",
        auth: RealmSyncAuth | None = None,
        csrf_secret: str | None = None,
        https_enabled: bool = False,
        **kwargs: Any,
    ) -> None:
        self.prefix = prefix
        self.auth = auth
        self.csrf_secret = csrf_secret or secrets.token_urlsafe(32)
        self.https_enabled = https_enabled
        self.kwargs = kwargs

    def create_router(self) -> WebManagerRouter:
        """Create and return a WebManagerRouter instance."""
        return WebManagerRouter(
            prefix=self.prefix,
            auth=self.auth,
            https_enabled=self.https_enabled,
            **self.kwargs,
        )

    def get_csrf_secret(self) -> str:
        """Get the CSRF secret key."""
        return self.csrf_secret
