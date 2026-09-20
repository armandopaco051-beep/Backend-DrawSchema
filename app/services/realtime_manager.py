from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from fastapi import WebSocket


class RealtimeConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, dict[WebSocket, dict[str, Any]]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, diagrama_id: int, websocket: WebSocket, user: dict[str, Any]):
        await websocket.accept()

        async with self.lock:
            self.active_connections.setdefault(diagrama_id, {})
            self.active_connections[diagrama_id][websocket] = user

    async def disconnect(self, diagrama_id: int, websocket: WebSocket):
        async with self.lock:
            room = self.active_connections.get(diagrama_id)

            if not room:
                return None

            user = room.pop(websocket, None)

            if not room:
                self.active_connections.pop(diagrama_id, None)

            return user

    async def get_users(self, diagrama_id: int):
        async with self.lock:
            room = self.active_connections.get(diagrama_id, {})
            return list(room.values())

    async def broadcast(
        self,
        diagrama_id: int,
        message: dict[str, Any],
        exclude: WebSocket | None = None,
    ):
        async with self.lock:
            room = dict(self.active_connections.get(diagrama_id, {}))

        disconnected: list[WebSocket] = []

        for websocket in room:
            if websocket is exclude:
                continue

            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)

        if disconnected:
            async with self.lock:
                current_room = self.active_connections.get(diagrama_id)

                if current_room:
                    for websocket in disconnected:
                        current_room.pop(websocket, None)

                    if not current_room:
                        self.active_connections.pop(diagrama_id, None)


def utc_now_iso():
    return datetime.utcnow().isoformat()


realtime_manager = RealtimeConnectionManager()
