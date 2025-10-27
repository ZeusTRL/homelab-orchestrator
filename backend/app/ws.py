# backend/app/ws.py
from __future__ import annotations
from typing import Set, Dict, Any
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
PING_INTERVAL_SEC = 30

class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return
        # Send concurrently; drop dead sockets
        to_remove = []
        payload = message
        for ws in list(self.active_connections):
            try:
                await ws.send_json(payload)
            except Exception:
                to_remove.append(ws)
        if to_remove:
            async with self._lock:
                for ws in to_remove:
                    self.active_connections.discard(ws)

manager = ConnectionManager()

@router.websocket("/ws/topology")
async def topology_ws(websocket: WebSocket):
    """
    Simple WS endpoint:
      - accepts connection
      - sends periodic ping text to keep NATs alive
      - listens for optional client pings/echo (ignored)
    """
    await manager.connect(websocket)
    try:
        while True:
            # race: either client sends a message or ping timer ticks
            ping = asyncio.create_task(asyncio.sleep(PING_INTERVAL_SEC))
            recv = asyncio.create_task(websocket.receive_text())
            done, pending = await asyncio.wait({ping, recv}, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            if recv in done:
                # ignore content; could add commands later
                try:
                    _ = recv.result()
                except Exception:
                    # client closed
                    break
            else:
                # ping timer fired
                try:
                    await websocket.send_text("ping")
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)

# Convenience helpers to trigger broadcasts from endpoints/services

async def notify_topology_update() -> None:
    """Async helper (use inside async endpoints)."""
    await manager.broadcast({"event": "update_topology"})

def notify_topology_update_background() -> None:
    """
    Fire-and-forget helper usable with BackgroundTasks or threads.
    Schedules the async broadcast on the running loop.
    """
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast({"event": "update_topology"}))
    except RuntimeError:
        # No running loop (rare under uvicorn); safely ignore
        pass
