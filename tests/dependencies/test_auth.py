"""Tests for RealmSyncAuth class."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from realm_sync_api.dependencies.auth import RealmSyncAuth
from realm_sync_api.dependencies.postgres import MockRealmSyncPostgres, set_postgres_client


def test_realm_sync_auth_init_with_defaults():
    """Test RealmSyncAuth initialization with default values."""
    auth = RealmSyncAuth()
    assert auth.secret_key is not None
    assert auth.access_token_expire_minutes == 30
    assert auth.security is not None


def test_realm_sync_auth_init_with_secret_key():
    """Test RealmSyncAuth initialization with custom secret key."""
    secret_key = "test-secret-key"
    auth = RealmSyncAuth(secret_key=secret_key)
    assert auth.secret_key == secret_key


def test_realm_sync_auth_init_with_custom_expire_minutes():
    """Test RealmSyncAuth initialization with custom expiration time."""
    auth = RealmSyncAuth(access_token_expire_minutes=60)
    assert auth.access_token_expire_minutes == 60


def test_get_token_from_request_with_bearer():
    """Test _get_token_from_request with Bearer token."""
    auth = RealmSyncAuth()
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer test-token"}

    token = auth._get_token_from_request(request)
    assert token == "test-token"


def test_get_token_from_request_without_bearer():
    """Test _get_token_from_request without Bearer prefix."""
    auth = RealmSyncAuth()
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "test-token"}

    token = auth._get_token_from_request(request)
    assert token is None


def test_get_token_from_request_without_authorization():
    """Test _get_token_from_request without Authorization header."""
    auth = RealmSyncAuth()
    request = MagicMock(spec=Request)
    request.headers = {}

    token = auth._get_token_from_request(request)
    assert token is None


def test_create_access_token_with_expires_delta():
    """Test _create_access_token with custom expires_delta."""
    auth = RealmSyncAuth(secret_key="test-secret")
    data = {"sub": "user123"}
    expires_delta = timedelta(minutes=60)

    token = auth._create_access_token(data, expires_delta)
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify
    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert payload["sub"] == "user123"
    assert "exp" in payload


def test_create_access_token_without_expires_delta():
    """Test _create_access_token without expires_delta."""
    auth = RealmSyncAuth(secret_key="test-secret", access_token_expire_minutes=45)
    data = {"sub": "user123"}

    token = auth._create_access_token(data, None)
    assert isinstance(token, str)

    # Decode and verify expiration
    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert payload["sub"] == "user123"
    assert "exp" in payload


def test_decode_token_success():
    """Test _decode_token with valid token."""
    auth = RealmSyncAuth(secret_key="test-secret")
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")

    payload = auth._decode_token(token)
    assert payload["sub"] == "user123"


def test_decode_token_invalid():
    """Test _decode_token with invalid token."""
    auth = RealmSyncAuth(secret_key="test-secret")

    with pytest.raises(HTTPException) as exc_info:
        auth._decode_token("invalid-token")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authentication credentials" in exc_info.value.detail


def test_decode_token_wrong_secret():
    """Test _decode_token with token signed with different secret."""
    auth = RealmSyncAuth(secret_key="test-secret")
    data = {"sub": "user123"}
    token = jwt.encode(data, "wrong-secret", algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        auth._decode_token(token)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_token_from_db_with_result():
    """Test _get_token_from_db when token exists in database."""
    auth = RealmSyncAuth()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": datetime.now(UTC)}
    )
    set_postgres_client(postgres_client)

    result = await auth._get_token_from_db("test-token")
    assert result is not None
    assert result["user_id"] == "user123"
    assert "expires_at" in result


@pytest.mark.asyncio
async def test_get_token_from_db_no_result():
    """Test _get_token_from_db when token doesn't exist."""
    auth = RealmSyncAuth()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(return_value=None)
    set_postgres_client(postgres_client)

    result = await auth._get_token_from_db("test-token")
    assert result is None


@pytest.mark.asyncio
async def test_get_token_from_db_attribute_error():
    """Test _get_token_from_db when postgres client doesn't have fetch_one."""
    auth = RealmSyncAuth()
    # Create a mock that doesn't have fetch_one
    postgres_client = MagicMock()
    del postgres_client.fetch_one
    set_postgres_client(postgres_client)

    result = await auth._get_token_from_db("test-token")
    assert result is None


@pytest.mark.asyncio
async def test_store_token_in_db():
    """Test _store_token_in_db."""
    auth = RealmSyncAuth()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.execute = AsyncMock()
    set_postgres_client(postgres_client)

    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    await auth._store_token_in_db("test-token", "user123", expires_at)

    postgres_client.execute.assert_called_once()


@pytest.mark.asyncio
async def test_store_token_in_db_attribute_error():
    """Test _store_token_in_db when postgres client doesn't have execute."""
    auth = RealmSyncAuth()
    # Create a mock that doesn't have execute
    postgres_client = MagicMock()
    del postgres_client.execute
    set_postgres_client(postgres_client)

    expires_at = datetime.now(UTC) + timedelta(minutes=30)
    # Should not raise an exception
    await auth._store_token_in_db("test-token", "user123", expires_at)


@pytest.mark.asyncio
async def test_revoke_token_in_db():
    """Test _revoke_token_in_db."""
    auth = RealmSyncAuth()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.execute = AsyncMock()
    set_postgres_client(postgres_client)

    await auth._revoke_token_in_db("test-token")
    postgres_client.execute.assert_called_once()


@pytest.mark.asyncio
async def test_revoke_token_in_db_attribute_error():
    """Test _revoke_token_in_db when postgres client doesn't have execute."""
    auth = RealmSyncAuth()
    # Create a mock that doesn't have execute
    postgres_client = MagicMock()
    del postgres_client.execute
    set_postgres_client(postgres_client)

    # Should not raise an exception
    await auth._revoke_token_in_db("test-token")


@pytest.mark.asyncio
async def test_validate_session_no_token():
    """Test validate_session when no token is provided."""
    auth = RealmSyncAuth()
    request = MagicMock(spec=Request)
    request.headers = {}

    with pytest.raises(HTTPException) as exc_info:
        await auth.validate_session(request)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_session_valid_token_no_db():
    """Test validate_session with valid token but no database check."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer test-token"}
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return None (no database check)
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(return_value=None)
    set_postgres_client(postgres_client)

    result = await auth.validate_session(request)
    assert result is True
    assert request.state.user_id == "user123"
    assert request.state.user_payload is not None


@pytest.mark.asyncio
async def test_validate_session_valid_token_with_db_not_expired():
    """Test validate_session with valid token and database check, not expired."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return token data with future expiration
    expires_at = datetime.now(UTC) + timedelta(minutes=20)
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": expires_at}
    )
    set_postgres_client(postgres_client)

    result = await auth.validate_session(request)
    assert result is True


@pytest.mark.asyncio
async def test_validate_session_valid_token_with_db_expired():
    """Test validate_session with valid token but expired in database."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return token data with past expiration
    expires_at = datetime.now(UTC) - timedelta(minutes=10)
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": expires_at}
    )
    set_postgres_client(postgres_client)

    with pytest.raises(HTTPException) as exc_info:
        await auth.validate_session(request)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_session_with_datetime_string():
    """Test validate_session with expires_at as string."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return token data with string expiration
    expires_at_str = (datetime.now(UTC) + timedelta(minutes=20)).isoformat()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": expires_at_str}
    )
    set_postgres_client(postgres_client)

    result = await auth.validate_session(request)
    assert result is True


@pytest.mark.asyncio
async def test_validate_session_with_naive_datetime():
    """Test validate_session with naive datetime."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return token data with naive datetime (future time)
    # Use UTC time but without timezone info to create naive datetime
    future_utc = datetime.now(UTC) + timedelta(minutes=20)
    expires_at = datetime(
        future_utc.year,
        future_utc.month,
        future_utc.day,
        future_utc.hour,
        future_utc.minute,
        future_utc.second,
        future_utc.microsecond,
    )  # Naive datetime with UTC time values
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": expires_at}
    )
    set_postgres_client(postgres_client)

    result = await auth.validate_session(request)
    assert result is True


@pytest.mark.asyncio
async def test_validate_session_with_unexpected_type():
    """Test validate_session with unexpected expires_at type."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client to return token data with unexpected type
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(
        return_value={"user_id": "user123", "expires_at": 12345}  # int instead of datetime
    )
    set_postgres_client(postgres_client)

    # Should still work, just skip expiration check
    result = await auth.validate_session(request)
    assert result is True


@pytest.mark.asyncio
async def test_create_token():
    """Test create_token."""
    auth = RealmSyncAuth(secret_key="test-secret")
    postgres_client = MockRealmSyncPostgres()
    postgres_client.execute = AsyncMock()
    set_postgres_client(postgres_client)

    token = await auth.create_token("user123")
    assert isinstance(token, str)
    assert len(token) > 0

    # Verify token can be decoded
    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert payload["sub"] == "user123"

    # Verify database was called
    postgres_client.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_token_with_additional_claims():
    """Test create_token with additional claims."""
    auth = RealmSyncAuth(secret_key="test-secret")
    postgres_client = MockRealmSyncPostgres()
    postgres_client.execute = AsyncMock()
    set_postgres_client(postgres_client)

    additional_claims = {"role": "admin", "permissions": ["read", "write"]}
    token = await auth.create_token("user123", additional_claims=additional_claims)

    # Verify token contains additional claims
    payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
    assert payload["sub"] == "user123"
    assert payload["role"] == "admin"
    assert payload["permissions"] == ["read", "write"]


@pytest.mark.asyncio
async def test_revoke_token():
    """Test revoke_token."""
    auth = RealmSyncAuth()
    postgres_client = MockRealmSyncPostgres()
    postgres_client.execute = AsyncMock()
    set_postgres_client(postgres_client)

    await auth.revoke_token("test-token")
    postgres_client.execute.assert_called_once()


@patch("realm_sync_api.dependencies.auth.pwd_context")
def test_verify_password(mock_pwd_context):
    """Test verify_password."""
    password = "test-password"
    hashed = "$2b$12$hashedpassword"

    # Mock verify to return True for correct password, False for incorrect
    def verify_side_effect(plain, hashed_pwd):
        return plain == password and hashed_pwd == hashed

    mock_pwd_context.verify.side_effect = verify_side_effect

    # Verify correct password
    assert RealmSyncAuth.verify_password(password, hashed) is True

    # Verify incorrect password
    assert RealmSyncAuth.verify_password("wrong-password", hashed) is False

    # Verify verify was called
    assert mock_pwd_context.verify.call_count == 2


@patch("realm_sync_api.dependencies.auth.pwd_context")
def test_get_password_hash(mock_pwd_context):
    """Test get_password_hash."""
    password = "test-password"
    mock_pwd_context.hash.return_value = "$2b$12$hashedpassword123"

    hashed = RealmSyncAuth.get_password_hash(password)

    assert isinstance(hashed, str)
    assert hashed == "$2b$12$hashedpassword123"
    assert len(hashed) > 0

    # Verify hash was called
    mock_pwd_context.hash.assert_called_once_with(password)


@pytest.mark.asyncio
async def test_get_current_user():
    """Test get_current_user."""
    auth = RealmSyncAuth(secret_key="test-secret")
    request = MagicMock(spec=Request)
    request.state = MagicMock()

    # Create a valid token
    data = {"sub": "user123", "exp": datetime.now(UTC) + timedelta(minutes=30)}
    token = jwt.encode(data, "test-secret", algorithm="HS256")
    request.headers = {"Authorization": f"Bearer {token}"}

    # Mock postgres client
    postgres_client = MockRealmSyncPostgres()
    postgres_client.fetch_one = AsyncMock(return_value=None)
    set_postgres_client(postgres_client)

    user = await auth.get_current_user(request)
    assert user["user_id"] == "user123"
    assert user["payload"] is not None
    assert user["payload"]["sub"] == "user123"

