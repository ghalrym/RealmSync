import asyncio
import logging
import queue
from collections import deque
from datetime import datetime

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from .template import templates

router = APIRouter(prefix="/logs", tags=["logs"])

# Store logs in memory (last 1000 lines)
log_buffer: deque[dict] = deque(maxlen=1000)
# Store active WebSocket connections
active_connections: list[WebSocket] = []
# Queue for broadcasting logs (unbounded to prevent blocking)
log_queue: queue.Queue = queue.Queue(maxsize=0)


class LogHandler(logging.Handler):
    """Custom log handler that captures logs and broadcasts to WebSocket clients."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": self.format(record),
            "logger": record.name,
        }
        log_buffer.append(log_entry)
        # Add to queue for async broadcasting
        try:
            log_queue.put_nowait(log_entry)
        except queue.Full:
            pass  # Queue full, skip this log entry


# Set up the log handler
log_handler = LogHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Add handler to root logger
root_logger = logging.getLogger()
root_logger.addHandler(log_handler)
root_logger.setLevel(logging.DEBUG)

# Also capture uvicorn logs
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.addHandler(log_handler)
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.addHandler(log_handler)


async def broadcast_logs_task() -> None:
    """Background task to broadcast logs from queue to WebSocket clients."""
    while True:
        try:
            # Wait for log entry with timeout
            try:
                log_entry = log_queue.get(timeout=0.1)
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue

            # Broadcast to all connected clients
            if active_connections:
                disconnected = []
                for connection in active_connections:
                    try:
                        await connection.send_json(log_entry)
                    except Exception:
                        disconnected.append(connection)
                # Remove disconnected connections
                for conn in disconnected:
                    if conn in active_connections:
                        active_connections.remove(conn)
        except Exception:
            await asyncio.sleep(0.1)


# Start background task when module is imported
_broadcast_task: asyncio.Task | None = None


def start_broadcast_task() -> None:
    """Start the background broadcast task."""
    global _broadcast_task
    if _broadcast_task is None or _broadcast_task.done():
        try:
            loop = asyncio.get_event_loop()
            _broadcast_task = loop.create_task(broadcast_logs_task())
        except RuntimeError:
            # No event loop yet, will be started later
            pass


@router.get("/", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Display the logs page."""
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
        },
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming."""
    await websocket.accept()
    active_connections.append(websocket)

    # Start broadcast task if not already running
    start_broadcast_task()

    try:
        # Send existing logs to the newly connected client (in batches to avoid overwhelming)
        if log_buffer:
            # Send in smaller batches with small delays
            batch_size = 50
            log_list = list(log_buffer)
            for i in range(0, len(log_list), batch_size):
                batch = log_list[i : i + batch_size]
                for log_entry in batch:
                    try:
                        await websocket.send_json(log_entry)
                    except Exception:
                        # If sending fails, connection might be closed
                        raise
                # Small delay between batches
                if i + batch_size < len(log_list):
                    await asyncio.sleep(0.01)

        # Keep connection alive and handle incoming messages
        while True:
            # Wait for any message (ping/pong for keepalive)
            try:
                data = await websocket.receive_text()
                # Echo back for ping/pong
                if data == "ping":
                    try:
                        await websocket.send_text("pong")
                    except Exception:
                        # Connection closed, break out
                        break
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Log the error but don't break immediately
                logging.error("WebSocket error: %s", e)
                break
    except Exception as e:
        logging.error(f"WebSocket endpoint error: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        try:
            await websocket.close()
        except Exception:
            pass
