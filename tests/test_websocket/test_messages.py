"""Tests for WebSocket real-time messaging."""

import pytest
import pytest_asyncio
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebSocketMessages:
    """Test WebSocket message sending, receiving, and broadcasting."""

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
    async def message_handler(self):
        """Create a message handler instance."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()
        yield handler

    @pytest.mark.asyncio
    async def test_send_personal_message(self, mock_websocket):
        """Test sending a message to a specific user."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)
        message = {"type": "text", "content": "Hello, user!"}
        await manager.send_personal_message("user_1", message)

        mock_websocket.send.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_user(self):
        """Test sending a message to a non-existent user."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        with pytest.raises(KeyError):
            await manager.send_personal_message("nonexistent", {"type": "text"})

    @pytest.mark.asyncio
    async def test_broadcast_message(self, mock_websocket):
        """Test broadcasting a message to all connected users."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket)
        await manager.connect("user_2", ws2)

        message = {"type": "broadcast", "content": "Hello, everyone!"}
        await manager.broadcast(message)

        expected = json.dumps(message)
        mock_websocket.send.assert_called_with(expected)
        ws2.send.assert_called_with(expected)

    @pytest.mark.asyncio
    async def test_broadcast_excludes_sender(self, mock_websocket):
        """Test that broadcast can exclude the sender."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket)
        await manager.connect("user_2", ws2)

        message = {"type": "broadcast", "content": "Hello!"}
        await manager.broadcast(message, exclude=["user_1"])

        mock_websocket.send.assert_not_called()
        ws2.send.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_receive_message(self, mock_websocket):
        """Test receiving a message from a client."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        incoming = {"type": "text", "content": "Test message"}
        mock_websocket.recv.return_value = json.dumps(incoming)

        result = await handler.handle_message("user_1", mock_websocket)

        assert result["type"] == "text"
        assert result["content"] == "Test message"

    @pytest.mark.asyncio
    async def test_receive_invalid_json(self, mock_websocket):
        """Test handling of invalid JSON messages."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        mock_websocket.recv.return_value = "not valid json"

        with pytest.raises(json.JSONDecodeError):
            await handler.handle_message("user_1", mock_websocket)

    @pytest.mark.asyncio
    async def test_message_validation(self):
        """Test that messages are validated before processing."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        invalid_message = {"content": "Missing type field"}

        with pytest.raises(ValueError, match="Invalid message format"):
            await handler.validate_message(invalid_message)

    @pytest.mark.asyncio
    async def test_message_type_routing(self):
        """Test that messages are routed based on type."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        text_handler = AsyncMock()
        handler.register_handler("text", text_handler)

        message = {"type": "text", "content": "Hello"}
        await handler.route_message("user_1", message)

        text_handler.assert_called_once_with("user_1", message)

    @pytest.mark.asyncio
    async def test_unhandled_message_type(self):
        """Test handling of unregistered message types."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        message = {"type": "unknown_type", "data": "test"}

        with pytest.raises(ValueError, match="No handler for message type"):
            await handler.route_message("user_1", message)

    @pytest.mark.asyncio
    async def test_message_to_group(self, mock_websocket):
        """Test sending a message to a specific group/room."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        ws2 = AsyncMock()
        await manager.connect("user_1", mock_websocket, metadata={"room": "general"})
        await manager.connect("user_2", ws2, metadata={"room": "general"})

        message = {"type": "text", "content": "Hello, room!"}
        await manager.send_to_room("general", message)

        mock_websocket.send.assert_called_once_with(json.dumps(message))
        ws2.send.assert_called_once_with(json.dumps(message))

    @pytest.mark.asyncio
    async def test_message_to_empty_group(self):
        """Test sending a message to a group with no members."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        message = {"type": "text", "content": "Hello?"}
        await manager.send_to_room("empty_room", message)

    @pytest.mark.asyncio
    async def test_message_serialization(self):
        """Test that messages are properly serialized."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        message = {
            "type": "text",
            "content": "Hello",
            "timestamp": 1234567890,
            "metadata": {"key": "value"},
        }

        serialized = handler.serialize_message(message)
        deserialized = json.loads(serialized)

        assert deserialized == message

    @pytest.mark.asyncio
    async def test_message_deserialization(self):
        """Test that messages are properly deserialized."""
        from src.websocket.messages import MessageHandler
        handler = MessageHandler()

        raw = json.dumps({"type": "text", "content": "Hello"})
        deserialized = handler.deserialize_message(raw)

        assert deserialized["type"] == "text"
        assert deserialized["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_concurrent_message_sending(self, mock_websocket):
        """Test that multiple messages can be sent concurrently."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)

        messages = [{"type": "text", "content": f"Message {i}"} for i in range(10)]
        await asyncio.gather(*[
            manager.send_personal_message("user_1", msg) for msg in messages
        ])

        assert mock_websocket.send.call_count == 10

    @pytest.mark.asyncio
    async def test_message_ordering(self, mock_websocket):
        """Test that messages are sent in order."""
        from src.websocket.connection import ConnectionManager
        manager = ConnectionManager()

        await manager.connect("user_1", mock_websocket)

        for i in range(5):
            await manager.send_personal_message("user_1", {"seq": i})

        calls = mock_websocket.send.call_args_list
        for i, call in enumerate(calls):
            sent_data = json.loads(call[0][0])
            assert sent_data["seq"] == i
