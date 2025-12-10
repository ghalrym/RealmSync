import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..models.token import Token
from ..models.user import User
from .database import get_postgres_client

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
# Default secret key - should be overridden in production
DEFAULT_SECRET_KEY = secrets.token_urlsafe(32)
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class RealmSyncAuth:
    """Token-based authentication using JWT tokens stored in PostgreSQL."""

    def __init__(
        self,
        secret_key: str | None = None,
        access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
    ):
        """
        Initialize the authentication system.

        Args:
            secret_key: Secret key for JWT encoding/decoding. If None, uses a default.
            access_token_expire_minutes: Token expiration time in minutes.
        """
        self.secret_key = secret_key or DEFAULT_SECRET_KEY
        self.access_token_expire_minutes = access_token_expire_minutes
        self.security = HTTPBearer()

    def _get_token_from_request(self, request: Request) -> str | None:
        """Extract JWT token from Authorization header."""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        # Check if it's a Bearer token
        if authorization.startswith("Bearer "):
            return authorization[7:]  # Remove "Bearer " prefix
        return None

    def _create_access_token(
        self, data: dict[str, Any], expires_delta: timedelta | None = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return cast(str, encoded_jwt)

    def _decode_token(self, token: str) -> dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            return cast(dict[str, Any], payload)
        except JWTError as e:
            logger.exception("JWT token validation failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    async def _get_token_from_db(self, token: str) -> dict[str, Any] | None:
        """Retrieve token data from PostgreSQL."""
        db = get_postgres_client()
        try:
            # Register Token model if not already registered
            await db.register_model(Token)
            # Get token from database
            tokens = await db.select(Token, filters={"id": token})
            if tokens:
                token_obj = tokens[0]
                return {"user_id": token_obj.user_id, "expires_at": token_obj.expires_at}
            return None
        except Exception:
            # If database operation fails, return None to allow JWT-only validation
            return None

    async def _store_token_in_db(self, token: str, user_id: str, expires_at: datetime) -> None:
        """Store token in PostgreSQL."""
        db = get_postgres_client()
        try:
            # Register Token model if not already registered
            await db.register_model(Token)
            # Use internal postgres client for upsert operation
            # This handles the ON CONFLICT case that models don't support yet
            await db.postgres.execute(
                "INSERT INTO tokens (id, user_id, expires_at) VALUES ($1, $2, $3) "
                "ON CONFLICT (id) DO UPDATE SET expires_at = $3, user_id = $2",
                token,
                user_id,
                expires_at,
            )
        except Exception:
            # If database operation fails, skip database storage
            logger.exception("Failed to store token in database during upsert operation")

    async def _revoke_token_in_db(self, token: str) -> None:
        """Revoke token in PostgreSQL."""
        db = get_postgres_client()
        try:
            # Register Token model if not already registered
            await db.register_model(Token)
            # Soft delete the token
            await db.soft_delete(Token, token)
        except Exception:
            # If database operation fails, skip database revocation
            logger.exception("Failed to revoke token in DB")

    async def validate_session(self, request: Request) -> bool:
        """
        Validate the session for the given request using JWT token.
        Checks Authorization header first, then cookie if header is not present.

        Args:
            request: The FastAPI request object

        Returns:
            True if the session is valid

        Raises:
            HTTPException: If the session is invalid
        """
        # Try to get token from Authorization header first, then from cookie
        token = self._get_token_from_request(request) or self._get_token_from_cookie(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Decode and validate JWT token
        payload = self._decode_token(token)

        # Check if token exists in database (if postgres client supports it)
        token_data = await self._get_token_from_db(token)
        if token_data is None:
            # If we can't check the database, rely on JWT validation only
            # This allows the auth to work even if postgres client doesn't support token storage
            pass
        else:
            # Verify token hasn't been revoked
            expires_at = token_data.get("expires_at")
            if expires_at:
                # Handle both datetime objects and strings from the database
                if isinstance(expires_at, datetime):
                    # Ensure timezone-aware datetime (convert to UTC if naive or different timezone)
                    if expires_at.tzinfo is None:
                        # Naive datetime - assume UTC
                        expires_at_dt = expires_at.replace(tzinfo=UTC)
                    else:
                        # Timezone-aware datetime - convert to UTC
                        expires_at_dt = expires_at.astimezone(UTC)
                elif isinstance(expires_at, str):
                    # Parse string to datetime using fromisoformat (Python 3.7+)
                    try:
                        expires_at_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        # Fallback: try parsing as-is, or use current time if parsing fails
                        logger.warning(f"Failed to parse expires_at: {expires_at}")
                        expires_at_dt = None
                    # Ensure timezone-aware (normalize to UTC)
                    if expires_at_dt and expires_at_dt.tzinfo is None:
                        expires_at_dt = expires_at_dt.replace(tzinfo=UTC)
                    elif expires_at_dt:
                        expires_at_dt = expires_at_dt.astimezone(UTC)
                else:
                    # Unexpected type - skip expiration check
                    logger.warning(f"Unexpected expires_at type: {type(expires_at)}")
                    expires_at_dt = None

                if expires_at_dt and expires_at_dt < datetime.now(UTC):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        # Store user info in request state for use in route handlers
        request.state.user_id = payload.get("sub")  # 'sub' is the standard JWT subject claim
        request.state.user_payload = payload

        return True

    async def create_token(
        self, user_id: str, additional_claims: dict[str, Any] | None = None
    ) -> str:
        """
        Create a JWT token for a user.

        Args:
            user_id: The user ID to encode in the token
            additional_claims: Additional claims to include in the token

        Returns:
            The encoded JWT token
        """
        data = {"sub": user_id}
        if additional_claims:
            data.update(additional_claims)

        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        token = self._create_access_token(data, expires_delta)

        # Store token in database
        expires_at = datetime.now(UTC) + expires_delta
        await self._store_token_in_db(token, user_id, expires_at)

        return token

    async def revoke_token(self, token: str) -> None:
        """
        Revoke a token by removing it from the database.

        Args:
            token: The token to revoke
        """
        await self._revoke_token_in_db(token)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return cast(bool, pwd_context.verify(plain_password, hashed_password))

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return cast(str, pwd_context.hash(password))

    async def get_current_user(self, request: Request) -> dict[str, Any]:
        """
        Get the current authenticated user from the request.

        Args:
            request: The FastAPI request object

        Returns:
            Dictionary containing user information from the token

        Raises:
            HTTPException: If the user is not authenticated
        """
        await self.validate_session(request)
        return {
            "user_id": request.state.user_id,
            "payload": request.state.user_payload,
        }

    def _get_token_from_cookie(self, request: Request) -> str | None:
        """Extract JWT token from cookie."""
        return request.cookies.get("access_token")

    async def signup(self, username: str, email: str, password: str) -> dict[str, Any]:
        """
        Create a new user account.

        Args:
            username: The username for the new account
            email: The email address for the new account
            password: The plain text password

        Returns:
            Dictionary containing user_id and username

        Raises:
            HTTPException: If the user already exists
        """
        db = get_postgres_client()
        try:
            # Register User model if not already registered
            await db.register_model(User)
            # Check if user already exists by username
            existing_by_username = await db.select(User, filters={"username": username})
            if existing_by_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists",
                )
            # Check if user already exists by email
            existing_by_email = await db.select(User, filters={"email": email})
            if existing_by_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username or email already exists",
                )

            # Generate user ID
            user_id = secrets.token_urlsafe(16)
            hashed_password = self.get_password_hash(password)
            created_at = datetime.now(UTC)

            # Create user
            user = User(
                id=user_id,
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                created_at=created_at,
            )
            await db.create(user)

            return {"user_id": user_id, "username": username, "email": email}
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error during user signup")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An internal error occurred while creating the user",
            ) from e

    async def login(self, username: str, password: str) -> str:
        """
        Authenticate a user and return a JWT token.

        Args:
            username: The username or email
            password: The plain text password

        Returns:
            JWT token string

        Raises:
            HTTPException: If authentication fails
        """
        db = get_postgres_client()
        try:
            # Register User model if not already registered
            await db.register_model(User)
            # Find user by username first
            users = await db.select(User, filters={"username": username})
            # If not found, try email
            if not users:
                users = await db.select(User, filters={"email": username})

            if not users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                )

            user = users[0]

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive",
                )

            # Verify password
            if not user.hashed_password or not self.verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                )

            # Create token
            token = await self.create_token(user.id)

            return token
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error during user login")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during authentication: {str(e)}",
            ) from e
