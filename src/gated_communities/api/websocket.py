"""WebSocket endpoint for real-time communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, community_id: str):
        await websocket.accept()
        if community_id not in self.active_connections:
            self.active_connections[community_id] = []
        self.active_connections[community_id].append(websocket)

    def disconnect(self, websocket: WebSocket, community_id: str):
        if community_id in self.active_connections:
            self.active_connections[community_id].remove(websocket)
            if not self.active_connections[community_id]:
                del self.active_connections[community_id]

    async def broadcast(self, message: str, community_id: str):
        if community_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[community_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.active_connections[community_id].remove(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, community_id: str = "default"):
    await manager.connect(websocket, community_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}", community_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, community_id)
        await manager.broadcast("A user disconnected", community_id)
