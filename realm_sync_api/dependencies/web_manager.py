from typing import Any

from ..web_manager.web_manager_router import WebManagerRouter
from .auth import RealmSyncAuth


class WebManager:
    def __init__(
        self,
        prefix: str = "/web",
        auth: RealmSyncAuth | None = None,
        **kwargs: Any,
    ) -> None:
        self.prefix = prefix
        self.auth = auth
        self.kwargs = kwargs

    def create_router(self) -> WebManagerRouter:
        """Create and return a WebManagerRouter instance."""
        return WebManagerRouter(prefix=self.prefix, auth=self.auth, **self.kwargs)
