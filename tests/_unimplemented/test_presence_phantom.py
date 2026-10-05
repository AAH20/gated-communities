"""Tests for WebSocket online presence tracking."""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebSocketPresence:
    """Test WebSocket presence tracking and status updates."""

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
    async def presence_tracker(self):
        """Create a presence tracker instance."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()
        yield tracker
        await tracker.clear()

    @pytest.mark.asyncio
    async def test_user_comes_online(self, mock_websocket):
        """Test that a user is marked as online when they connect."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)

        assert tracker.is_online("user_1")
        assert tracker.get_status("user_1") == "online"

    @pytest.mark.asyncio
    async def test_user_goes_offline(self, mock_websocket):
        """Test that a user is marked as offline when they disconnect."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)
        await tracker.user_disconnected("user_1")

        assert not tracker.is_online("user_1")

    @pytest.mark.asyncio
    async def test_get_online_users(self, mock_websocket):
        """Test retrieving the list of online users."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        ws2 = AsyncMock()
        await tracker.user_connected("user_1", mock_websocket)
        await tracker.user_connected("user_2", ws2)

        online_users = tracker.get_online_users()

        assert "user_1" in online_users
        assert "user_2" in online_users
        assert len(online_users) == 2

    @pytest.mark.asyncio
    async def test_get_online_count(self, mock_websocket):
        """Test getting the count of online users."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        assert tracker.get_online_count() == 0

        await tracker.user_connected("user_1", mock_websocket)
        assert tracker.get_online_count() == 1

        ws2 = AsyncMock()
        await tracker.user_connected("user_2", ws2)
        assert tracker.get_online_count() == 2

    @pytest.mark.asyncio
    async def test_presence_status_update(self, mock_websocket):
        """Test updating a user's presence status."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)
        await tracker.update_status("user_1", "away")

        assert tracker.get_status("user_1") == "away"

    @pytest.mark.asyncio
    async def test_presence_status_invalid(self, mock_websocket):
        """Test that invalid presence statuses are rejected."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)

        with pytest.raises(ValueError, match="Invalid status"):
            await tracker.update_status("user_1", "invalid_status")

    @pytest.mark.asyncio
    async def test_presence_broadcast_on_connect(self, mock_websocket):
        """Test that presence is broadcast when a user connects."""
        from src.websocket.presence import PresenceTracker
        from src.websocket.connection import ConnectionManager

        tracker = PresenceTracker()
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket)
        await manager.connect("user_2", ws2)

        await tracker.user_connected("user_3", AsyncMock(), broadcast_manager=manager)

        # All connected users should receive the presence update
        expected_msg = json.dumps({
            "type": "presence",
            "user_id": "user_3",
            "status": "online",
        })
        mock_websocket.send.assert_called_with(expected_msg)
        ws2.send.assert_called_with(expected_msg)

    @pytest.mark.asyncio
    async def test_presence_broadcast_on_disconnect(self, mock_websocket):
        """Test that presence is broadcast when a user disconnects."""
        from src.websocket.presence import PresenceTracker
        from src.websocket.connection import ConnectionManager

        tracker = PresenceTracker()
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)
        await tracker.user_connected("user_2", AsyncMock(), broadcast_manager=manager)
        await tracker.user_disconnected("user_2", broadcast_manager=manager)

        expected_msg = json.dumps({
            "type": "presence",
            "user_id": "user_2",
            "status": "offline",
        })
        mock_websocket.send.assert_called_with(expected_msg)

    @pytest.mark.asyncio
    async def test_presence_heartbeat(self, mock_websocket):
        """Test that presence heartbeats keep users online."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker(heartbeat_timeout=0.2)

        await tracker.user_connected("user_1", mock_websocket)

        # Send heartbeat before timeout
        await asyncio.sleep(0.1)
        await tracker.heartbeat("user_1")
        await asyncio.sleep(0.1)

        assert tracker.is_online("user_1")

    @pytest.mark.asyncio
    async def test_presence_heartbeat_timeout(self, mock_websocket):
        """Test that users are marked offline after heartbeat timeout."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker(heartbeat_timeout=0.1)

        await tracker.user_connected("user_1", mock_websocket)
        await asyncio.sleep(0.2)

        assert not tracker.is_online("user_1")

    @pytest.mark.asyncio
    async def test_presence_last_seen(self, mock_websocket):
        """Test that last seen timestamp is tracked."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)
        last_seen = tracker.get_last_seen("user_1")

        assert last_seen is not None
        assert isinstance(last_seen, (int, float))

    @pytest.mark.asyncio
    async def test_presence_status_transitions(self, mock_websocket):
        """Test valid presence status transitions."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        await tracker.user_connected("user_1", mock_websocket)

        await tracker.update_status("user_1", "away")
        assert tracker.get_status("user_1") == "away"

        await tracker.update_status("user_1", "online")
        assert tracker.get_status("user_1") == "online"

        await tracker.update_status("user_1", "busy")
        assert tracker.get_status("user_1") == "busy"

    @pytest.mark.asyncio
    async def test_presence_multiple_statuses(self, mock_websocket):
        """Test that different users can have different statuses."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        ws2 = AsyncMock()
        ws3 = AsyncMock()

        await tracker.user_connected("user_1", mock_websocket)
        await tracker.user_connected("user_2", ws2)
        await tracker.user_connected("user_3", ws3)

        await tracker.update_status("user_1", "online")
        await tracker.update_status("user_2", "away")
        await tracker.update_status("user_3", "busy")

        assert tracker.get_status("user_1") == "online"
        assert tracker.get_status("user_2") == "away"
        assert tracker.get_status("user_3") == "busy"

    @pytest.mark.asyncio
    async def test_presence_clear_all(self, mock_websocket):
        """Test clearing all presence data."""
        from src.websocket.presence import PresenceTracker
        tracker = PresenceTracker()

        ws2 = AsyncMock()
        await tracker.user_connected("user_1", mock_websocket)
        await tracker.user_connected("user_2", ws2)

        await tracker.clear()

        assert tracker.get_online_count() == 0
        assert not tracker.is_online("user_1")
        assert not tracker.is_online("user_2")
