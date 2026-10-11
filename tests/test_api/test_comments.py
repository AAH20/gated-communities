"""API tests for the Comments endpoints.

Real shipped routes (mounted at ROOT):

    GET  /comments  -> 200 {"data": [...], "total", "page", "page_size", "total_pages"}
    POST /comments  -> 201 CommentResponse

The router (src/gated_communities/api/comments.py) is backed by an in-memory
mock store seeded with 10 comments across post_alpha/post_beta/post_gamma/
post_delta.  ``CommentCreate`` accepts only ``post_id`` and ``content`` (an
optional ``parent_id``); the author is assigned server-side as "user_current".

Endpoint coverage note:

* The shipped router exposes no ``/comments/{id}`` route at all, so
  ``TestGetComment`` / ``TestUpdateComment`` / ``TestDeleteComment`` assert the
  real contract (fail closed: 404/405) rather than success.
"""

import pytest


@pytest.fixture
def sample_comment_payload():
    return {"post_id": "post_alpha", "content": "This is a test comment."}


@pytest.fixture
def created_comment(client, sample_comment_payload):
    response = client.post("/comments", json=sample_comment_payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestListComments:
    """Tests for GET /comments."""

    def test_list_comments_returns_200(self, client):
        response = client.get("/comments")
        assert response.status_code == 200

    def test_list_comments_envelope(self, client):
        """The response is a pagination envelope, not a bare list."""
        response = client.get("/comments")
        data = response.json()
        assert isinstance(data, dict)
        assert {"data", "total", "page", "page_size", "total_pages"}.issubset(data)
        assert isinstance(data["data"], list)

    def test_list_comments_seeded(self, client):
        """The mock store ships with comments."""
        data = client.get("/comments").json()
        assert data["total"] >= 1

    def test_list_comments_page_size_caps_results(self, client):
        response = client.get("/comments", params={"page_size": 3})
        assert response.status_code == 200
        assert len(response.json()["data"]) <= 3

    def test_list_comments_page_param(self, client):
        response = client.get("/comments", params={"page": 2, "page_size": 3})
        assert response.status_code == 200
        assert response.json()["page"] == 2

    def test_list_comments_invalid_page_size(self, client):
        """page_size must be 1..100."""
        assert client.get("/comments", params={"page_size": 0}).status_code == 422

    def test_list_comments_filter_by_post(self, client):
        response = client.get("/comments", params={"post_id": "post_alpha"})
        assert response.status_code == 200
        for comment in response.json()["data"]:
            assert comment["post_id"] == "post_alpha"


class TestCreateComment:
    """Tests for POST /comments."""

    def test_create_comment_returns_201(self, client, sample_comment_payload):
        response = client.post("/comments", json=sample_comment_payload)
        assert response.status_code == 201

    def test_create_comment_returns_created_comment(self, client, sample_comment_payload):
        response = client.post("/comments", json=sample_comment_payload)
        data = response.json()
        assert "id" in data
        assert data["content"] == sample_comment_payload["content"]
        assert data["post_id"] == sample_comment_payload["post_id"]

    def test_create_comment_author_is_server_assigned(self, client, sample_comment_payload):
        data = client.post("/comments", json=sample_comment_payload).json()
        assert data["author_id"] == "user_current"

    def test_create_comment_missing_content(self, client):
        response = client.post("/comments", json={"post_id": "post_alpha"})
        assert response.status_code == 422

    def test_create_comment_missing_post_id(self, client):
        response = client.post("/comments", json={"content": "Test comment"})
        assert response.status_code == 422

    def test_create_comment_empty_content(self, client):
        response = client.post("/comments", json={"post_id": "post_alpha", "content": ""})
        assert response.status_code == 422

    def test_create_comment_unknown_post_returns_404(self, client):
        response = client.post("/comments", json={"post_id": "does-not-exist", "content": "hi"})
        assert response.status_code == 404

    def test_create_comment_persists(self, client, created_comment):
        response = client.get("/comments", params={"page_size": 100})
        ids = [c["id"] for c in response.json()["data"]]
        assert created_comment["id"] in ids


class TestGetComment:
    """GET /comments/{id} is not implemented in the shipped router.

    The router exposes only ``GET /comments`` and ``POST /comments``, so the
    single-comment path is unrouted and must fail closed (404/405) rather than
    appear to succeed.
    """

    def test_get_comment_route_absent(self, client, created_comment):
        response = client.get(f"/comments/{created_comment['id']}")
        assert response.status_code in (404, 405)

    def test_get_comment_unknown_id_route_absent(self, client):
        response = client.get("/comments/does-not-exist")
        assert response.status_code in (404, 405)


class TestUpdateComment:
    """PUT /comments/{id} is not implemented — must fail closed (404/405)."""

    def test_update_comment_route_absent(self, client, created_comment):
        response = client.put(f"/comments/{created_comment['id']}", json={"content": "x"})
        assert response.status_code in (404, 405)


class TestDeleteComment:
    """DELETE /comments/{id} is not implemented — must fail closed (404/405)."""

    def test_delete_comment_route_absent(self, client, created_comment):
        response = client.delete(f"/comments/{created_comment['id']}")
        assert response.status_code in (404, 405)
