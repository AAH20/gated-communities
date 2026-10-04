"""Comprehensive API tests for the Comments endpoints."""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    from gated_communities.main import app

    return TestClient(app)


@pytest.fixture
def sample_comment_payload():
    """Return a valid payload for creating a comment."""
    return {
        "post_id": "post-123",
        "author_id": "user-456",
        "content": "This is a test comment.",
    }


@pytest.fixture
def created_comment(client, sample_comment_payload):
    """Create a comment via the API and return the response JSON."""
    response = client.post("/api/v1/comments", json=sample_comment_payload)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# 1. GET /api/v1/comments — list with pagination
# ---------------------------------------------------------------------------


class TestListComments:
    """Tests for GET /api/v1/comments."""

    def test_list_comments_returns_200(self, client):
        """GET /api/v1/comments should return HTTP 200."""
        response = client.get("/api/v1/comments")
        assert response.status_code == 200

    def test_list_comments_returns_list(self, client):
        """GET /api/v1/comments should return a JSON list."""
        response = client.get("/api/v1/comments")
        data = response.json()
        assert isinstance(data, list)

    def test_list_comments_empty(self, client):
        """GET /api/v1/comments should return an empty list when no comments exist."""
        response = client.get("/api/v1/comments")
        data = response.json()
        assert data == []

    def test_list_comments_pagination_limit(self, client, sample_comment_payload):
        """GET /api/v1/comments?limit=N should return at most N comments."""
        # Create 5 comments
        for i in range(5):
            payload = {**sample_comment_payload, "content": f"Comment {i}"}
            client.post("/api/v1/comments", json=payload)

        response = client.get("/api/v1/comments", params={"limit": 3})
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_list_comments_pagination_offset(self, client, sample_comment_payload):
        """GET /api/v1/comments?offset=N should skip the first N comments."""
        # Create 5 comments
        for i in range(5):
            payload = {**sample_comment_payload, "content": f"Comment {i}"}
            client.post("/api/v1/comments", json=payload)

        # Get all comments
        all_response = client.get("/api/v1/comments")
        all_data = all_response.json()

        # Get comments with offset=2
        offset_response = client.get("/api/v1/comments", params={"offset": 2})
        offset_data = offset_response.json()

        assert len(offset_data) == len(all_data) - 2
        # The offset data should be a subset starting from index 2
        if len(all_data) > 2:
            assert offset_data[0]["id"] == all_data[2]["id"]

    def test_list_comments_pagination_limit_and_offset(self, client, sample_comment_payload):
        """GET /api/v1/comments?limit=N&offset=M should paginate correctly."""
        # Create 10 comments
        for i in range(10):
            payload = {**sample_comment_payload, "content": f"Comment {i}"}
            client.post("/api/v1/comments", json=payload)

        response = client.get(
            "/api/v1/comments", params={"limit": 3, "offset": 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    def test_list_comments_default_pagination(self, client, sample_comment_payload):
        """GET /api/v1/comments should return all comments by default (no pagination params)."""
        # Create 3 comments
        for i in range(3):
            payload = {**sample_comment_payload, "content": f"Comment {i}"}
            client.post("/api/v1/comments", json=payload)

        response = client.get("/api/v1/comments")
        data = response.json()
        assert len(data) >= 3


# ---------------------------------------------------------------------------
# 2. POST /api/v1/comments — create
# ---------------------------------------------------------------------------


class TestCreateComment:
    """Tests for POST /api/v1/comments."""

    def test_create_comment_returns_201(self, client, sample_comment_payload):
        """POST /api/v1/comments should return HTTP 201 on success."""
        response = client.post("/api/v1/comments", json=sample_comment_payload)
        assert response.status_code == 201

    def test_create_comment_returns_created_comment(self, client, sample_comment_payload):
        """POST /api/v1/comments should return the created comment with an id."""
        response = client.post("/api/v1/comments", json=sample_comment_payload)
        data = response.json()
        assert "id" in data
        assert data["content"] == sample_comment_payload["content"]
        assert data["post_id"] == sample_comment_payload["post_id"]
        assert data["author_id"] == sample_comment_payload["author_id"]

    def test_create_comment_missing_content(self, client):
        """POST /api/v1/comments without content should return 422."""
        payload = {"post_id": "post-123", "author_id": "user-456"}
        response = client.post("/api/v1/comments", json=payload)
        assert response.status_code == 422

    def test_create_comment_missing_post_id(self, client):
        """POST /api/v1/comments without post_id should return 422."""
        payload = {"author_id": "user-456", "content": "Test comment"}
        response = client.post("/api/v1/comments", json=payload)
        assert response.status_code == 422

    def test_create_comment_missing_author_id(self, client):
        """POST /api/v1/comments without author_id should return 422."""
        payload = {"post_id": "post-123", "content": "Test comment"}
        response = client.post("/api/v1/comments", json=payload)
        assert response.status_code == 422

    def test_create_comment_empty_content(self, client):
        """POST /api/v1/comments with empty content should return 422."""
        payload = {"post_id": "post-123", "author_id": "user-456", "content": ""}
        response = client.post("/api/v1/comments", json=payload)
        assert response.status_code == 422

    def test_create_comment_persists(self, client, sample_comment_payload):
        """POST /api/v1/comments should persist the comment so it can be retrieved."""
        create_response = client.post(
            "/api/v1/comments", json=sample_comment_payload
        )
        created = create_response.json()

        get_response = client.get(f"/api/v1/comments/{created['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["id"] == created["id"]
        assert fetched["content"] == sample_comment_payload["content"]


# ---------------------------------------------------------------------------
# 3. GET /api/v1/comments/{id} — retrieve
# ---------------------------------------------------------------------------


class TestGetComment:
    """Tests for GET /api/v1/comments/{id}."""

    def test_get_comment_returns_200(self, client, created_comment):
        """GET /api/v1/comments/{id} should return HTTP 200 for an existing comment."""
        response = client.get(f"/api/v1/comments/{created_comment['id']}")
        assert response.status_code == 200

    def test_get_comment_returns_correct_data(self, client, created_comment):
        """GET /api/v1/comments/{id} should return the correct comment data."""
        response = client.get(f"/api/v1/comments/{created_comment['id']}")
        data = response.json()
        assert data["id"] == created_comment["id"]
        assert data["content"] == created_comment["content"]
        assert data["post_id"] == created_comment["post_id"]
        assert data["author_id"] == created_comment["author_id"]

    def test_get_comment_not_found(self, client):
        """GET /api/v1/comments/{id} should return 404 for a non-existent comment."""
        response = client.get("/api/v1/comments/nonexistent-id")
        assert response.status_code == 404

    def test_get_comment_invalid_id_format(self, client):
        """GET /api/v1/comments/{id} should handle invalid id formats gracefully."""
        response = client.get("/api/v1/comments/!!!invalid!!!")
        assert response.status_code in (404, 422)


# ---------------------------------------------------------------------------
# 4. PUT /api/v1/comments/{id} — update
# ---------------------------------------------------------------------------


class TestUpdateComment:
    """Tests for PUT /api/v1/comments/{id}."""

    def test_update_comment_returns_200(self, client, created_comment):
        """PUT /api/v1/comments/{id} should return HTTP 200 on success."""
        update_payload = {"content": "Updated comment content"}
        response = client.put(
            f"/api/v1/comments/{created_comment['id']}", json=update_payload
        )
        assert response.status_code == 200

    def test_update_comment_returns_updated_data(self, client, created_comment):
        """PUT /api/v1/comments/{id} should return the updated comment."""
        update_payload = {"content": "Updated comment content"}
        response = client.put(
            f"/api/v1/comments/{created_comment['id']}", json=update_payload
        )
        data = response.json()
        assert data["id"] == created_comment["id"]
        assert data["content"] == "Updated comment content"

    def test_update_comment_persists(self, client, created_comment):
        """PUT /api/v1/comments/{id} should persist the update."""
        update_payload = {"content": "Updated comment content"}
        client.put(
            f"/api/v1/comments/{created_comment['id']}", json=update_payload
        )

        get_response = client.get(f"/api/v1/comments/{created_comment['id']}")
        data = get_response.json()
        assert data["content"] == "Updated comment content"

    def test_update_comment_not_found(self, client):
        """PUT /api/v1/comments/{id} should return 404 for a non-existent comment."""
        update_payload = {"content": "Updated content"}
        response = client.put(
            "/api/v1/comments/nonexistent-id", json=update_payload
        )
        assert response.status_code == 404

    def test_update_comment_empty_content(self, client, created_comment):
        """PUT /api/v1/comments/{id} with empty content should return 422."""
        update_payload = {"content": ""}
        response = client.put(
            f"/api/v1/comments/{created_comment['id']}", json=update_payload
        )
        assert response.status_code == 422

    def test_update_comment_partial_update(self, client, created_comment):
        """PUT /api/v1/comments/{id} should allow partial updates (only content)."""
        update_payload = {"content": "Only updating content"}
        response = client.put(
            f"/api/v1/comments/{created_comment['id']}", json=update_payload
        )
        assert response.status_code == 200
        data = response.json()
        # Other fields should remain unchanged
        assert data["post_id"] == created_comment["post_id"]
        assert data["author_id"] == created_comment["author_id"]


# ---------------------------------------------------------------------------
# 5. DELETE /api/v1/comments/{id} — delete
# ---------------------------------------------------------------------------


class TestDeleteComment:
    """Tests for DELETE /api/v1/comments/{id}."""

    def test_delete_comment_returns_204(self, client, created_comment):
        """DELETE /api/v1/comments/{id} should return HTTP 204 on success."""
        response = client.delete(f"/api/v1/comments/{created_comment['id']}")
        assert response.status_code == 204

    def test_delete_comment_removes_comment(self, client, created_comment):
        """DELETE /api/v1/comments/{id} should remove the comment from the store."""
        client.delete(f"/api/v1/comments/{created_comment['id']}")

        get_response = client.get(f"/api/v1/comments/{created_comment['id']}")
        assert get_response.status_code == 404

    def test_delete_comment_not_found(self, client):
        """DELETE /api/v1/comments/{id} should return 404 for a non-existent comment."""
        response = client.delete("/api/v1/comments/nonexistent-id")
        assert response.status_code == 404

    def test_delete_comment_idempotent_behavior(self, client, created_comment):
        """DELETE /api/v1/comments/{id} on an already-deleted comment should return 404."""
        # First delete should succeed
        response1 = client.delete(f"/api/v1/comments/{created_comment['id']}")
        assert response1.status_code == 204

        # Second delete should return 404
        response2 = client.delete(f"/api/v1/comments/{created_comment['id']}")
        assert response2.status_code == 404

    def test_delete_comment_does_not_affect_others(
        self, client, sample_comment_payload
    ):
        """DELETE /api/v1/comments/{id} should only delete the specified comment."""
        # Create two comments
        comment1 = client.post(
            "/api/v1/comments",
            json={**sample_comment_payload, "content": "Comment 1"},
        ).json()
        comment2 = client.post(
            "/api/v1/comments",
            json={**sample_comment_payload, "content": "Comment 2"},
        ).json()

        # Delete the first comment
        client.delete(f"/api/v1/comments/{comment1['id']}")

        # The second comment should still exist
        get_response = client.get(f"/api/v1/comments/{comment2['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["content"] == "Comment 2"
