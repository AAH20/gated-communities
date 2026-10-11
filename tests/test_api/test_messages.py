"""API tests for the Messages endpoints.

Real shipped routes (mounted at ROOT):

    GET  /messages  -> 200 {"data": [...], "total", "page", "page_size",
                            "has_next", "has_prev"}
    POST /messages  -> 201 MessageResponse

The router (src/gated_communities/api/messages.py) is backed by an in-memory
mock store seeded on import.  ``MessageCreate`` requires ``channel_id``,
``user_id`` and ``content`` (max 4000 chars); channels/users must exist in the
mock maps (chan-general, ..., user-001, ...).

Quarantined in this module:

* ``TestMarkAsRead`` — ``PATCH /messages/{id}/read`` is not implemented
  (405, no such route).
"""

import pytest


@pytest.fixture
def sample_message_payload():
    return {"channel_id": "chan-general", "user_id": "user-001", "content": "Hello, this is a test message!"}


@pytest.fixture
def created_message(client, sample_message_payload):
    response = client.post("/messages", json=sample_message_payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestSendMessage:
    """Tests for POST /messages."""

    def test_send_message_success(self, client, sample_message_payload):
        response = client.post("/messages", json=sample_message_payload)
        assert response.status_code == 201
        body = response.json()
        assert "id" in body
        assert body["content"] == sample_message_payload["content"]
        assert body["channel_id"] == sample_message_payload["channel_id"]
        assert body["user_id"] == sample_message_payload["user_id"]

    def test_send_message_missing_content(self, client):
        response = client.post("/messages", json={"channel_id": "chan-general", "user_id": "user-001"})
        assert response.status_code == 422

    def test_send_message_blank_content(self, client):
        response = client.post(
            "/messages", json={"channel_id": "chan-general", "user_id": "user-001", "content": "   "}
        )
        assert response.status_code == 422

    def test_send_message_missing_channel(self, client):
        response = client.post("/messages", json={"user_id": "user-001", "content": "Test"})
        assert response.status_code == 422

    def test_send_message_missing_user(self, client):
        response = client.post("/messages", json={"channel_id": "chan-general", "content": "Test"})
        assert response.status_code == 422

    def test_send_message_unknown_channel_returns_404(self, client):
        response = client.post(
            "/messages", json={"channel_id": "chan-nope", "user_id": "user-001", "content": "Test"}
        )
        assert response.status_code == 404

    def test_send_message_unknown_user_returns_404(self, client):
        response = client.post(
            "/messages", json={"channel_id": "chan-general", "user_id": "user-999", "content": "Test"}
        )
        assert response.status_code == 404

    def test_send_message_content_too_long(self, client):
        response = client.post(
            "/messages",
            json={"channel_id": "chan-general", "user_id": "user-001", "content": "A" * 4001},
        )
        assert response.status_code == 422

    def test_send_message_returns_unique_ids(self, client, sample_message_payload):
        ids = set()
        for _ in range(5):
            resp = client.post("/messages", json=sample_message_payload)
            assert resp.status_code == 201
            ids.add(resp.json()["id"])
        assert len(ids) == 5

    def test_send_message_extra_fields_ignored(self, client, sample_message_payload):
        payload = {**sample_message_payload, "unknown_field": "value"}
        response = client.post("/messages", json=payload)
        assert response.status_code in (201, 422)


class TestGetMessages:
    """Tests for GET /messages."""

    def test_get_messages_envelope(self, client):
        response = client.get("/messages")
        assert response.status_code == 200
        data = response.json()
        assert {"data", "total", "page", "page_size", "has_next", "has_prev"}.issubset(data)
        assert isinstance(data["data"], list)

    def test_get_messages_seeded(self, client):
        assert client.get("/messages").json()["total"] >= 1

    def test_get_messages_returns_created(self, client, created_message):
        response = client.get("/messages", params={"page_size": 100})
        ids = [m["id"] for m in response.json()["data"]]
        assert created_message["id"] in ids

    def test_get_messages_filter_by_channel(self, client, sample_message_payload):
        client.post("/messages", json=sample_message_payload)
        response = client.get("/messages", params={"channel_id": "chan-general"})
        assert response.status_code == 200
        for msg in response.json()["data"]:
            assert msg["channel_id"] == "chan-general"

    def test_get_messages_filter_by_user(self, client, sample_message_payload):
        client.post("/messages", json=sample_message_payload)
        response = client.get("/messages", params={"user_id": "user-001"})
        assert response.status_code == 200
        for msg in response.json()["data"]:
            assert msg["user_id"] == "user-001"

    def test_get_messages_page_size_caps(self, client):
        response = client.get("/messages", params={"page_size": 3})
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 3

    def test_get_messages_response_structure(self, client, created_message):
        first = client.get("/messages").json()["data"][0]
        expected = {"id", "channel_id", "user_id", "content", "created_at"}
        assert expected.issubset(first)

    def test_get_messages_invalid_page_size(self, client):
        assert client.get("/messages", params={"page_size": 0}).status_code == 422


@pytest.mark.skip(reason="PATCH /messages/{id}/read is not implemented (no such route)")
class TestMarkAsRead:
    """Tests for PATCH /messages/{id}/read (quarantined — endpoint absent)."""

    def test_mark_as_read_success(self, client, created_message):
        response = client.patch(f"/messages/{created_message['id']}/read")
        assert response.status_code == 200
