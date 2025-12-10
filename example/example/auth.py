"""Custom authentication class extending RealmSyncAuth."""

from fastapi import Request

from realm_sync_api.dependencies.auth import RealmSyncAuth


class Auth(RealmSyncAuth):
    """Custom authentication class with session validation."""

    async def validate_session(self, request: Request) -> bool:
        """
        Validate the session for the given request.

        This method extends the base RealmSyncAuth.validate_session() method.
        You can add custom validation logic here before or after calling the parent method.

        Args:
            request: The FastAPI request object

        Returns:
            True if the session is valid

        Raises:
            HTTPException: If the session is invalid
        """
        # Call parent validation first
        result = await super().validate_session(request)

        # Add custom validation logic here if needed
        # Example:
        # payload = self._decode_token(self._get_token_from_request(request))
        # user_id = payload.get("sub")
        # # Add custom checks here

        return result

