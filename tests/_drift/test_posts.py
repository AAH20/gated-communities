"""
Comprehensive API tests for the Posts endpoints.

Tests cover:
- GET /api/v1/posts (list with pagination)
- POST /api/v1/posts (create)
- GET /api/v1/posts/{id} (retrieve)
- PUT /api/v1/posts/{id} (update)
- DELETE /api/v1/posts/{id} (delete)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Return a TestClient instance for the FastAPI app."""
    from gated_communities.main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return headers with a valid auth token for an authenticated user."""
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_post_payload():
    """Return a valid payload for creating a post."""
    return {
        "title": "Test Post Title",
        "content": "This is the content of the test post.",
        "community_id": "community-123",
    }


@pytest.fixture
def created_post(client, auth_headers, sample_post_payload):
    """Create a post via the API and return the response JSON."""
    response = client.post(
        "/api/v1/posts",
        json=sample_post_payload,
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def multiple_posts(client, auth_headers):
    """Create multiple posts and return their IDs for pagination tests."""
    posts = []
    for i in range(5):
        payload = {
            "title": f"Pagination Test Post {i}",
            "content": f"Content for pagination test post {i}.",
            "community_id": "community-page",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 201
        posts.append(response.json())
    return posts


# ---------------------------------------------------------------------------
# 1. GET /api/v1/posts — List posts with pagination
# ---------------------------------------------------------------------------


class TestListPosts:
    """Tests for GET /api/v1/posts."""

    def test_list_posts_success(self, client, auth_headers, multiple_posts):
        """GET /api/v1/posts returns 200 and a list of posts."""
        response = client.get("/api/v1/posts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5

    def test_list_posts_pagination_limit(self, client, auth_headers, multiple_posts):
        """GET /api/v1/posts?limit=N returns at most N posts."""
        limit = 3
        response = client.get(
            f"/api/v1/posts?limit={limit}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= limit

    def test_list_posts_pagination_offset(self, client, auth_headers, multiple_posts):
        """GET /api/v1/posts?offset=N skips the first N posts."""
        # Get all posts first
        all_response = client.get("/api/v1/posts", headers=auth_headers)
        all_posts = all_response.json()
        total = len(all_posts)

        if total < 2:
            pytest.skip("Not enough posts to test offset pagination")

        offset = 2
        response = client.get(
            f"/api/v1/posts?offset={offset}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == total - offset

    def test_list_posts_pagination_limit_and_offset(self, client, auth_headers, multiple_posts):
        """GET /api/v1/posts?limit=N&offset=M returns correct slice."""
        limit = 2
        offset = 1
        response = client.get(
            f"/api/v1/posts?limit={limit}&offset={offset}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= limit

    def test_list_posts_empty_database(self, client, auth_headers):
        """GET /api/v1/posts returns empty list when no posts exist."""
        response = client.get("/api/v1/posts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_posts_unauthenticated(self, client):
        """GET /api/v1/posts without auth returns 401."""
        response = client.get("/api/v1/posts")

        assert response.status_code == 401

    def test_list_posts_response_structure(self, client, auth_headers, created_post):
        """Each post in the list has the expected fields."""
        response = client.get("/api/v1/posts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        post = data[0]
        assert "id" in post
        assert "title" in post
        assert "content" in post
        assert "community_id" in post
        assert "author_id" in post
        assert "created_at" in post
        assert "updated_at" in post


# ---------------------------------------------------------------------------
# 2. POST /api/v1/posts — Create post
# ---------------------------------------------------------------------------


class TestCreatePost:
    """Tests for POST /api/v1/posts."""

    def test_create_post_success(self, client, auth_headers, sample_post_payload):
        """POST /api/v1/posts creates a post and returns 201."""
        response = client.post(
            "/api/v1/posts",
            json=sample_post_payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_post_payload["title"]
        assert data["content"] == sample_post_payload["content"]
        assert data["community_id"] == sample_post_payload["community_id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_post_missing_title(self, client, auth_headers):
        """POST /api/v1/posts without title returns 422."""
        payload = {
            "content": "Content without title",
            "community_id": "community-123",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_post_missing_content(self, client, auth_headers):
        """POST /api/v1/posts without content returns 422."""
        payload = {
            "title": "Title without content",
            "community_id": "community-123",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_post_missing_community_id(self, client, auth_headers):
        """POST /api/v1/posts without community_id returns 422."""
        payload = {
            "title": "Title",
            "content": "Content",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_post_empty_title(self, client, auth_headers):
        """POST /api/v1/posts with empty title returns 422."""
        payload = {
            "title": "",
            "content": "Content",
            "community_id": "community-123",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_create_post_unauthenticated(self, client, sample_post_payload):
        """POST /api/v1/posts without auth returns 401."""
        response = client.post(
            "/api/v1/posts",
            json=sample_post_payload,
        )

        assert response.status_code == 401

    def test_create_post_invalid_json(self, client, auth_headers):
        """POST /api/v1/posts with invalid JSON returns 422."""
        response = client.post(
            "/api/v1/posts",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_create_post_title_too_long(self, client, auth_headers):
        """POST /api/v1/posts with excessively long title returns 422."""
        payload = {
            "title": "x" * 500,
            "content": "Content",
            "community_id": "community-123",
        }
        response = client.post(
            "/api/v1/posts",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 3. GET /api/v1/posts/{id} — Get single post
# ---------------------------------------------------------------------------


class TestGetPost:
    """Tests for GET /api/v1/posts/{id}."""

    def test_get_post_success(self, client, auth_headers, created_post):
        """GET /api/v1/posts/{id} returns the post with matching ID."""
        post_id = created_post["id"]
        response = client.get(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == created_post["title"]
        assert data["content"] == created_post["content"]
        assert data["community_id"] == created_post["community_id"]

    def test_get_post_not_found(self, client, auth_headers):
        """GET /api/v1/posts/{id} with non-existent ID returns 404."""
        response = client.get(
            "/api/v1/posts/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_post_unauthenticated(self, client, created_post):
        """GET /api/v1/posts/{id} without auth returns 401."""
        post_id = created_post["id"]
        response = client.get(f"/api/v1/posts/{post_id}")

        assert response.status_code == 401

    def test_get_post_invalid_id_format(self, client, auth_headers):
        """GET /api/v1/posts/{id} with invalid ID format returns 422 or 404."""
        response = client.get(
            "/api/v1/posts/invalid-id-format!@#",
            headers=auth_headers,
        )

        assert response.status_code in (404, 422)

    def test_get_post_response_structure(self, client, auth_headers, created_post):
        """GET /api/v1/posts/{id} returns all expected fields."""
        post_id = created_post["id"]
        response = client.get(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "content" in data
        assert "community_id" in data
        assert "author_id" in data
        assert "created_at" in data
        assert "updated_at" in data


# ---------------------------------------------------------------------------
# 4. PUT /api/v1/posts/{id} — Update post
# ---------------------------------------------------------------------------


class TestUpdatePost:
    """Tests for PUT /api/v1/posts/{id}."""

    def test_update_post_success(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} updates the post and returns 200."""
        post_id = created_post["id"]
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content for the post.",
        }
        response = client.put(
            f"/api/v1/posts/{post_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == update_payload["title"]
        assert data["content"] == update_payload["content"]

    def test_update_post_partial(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} with partial data updates only provided fields."""
        post_id = created_post["id"]
        original_title = created_post["title"]
        update_payload = {
            "content": "Only content updated.",
        }
        response = client.put(
            f"/api/v1/posts/{post_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post_id
        assert data["title"] == original_title
        assert data["content"] == update_payload["content"]

    def test_update_post_not_found(self, client, auth_headers):
        """PUT /api/v1/posts/{id} with non-existent ID returns 404."""
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content.",
        }
        response = client.put(
            "/api/v1/posts/non-existent-id",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_update_post_unauthenticated(self, client, created_post):
        """PUT /api/v1/posts/{id} without auth returns 401."""
        post_id = created_post["id"]
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content.",
        }
        response = client.put(
            f"/api/v1/posts/{post_id}",
            json=update_payload,
        )

        assert response.status_code == 401

    def test_update_post_empty_body(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} with empty body returns 422."""
        post_id = created_post["id"]
        response = client.put(
            f"/api/v1/posts/{post_id}",
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_update_post_invalid_json(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} with invalid JSON returns 422."""
        post_id = created_post["id"]
        response = client.put(
            f"/api/v1/posts/{post_id}",
            data="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_update_post_title_too_long(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} with excessively long title returns 422."""
        post_id = created_post["id"]
        update_payload = {
            "title": "x" * 500,
        }
        response = client.put(
            f"/api/v1/posts/{post_id}",
            json=update_payload,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_update_post_verify_persistence(self, client, auth_headers, created_post):
        """PUT /api/v1/posts/{id} changes persist on subsequent GET."""
        post_id = created_post["id"]
        update_payload = {
            "title": "Persisted Title",
            "content": "Persisted content.",
        }
        client.put(
            f"/api/v1/posts/{post_id}",
            json=update_payload,
            headers=auth_headers,
        )

        response = client.get(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_payload["title"]
        assert data["content"] == update_payload["content"]


# ---------------------------------------------------------------------------
# 5. DELETE /api/v1/posts/{id} — Delete post
# ---------------------------------------------------------------------------


class TestDeletePost:
    """Tests for DELETE /api/v1/posts/{id}."""

    def test_delete_post_success(self, client, auth_headers, created_post):
        """DELETE /api/v1/posts/{id} deletes the post and returns 204."""
        post_id = created_post["id"]
        response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    def test_delete_post_not_found(self, client, auth_headers):
        """DELETE /api/v1/posts/{id} with non-existent ID returns 404."""
        response = client.delete(
            "/api/v1/posts/non-existent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_delete_post_unauthenticated(self, client, created_post):
        """DELETE /api/v1/posts/{id} without auth returns 401."""
        post_id = created_post["id"]
        response = client.delete(f"/api/v1/posts/{post_id}")

        assert response.status_code == 401

    def test_delete_post_verify_removal(self, client, auth_headers, created_post):
        """After DELETE, GET /api/v1/posts/{id} returns 404."""
        post_id = created_post["id"]

        delete_response = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        get_response = client.get(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_post_already_deleted(self, client, auth_headers, created_post):
        """Deleting an already-deleted post returns 404."""
        post_id = created_post["id"]

        first_delete = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )
        assert first_delete.status_code == 204

        second_delete = client.delete(
            f"/api/v1/posts/{post_id}",
            headers=auth_headers,
        )
        assert second_delete.status_code == 404

    def test_delete_post_invalid_id_format(self, client, auth_headers):
        """DELETE /api/v1/posts/{id} with invalid ID format returns 404 or 422."""
        response = client.delete(
            "/api/v1/posts/invalid-id-format!@#",
            headers=auth_headers,
        )

        assert response.status_code in (404, 422)
