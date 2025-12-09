from fastapi import Request


class RealmSyncAuth:
    """Interface for authentication dependency."""

    async def validate_session(self, request: Request) -> bool:
        """
        Validate the session for the given request.

        Args:
            request: The FastAPI request object

        Raises:
            HTTPException: If the session is invalid
        """
        return True
