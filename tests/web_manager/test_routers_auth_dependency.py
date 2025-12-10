"""Tests for web_manager auth_dependency."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

from realm_sync_api.dependencies.auth import RealmSyncAuth
from realm_sync_api.web_manager.routers.auth_dependency import check_auth
from realm_sync_api.web_manager.routers.template import templates


@pytest.mark.asyncio
async def test_check_auth_no_auth():
    """Test check_auth when no auth is configured."""
    # Set templates globals to have no auth
    templates.env.globals["web_auth"] = None
    templates.env.globals["web_prefix"] = "/web"

    request = MagicMock(spec=Request)
    result = await check_auth(request)
    assert result is None


@pytest.mark.asyncio
async def test_check_auth_valid_session():
    """Test check_auth with valid session."""
    auth = MagicMock(spec=RealmSyncAuth)
    auth.validate_session = AsyncMock(return_value=True)
    templates.env.globals["web_auth"] = auth
    templates.env.globals["web_prefix"] = "/web"

    request = MagicMock(spec=Request)
    result = await check_auth(request)
    assert result is None
    auth.validate_session.assert_called_once_with(request)


@pytest.mark.asyncio
async def test_check_auth_http_exception():
    """Test check_auth redirects on HTTPException (lines 23-28)."""
    auth = MagicMock(spec=RealmSyncAuth)
    auth.validate_session = AsyncMock(side_effect=HTTPException(status_code=401, detail="Unauthorized"))
    templates.env.globals["web_auth"] = auth
    templates.env.globals["web_prefix"] = "/web"

    request = MagicMock(spec=Request)
    result = await check_auth(request)
    assert isinstance(result, RedirectResponse)
    assert result.status_code == status.HTTP_303_SEE_OTHER
    assert "/web/login" in result.headers.get("location", "")

