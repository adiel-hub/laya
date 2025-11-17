"""
WebSocket server for real-time UI updates
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"🔌 WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        print(f"🔌 WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[Any, Any], websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[Any, Any]):
        """Send message to all connected clients"""
        print(f"📡 Broadcasting to {len(self.active_connections)} clients: {message.get('type')}")

        # Create a copy of connections list to avoid modification during iteration
        connections = self.active_connections.copy()

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"❌ Error sending to client: {e}")
                # Remove failed connection
                if connection in self.active_connections:
                    self.active_connections.remove(connection)


# Create global manager instance
manager = ConnectionManager()


@router.websocket("/ws/ui")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for UI clients

    Sends real-time updates about:
    - Call started
    - Call results (disposition, CX score)
    - Call ended
    - System events
    """
    await manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to LAYA Calling Agent WebSocket",
            "timestamp": "2025-01-17T00:00:00Z"
        })

        # Keep connection alive and listen for messages
        while True:
            # Receive messages from client (for ping/pong or commands)
            data = await websocket.receive_text()

            # Parse message
            try:
                message = json.loads(data)

                # Handle ping
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                # Handle other client messages if needed
                # (e.g., subscribe to specific channels, etc.)

            except json.JSONDecodeError:
                print(f"⚠️  Invalid JSON received: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("👋 Client disconnected normally")

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in manager.active_connections:
            manager.disconnect(websocket)


def get_manager() -> ConnectionManager:
    """Get the WebSocket manager instance"""
    return manager
