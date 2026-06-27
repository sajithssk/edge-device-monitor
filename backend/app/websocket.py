import json
import logging
from typing import List, Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.frontend_connections: List[WebSocket] = []
        self.device_connections: Dict[str, WebSocket] = {}

    async def connect_frontend(self, websocket: WebSocket):
        self.frontend_connections.append(websocket)
        logger.info("Frontend connected. Total: %d", len(self.frontend_connections))

    def disconnect_frontend(self, websocket: WebSocket):
        if websocket in self.frontend_connections:
            self.frontend_connections.remove(websocket)

    async def connect_device(self, device_id: str, websocket: WebSocket):
        old = self.device_connections.get(device_id)
        if old:
            try:
                await old.close()
            except Exception:
                pass
        self.device_connections[device_id] = websocket
        logger.info("Device %s connected", device_id)

    def disconnect_device(self, device_id: str):
        if device_id in self.device_connections:
            del self.device_connections[device_id]
            logger.info("Device %s disconnected", device_id)

    async def broadcast_to_frontends(self, message: dict):
        text = json.dumps(message)
        disconnected = []
        for conn in self.frontend_connections:
            try:
                await conn.send_text(text)
            except Exception as e:
                logger.warning("Failed to send to frontend: %s", e)
                disconnected.append(conn)
        for conn in disconnected:
            self.disconnect_frontend(conn)

    async def send_to_device(self, device_id: str, message: dict) -> bool:
        ws = self.device_connections.get(device_id)
        if not ws:
            return False
        try:
            await ws.send_text(json.dumps(message))
            return True
        except Exception as e:
            logger.warning("Failed to send to device %s: %s", device_id, e)
            self.disconnect_device(device_id)
            return False


manager = ConnectionManager()
