"""
Comprehensive API tests for the Events endpoints.

Tests cover:
- GET    /events        (list events with pagination and filtering)
- POST   /events        (create event with validation)
- GET    /events/{id}   (get single event)
- PUT    /events/{id}   (update event)
- DELETE /events/{id}   (delete event)
"""

import pytest
from datetime import date, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to a FastAPI app with the events router."""
    from gated_communities.api.events import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def sample_event_payload():
    """Return a valid payload for creating an event."""
    return {
        "title": "Community Meetup",
        "description": "Monthly community gathering for members to connect and share ideas.",
        "community_id": 1,
        "start_date": "2026-11-15",
        "end_date": "2026-11-16",
        "location": "Community Hall, 123 Main St",
        "max_attendees": 50,
        "is_public": True,
    }


@pytest.fixture
def created_event(client, sample_event_payload):
    """Create an event and return the response JSON."""
    response = client.post("/events", json=sample_event_payload)
    assert response.status_code == 201, f"Setup failed: {response.text}"
    return response.json()


# ---------------------------------------------------------------------------
# 1. test_list_events — GET /events
# ---------------------------------------------------------------------------

class TestListEvents:
    """Tests for GET /events."""

    def test_list_events_returns_paginated_response(self, client):
        """GET /events returns 200 with a paginated response structure."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data

    def test_list_events_default_pagination(self, client):
        """GET /events with default params returns page 1 with 20 items per page."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_events_pagination_page(self, client, sample_event_payload):
        """GET /events?page=2 returns the second page."""
        # Create enough events to have multiple pages
        for i in range(25):
            payload = {**sample_event_payload, "title": f"Event {i}"}
            client.post("/events", json=payload)

        response = client.get("/events?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 10
        assert len(data["items"]) <= 10

    def test_list_events_pagination_page_size(self, client, sample_event_payload):
        """GET /events?page_size=5 returns at most 5 items."""
        for i in range(10):
            payload = {**sample_event_payload, "title": f"Event {i}"}
            client.post("/events", json=payload)

        response = client.get("/events?page_size=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 5

    def test_list_events_filter_by_community(self, client, sample_event_payload):
        """GET /events?community_id=1 returns only events for that community."""
        client.post("/events", json={**sample_event_payload, "community_id": 1})
        client.post("/events", json={**sample_event_payload, "community_id": 2})

        response = client.get("/events?community_id=1")

        assert response.status_code == 200
        data = response.json()
        for event in data["items"]:
            assert event["community_id"] == 1

    def test_list_events_filter_by_public(self, client, sample_event_payload):
        """GET /events?is_public=true returns only public events."""
        client.post("/events", json={**sample_event_payload, "is_public": True})
        client.post("/events", json={**sample_event_payload, "is_public": False})

        response = client.get("/events?is_public=true")

        assert response.status_code == 200
        data = response.json()
        for event in data["items"]:
            assert event["is_public"] is True

    def test_list_events_filter_by_date_range(self, client, sample_event_payload):
        """GET /events with start_after and start_before filters by date."""
        today = date.today().isoformat()
        future = (date.today() + timedelta(days=30)).isoformat()

        response = client.get(f"/events?start_after={today}&start_before={future}")

        assert response.status_code == 200
        data = response.json()
        for event in data["items"]:
            assert event["start_date"] >= today
            assert event["start_date"] <= future

    def test_list_events_total_count(self, client, sample_event_payload):
        """GET /events returns correct total count."""
        for i in range(3):
            payload = {**sample_event_payload, "title": f"Event {i}"}
            client.post("/events", json=payload)

        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3

    def test_list_events_response_structure(self, client, created_event):
        """Each event in the list has the expected fields."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

        event = data["items"][0]
        expected_fields = {
            "id",
            "title",
            "description",
            "community_id",
            "start_date",
            "end_date",
            "location",
            "max_attendees",
            "attendee_count",
            "is_public",
            "created_at",
            "updated_at",
        }
        assert expected_fields.issubset(event.keys())

    def test_list_events_content_type(self, client):
        """GET /events returns application/json content type."""
        response = client.get("/events")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 2. test_create_event — POST /events
# ---------------------------------------------------------------------------

class TestCreateEvent:
    """Tests for POST /events."""

    def test_create_event_success(self, client, sample_event_payload):
        """POST /events with valid payload returns 201 and the created event."""
        response = client.post("/events", json=sample_event_payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == sample_event_payload["title"]
        assert data["description"] == sample_event_payload["description"]
        assert data["community_id"] == sample_event_payload["community_id"]
        assert data["start_date"] == sample_event_payload["start_date"]
        assert data["end_date"] == sample_event_payload["end_date"]
        assert data["location"] == sample_event_payload["location"]
        assert data["max_attendees"] == sample_event_payload["max_attendees"]
        assert data["is_public"] == sample_event_payload["is_public"]
        assert data["attendee_count"] == 0

    def test_create_event_minimal_payload(self, client):
        """POST /events with only required fields succeeds."""
        payload = {
            "title": "Quick Sync",
            "description": "A quick sync meeting.",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Quick Sync"
        assert "id" in data

    def test_create_event_missing_title(self, client):
        """POST /events without a title returns 422."""
        payload = {
            "description": "Event without a title",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_missing_description(self, client):
        """POST /events without a description returns 422."""
        payload = {
            "title": "Event Without Description",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_missing_community_id(self, client):
        """POST /events without a community_id returns 422."""
        payload = {
            "title": "Event Without Community",
            "description": "This event has no community.",
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_missing_start_date(self, client):
        """POST /events without a start_date returns 422."""
        payload = {
            "title": "Event Without Date",
            "description": "This event has no start date.",
            "community_id": 1,
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_empty_body(self, client):
        """POST /events with an empty JSON body returns 422."""
        response = client.post("/events", json={})

        assert response.status_code == 422

    def test_create_event_invalid_date_format(self, client):
        """POST /events with an unparseable date returns 422."""
        payload = {
            "title": "Bad Date Event",
            "description": "This event has an invalid date.",
            "community_id": 1,
            "start_date": "not-a-date",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_negative_community_id(self, client):
        """POST /events with negative community_id returns 422."""
        payload = {
            "title": "Invalid Community",
            "description": "This event has an invalid community ID.",
            "community_id": -1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_zero_community_id(self, client):
        """POST /events with zero community_id returns 422."""
        payload = {
            "title": "Invalid Community",
            "description": "This event has an invalid community ID.",
            "community_id": 0,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_negative_max_attendees(self, client):
        """POST /events with negative max_attendees returns 422."""
        payload = {
            "title": "Impossible Event",
            "description": "This event has negative max attendees.",
            "community_id": 1,
            "start_date": "2026-11-15",
            "max_attendees": -1,
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_zero_max_attendees(self, client):
        """POST /events with zero max_attendees returns 422."""
        payload = {
            "title": "Impossible Event",
            "description": "This event has zero max attendees.",
            "community_id": 1,
            "start_date": "2026-11-15",
            "max_attendees": 0,
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_end_date_before_start_date(self, client):
        """POST /events with end_date before start_date returns 422."""
        payload = {
            "title": "Time Travel Event",
            "description": "This event ends before it starts.",
            "community_id": 1,
            "start_date": "2026-11-15",
            "end_date": "2026-11-14",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_title_too_short(self, client):
        """POST /events with title shorter than 3 chars returns 422."""
        payload = {
            "title": "AB",
            "description": "This event has a very short title.",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_title_too_long(self, client):
        """POST /events with title longer than 200 chars returns 422."""
        payload = {
            "title": "A" * 201,
            "description": "This event has a very long title.",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_description_too_short(self, client):
        """POST /events with description shorter than 10 chars returns 422."""
        payload = {
            "title": "Short Description",
            "description": "Short",
            "community_id": 1,
            "start_date": "2026-11-15",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_wrong_content_type(self, client):
        """POST /events with non-JSON content type returns 415 or 422."""
        response = client.post(
            "/events",
            data="title=Hello",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code in (415, 422)

    def test_create_event_response_has_timestamps(self, client, sample_event_payload):
        """Created event response includes created_at and updated_at timestamps."""
        response = client.post("/events", json=sample_event_payload)

        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_event_content_type(self, client, sample_event_payload):
        """POST /events returns application/json content type."""
        response = client.post("/events", json=sample_event_payload)

        assert response.status_code == 201
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 3. test_get_event — GET /events/{id}
# ---------------------------------------------------------------------------

class TestGetEvent:
    """Tests for GET /events/{id}."""

    def test_get_event_not_found(self, client):
        """GET /events/{id} with non-existent id returns 404."""
        response = client.get("/events/999999")

        assert response.status_code == 404

    def test_get_event_invalid_id_format(self, client):
        """GET /events/{id} with non-integer id returns 404 (route not found)."""
        response = client.get("/events/not-a-number")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 4. test_update_event — PUT /events/{id}
# ---------------------------------------------------------------------------

class TestUpdateEvent:
    """Tests for PUT /events/{id}."""

    def test_update_event_not_found(self, client):
        """PUT /events/{id} with non-existent id returns 404."""
        payload = {"title": "Updated Title"}
        response = client.put("/events/999999", json=payload)

        assert response.status_code == 404

    def test_update_event_invalid_id_format(self, client):
        """PUT /events/{id} with non-integer id returns 404 (route not found)."""
        payload = {"title": "Updated Title"}
        response = client.put("/events/not-a-number", json=payload)

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 5. test_delete_event — DELETE /events/{id}
# ---------------------------------------------------------------------------

class TestDeleteEvent:
    """Tests for DELETE /events/{id}."""

    def test_delete_event_not_found(self, client):
        """DELETE /events/{id} with non-existent id returns 404."""
        response = client.delete("/events/999999")

        assert response.status_code == 404

    def test_delete_event_invalid_id_format(self, client):
        """DELETE /events/{id} with non-integer id returns 404 (route not found)."""
        response = client.delete("/events/not-a-number")

        assert response.status_code == 404
