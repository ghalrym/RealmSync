from typing import Any

from realm_sync_api.web_manager.web_manager_router import WebManagerRouter


class WebManager:
    def __init__(self, prefix: str = "/web", **kwargs: Any) -> None:
        self.prefix = prefix
        self.kwargs = kwargs

    def create_router(self) -> WebManagerRouter:
        """Create and return a WebManagerRouter instance."""
        return WebManagerRouter(prefix=self.prefix, **self.kwargs)
