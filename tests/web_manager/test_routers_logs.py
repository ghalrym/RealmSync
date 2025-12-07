"""Tests for web_manager logs router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from realm_sync_api.web_manager.routers import logs_router


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(logs_router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


def test_logs_page(app):
    """Test logs page endpoint."""
    client = TestClient(app)
    response = client.get("/logs/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_log_handler_emit():
    """Test that LogHandler.emit adds logs to buffer."""
    import logging

    from realm_sync_api.web_manager.routers.logs import LogHandler, log_buffer

    handler = LogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.created = 1234567890.0

    initial_len = len(log_buffer)
    handler.emit(record)
    assert len(log_buffer) == initial_len + 1
    assert log_buffer[-1]["message"] == "Test message"


@pytest.mark.asyncio
async def test_websocket_endpoint():
    """Test WebSocket endpoint."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(logs_router)
    client = TestClient(app)

    with client.websocket_connect("/logs/ws") as websocket:
        # Connection should be accepted
        # Send a ping
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"


@pytest.mark.asyncio
async def test_websocket_sends_existing_logs():
    """Test that WebSocket sends existing logs to new connections."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from realm_sync_api.web_manager.routers.logs import log_buffer
    from realm_sync_api.web_manager.web_manager_router import WebManagerRouter

    # Add some logs to the buffer
    log_buffer.clear()
    for i in range(10):
        log_buffer.append(
            {
                "timestamp": "2024-01-01T00:00:00",
                "level": "INFO",
                "message": f"Log {i}",
                "logger": "test",
            }
        )

    app = FastAPI()
    app.include_router(WebManagerRouter(prefix="/web"))
    app.include_router(logs_router)
    client = TestClient(app)

    with client.websocket_connect("/logs/ws") as websocket:
        # Should receive the existing logs
        received_logs = []
        try:
            while True:
                data = websocket.receive_json(timeout=0.5)
                received_logs.append(data)
        except Exception:
            pass
        # Should have received at least some logs
        assert len(received_logs) > 0
