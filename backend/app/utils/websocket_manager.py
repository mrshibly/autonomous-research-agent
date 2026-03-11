import asyncio
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

class ConnectionManager:
    """
    Manages active WebSocket connections for research task updates.
    Each client subscribes to a specific task_id.
    """
    def __init__(self):
        # Maps task_id -> set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept connection and add to the task's group."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket connected for task {task_id}. Total: {len(self.active_connections[task_id])}")

    def disconnect(self, websocket: WebSocket, task_id: str):
        """Remove connection from the task's group."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logger.info(f"WebSocket disconnected for task {task_id}")

    async def broadcast_update(self, task_id: str, data: dict):
        """Broadcast status update to all clients watching this task."""
        if task_id not in self.active_connections:
            return

        disconnected_sockets = set()
        message = {
            "task_id": task_id,
            "type": "status_update",
            "data": data
        }

        # Use gather for concurrent broadcasting
        tasks = []
        for connection in self.active_connections[task_id]:
            tasks.append(self._send_message(connection, message, disconnected_sockets))
        
        if tasks:
            await asyncio.gather(*tasks)

        # Cleanup disconnected sockets
        for ws in disconnected_sockets:
            self.disconnect(ws, task_id)

    async def _send_message(self, websocket: WebSocket, message: dict, disconnected_set: set):
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected_set.add(websocket)

# Global manager instance
manager = ConnectionManager()
