"""Tests for WebSocket connection lifecycle."""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebSocketConnection:
    """Test WebSocket connection establishment and teardown."""

    @pytest_asyncio.fixture
    async def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = AsyncMock()
        ws.send = AsyncMock()
        ws.recv = AsyncMock()
        ws.close = AsyncMock()
        ws.closed = False
        return ws

    @pytest_asyncio.fixture
    async def connection_manager(self):
        """Create a connection manager instance."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()
        yield manager
        await manager.disconnect_all()

    @pytest.mark.asyncio
    async def test_connection_establishment(self, mock_websocket):
        """Test that a WebSocket connection can be established."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)

        assert "user_1" in manager.active_connections
        assert manager.active_connections["user_1"] is mock_websocket

    @pytest.mark.asyncio
    async def test_connection_rejection_duplicate(self, mock_websocket):
        """Test that duplicate connections for the same user are rejected."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)

        with pytest.raises(ConnectionError, match="already connected"):
            await manager.connect("user_1", mock_websocket)

    @pytest.mark.asyncio
    async def test_connection_close(self, mock_websocket):
        """Test that a WebSocket connection can be closed."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)
        await manager.disconnect("user_1")

        assert "user_1" not in manager.active_connections
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_close_nonexistent(self):
        """Test that closing a non-existent connection raises an error."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        with pytest.raises(KeyError):
            await manager.disconnect("nonexistent_user")

    @pytest.mark.asyncio
    async def test_connection_ping_pong(self, mock_websocket):
        """Test that ping/pong keepalive works."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)
        await manager.send_ping("user_1")

        mock_websocket.send.assert_called_with(json.dumps({"type": "ping"}))

    @pytest.mark.asyncio
    async def test_connection_timeout(self, mock_websocket):
        """Test that idle connections are timed out."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager(timeout=0.1)

        await manager.connect("user_1", mock_websocket)
        await asyncio.sleep(0.2)

        assert "user_1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_websocket):
        """Test that connection errors are handled gracefully."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        mock_websocket.send.side_effect = ConnectionResetError("Connection lost")

        await manager.connect("user_1", mock_websocket)

        with pytest.raises(ConnectionResetError):
            await manager.send_personal_message("user_1", {"type": "test"})

    @pytest.mark.asyncio
    async def test_multiple_connections(self, mock_websocket):
        """Test that multiple users can connect simultaneously."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket)
        await manager.connect("user_2", ws2)

        assert len(manager.active_connections) == 2
        assert "user_1" in manager.active_connections
        assert "user_2" in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_all(self, mock_websocket):
        """Test that all connections can be closed at once."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket)
        await manager.connect("user_2", ws2)
        await manager.disconnect_all()

        assert len(manager.active_connections) == 0
        mock_websocket.close.assert_called_once()
        ws2.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_metadata(self, mock_websocket):
        """Test that connection metadata is stored correctly."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        metadata = {"ip": "127.0.0.1", "user_agent": "test-client"}
        await manager.connect("user_1", mock_websocket, metadata=metadata)

        assert manager.get_connection_info("user_1")["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_connection_count(self, mock_websocket):
        """Test that connection count is accurate."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        assert manager.connection_count == 0

        await manager.connect("user_1", mock_websocket)
        assert manager.connection_count == 1

        await manager.disconnect("user_1")
        assert manager.connection_count == 0
