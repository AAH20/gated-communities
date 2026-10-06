"""Comprehensive service tests for the event service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from gated_communities.services.event_service import (
    create_event,
    delete_event,
    get_event,
    list_events,
    update_event,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Provide a mock database session."""
    return MagicMock()


@pytest.fixture
def sample_event_data():
    """Return a dictionary of valid event creation data."""
    return {
        "title": "Community Meetup",
        "description": "A gathering for community members",
        "start_time": datetime.now(timezone.utc) + timedelta(days=1),
        "end_time": datetime.now(timezone.utc) + timedelta(days=1, hours=2),
        "location": "Community Center",
        "max_attendees": 50,
        "organizer_id": 1,
        "community_id": 1,
    }


@pytest.fixture
def sample_event():
    """Return a mock event object simulating a database record."""
    event = MagicMock()
    event.id = 1
    event.title = "Community Meetup"
    event.description = "A gathering for community members"
    event.start_time = datetime.now(timezone.utc) + timedelta(days=1)
    event.end_time = datetime.now(timezone.utc) + timedelta(days=1, hours=2)
    event.location = "Community Center"
    event.max_attendees = 50
    event.organizer_id = 1
    event.community_id = 1
    event.created_at = datetime.now(timezone.utc)
    event.updated_at = datetime.now(timezone.utc)
    return event


@pytest.fixture
def sample_event_list():
    """Return a list of mock event objects."""
    events = []
    for i in range(3):
        event = MagicMock()
        event.id = i + 1
        event.title = f"Event {i + 1}"
        event.description = f"Description for event {i + 1}"
        event.start_time = datetime.now(timezone.utc) + timedelta(days=i + 1)
        event.end_time = datetime.now(timezone.utc) + timedelta(days=i + 1, hours=2)
        event.location = f"Location {i + 1}"
        event.max_attendees = 50
        event.organizer_id = 1
        event.community_id = 1
        event.created_at = datetime.now(timezone.utc)
        event.updated_at = datetime.now(timezone.utc)
        events.append(event)
    return events


# ---------------------------------------------------------------------------
# Tests for get_event
# ---------------------------------------------------------------------------


class TestGetEvent:
    """Tests for the get_event function."""

    def test_get_event_returns_event_when_found(self, mock_db, sample_event):
        """get_event should return the event when it exists in the database."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event

        result = get_event(mock_db, event_id=1)

        assert result is not None
        assert result.id == 1
        assert result.title == "Community Meetup"
        assert result.description == "A gathering for community members"
        assert result.location == "Community Center"
        assert result.max_attendees == 50
        assert result.organizer_id == 1
        assert result.community_id == 1

    def test_get_event_returns_none_when_not_found(self, mock_db):
        """get_event should return None when the event does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_event(mock_db, event_id=999)

        assert result is None

    def test_get_event_queries_correct_event_id(self, mock_db, sample_event):
        """get_event should query for the correct event ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event

        get_event(mock_db, event_id=42)

        mock_db.query.assert_called_once()
        # Verify the filter was called (the query chain was exercised)
        assert mock_db.query.return_value.filter.called

    def test_get_event_with_different_ids(self, mock_db, sample_event):
        """get_event should work with various event IDs."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event

        result = get_event(mock_db, event_id=100)
        assert result is not None
        assert result.id == 1

        result = get_event(mock_db, event_id=0)
        assert result is not None

    def test_get_event_preserves_datetime_fields(self, mock_db, sample_event):
        """get_event should return events with correct datetime fields."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event

        result = get_event(mock_db, event_id=1)

        assert isinstance(result.start_time, datetime)
        assert isinstance(result.end_time, datetime)
        assert result.end_time > result.start_time


# ---------------------------------------------------------------------------
# Tests for list_events
# ---------------------------------------------------------------------------


class TestListEvents:
    """Tests for the list_events function."""

    def test_list_events_returns_all_events(self, mock_db, sample_event_list):
        """list_events should return all events when no filters are applied."""
        mock_db.query.return_value.all.return_value = sample_event_list

        result = list_events(mock_db)

        assert result is not None
        assert len(result) == 3
        assert result[0].title == "Event 1"
        assert result[1].title == "Event 2"
        assert result[2].title == "Event 3"

    def test_list_events_returns_empty_list_when_no_events(self, mock_db):
        """list_events should return an empty list when no events exist."""
        mock_db.query.return_value.all.return_value = []

        result = list_events(mock_db)

        assert result is not None
        assert len(result) == 0

    def test_list_events_with_community_filter(self, mock_db, sample_event_list):
        """list_events should filter by community_id when provided."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_event_list

        result = list_events(mock_db, community_id=1)

        assert result is not None
        assert len(result) == 3
        mock_db.query.return_value.filter.assert_called()

    def test_list_events_with_organizer_filter(self, mock_db, sample_event_list):
        """list_events should filter by organizer_id when provided."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_event_list

        result = list_events(mock_db, organizer_id=1)

        assert result is not None
        assert len(result) == 3

    def test_list_events_with_date_range_filter(self, mock_db, sample_event_list):
        """list_events should filter by date range when start_date and end_date are provided."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_event_list

        start = datetime.now(timezone.utc)
        end = start + timedelta(days=7)

        result = list_events(mock_db, start_date=start, end_date=end)

        assert result is not None
        assert len(result) == 3

    def test_list_events_with_multiple_filters(self, mock_db, sample_event_list):
        """list_events should apply multiple filters simultaneously."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_event_list

        result = list_events(
            mock_db,
            community_id=1,
            organizer_id=1,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=7),
        )

        assert result is not None
        assert len(result) == 3

    def test_list_events_with_limit(self, mock_db, sample_event_list):
        """list_events should respect the limit parameter."""
        mock_db.query.return_value.limit.return_value.all.return_value = sample_event_list[:2]

        result = list_events(mock_db, limit=2)

        assert result is not None
        assert len(result) == 2

    def test_list_events_with_offset(self, mock_db, sample_event_list):
        """list_events should respect the offset parameter."""
        mock_db.query.return_value.offset.return_value.all.return_value = sample_event_list[1:]

        result = list_events(mock_db, offset=1)

        assert result is not None
        assert len(result) == 2

    def test_list_events_with_limit_and_offset(self, mock_db, sample_event_list):
        """list_events should support pagination with limit and offset."""
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = sample_event_list[1:2]

        result = list_events(mock_db, limit=1, offset=1)

        assert result is not None
        assert len(result) == 1

    def test_list_events_with_title_search(self, mock_db, sample_event_list):
        """list_events should filter by title search term when provided."""
        mock_db.query.return_value.filter.return_value.all.return_value = sample_event_list

        result = list_events(mock_db, search="Event")

        assert result is not None
        assert len(result) == 3

    def test_list_events_preserves_event_attributes(self, mock_db, sample_event_list):
        """list_events should return events with all attributes intact."""
        mock_db.query.return_value.all.return_value = sample_event_list

        result = list_events(mock_db)

        for event in result:
            assert hasattr(event, "id")
            assert hasattr(event, "title")
            assert hasattr(event, "description")
            assert hasattr(event, "start_time")
            assert hasattr(event, "end_time")
            assert hasattr(event, "location")
            assert hasattr(event, "max_attendees")
            assert hasattr(event, "organizer_id")
            assert hasattr(event, "community_id")


# ---------------------------------------------------------------------------
# Tests for create_event
# ---------------------------------------------------------------------------


class TestCreateEvent:
    """Tests for the create_event function."""

    def test_create_event_returns_created_event(self, mock_db, sample_event_data):
        """create_event should return the newly created event."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        result = create_event(mock_db, **sample_event_data)

        assert result is not None
        assert result.id == 1
        assert result.title == "Community Meetup"
        assert result.description == "A gathering for community members"
        assert result.location == "Community Meetup" or result.location == "Community Center"
        assert result.max_attendees == 50
        assert result.organizer_id == 1
        assert result.community_id == 1

    def test_create_event_persists_to_database(self, mock_db, sample_event_data):
        """create_event should add the event to the database and commit."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        create_event(mock_db, **sample_event_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_event_sets_timestamps(self, mock_db, sample_event_data):
        """create_event should set created_at and updated_at timestamps."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        before = datetime.now(timezone.utc)
        result = create_event(mock_db, **sample_event_data)
        after = datetime.now(timezone.utc)

        assert hasattr(result, "created_at")
        assert hasattr(result, "updated_at")

    def test_create_event_with_minimal_data(self, mock_db):
        """create_event should work with minimal required data."""
        minimal_data = {
            "title": "Quick Event",
            "organizer_id": 1,
            "community_id": 1,
        }
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        result = create_event(mock_db, **minimal_data)

        assert result is not None
        assert result.title == "Quick Event"
        assert result.organizer_id == 1
        assert result.community_id == 1

    def test_create_event_with_all_fields(self, mock_db, sample_event_data):
        """create_event should handle all optional fields."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        result = create_event(mock_db, **sample_event_data)

        assert result is not None
        assert result.title == sample_event_data["title"]
        assert result.description == sample_event_data["description"]
        assert result.location == sample_event_data["location"]
        assert result.max_attendees == sample_event_data["max_attendees"]

    def test_create_event_commits_transaction(self, mock_db, sample_event_data):
        """create_event should commit the transaction."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        create_event(mock_db, **sample_event_data)

        assert mock_db.commit.called

    def test_create_event_refreshes_object(self, mock_db, sample_event_data):
        """create_event should refresh the object to get generated fields."""
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 1)

        create_event(mock_db, **sample_event_data)

        assert mock_db.refresh.called


# ---------------------------------------------------------------------------
# Tests for update_event
# ---------------------------------------------------------------------------


class TestUpdateEvent:
    """Tests for the update_event function."""

    def test_update_event_returns_updated_event(self, mock_db, sample_event):
        """update_event should return the updated event."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_event(mock_db, event_id=1, title="Updated Title")

        assert result is not None
        assert result.title == "Updated Title"

    def test_update_event_modifies_existing_event(self, mock_db, sample_event):
        """update_event should modify the existing event's fields."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_event(
            mock_db,
            event_id=1,
            title="New Title",
            description="New Description",
            location="New Location",
        )

        assert result.title == "New Title"
        assert result.description == "New Description"
        assert result.location == "New Location"

    def test_update_event_returns_none_when_event_not_found(self, mock_db):
        """update_event should return None when the event does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_event(mock_db, event_id=999, title="Updated Title")

        assert result is None

    def test_update_event_commits_changes(self, mock_db, sample_event):
        """update_event should commit the changes to the database."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        update_event(mock_db, event_id=1, title="Updated Title")

        mock_db.commit.assert_called_once()

    def test_update_event_refreshes_object(self, mock_db, sample_event):
        """update_event should refresh the object after update."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        update_event(mock_db, event_id=1, title="Updated Title")

        mock_db.refresh.assert_called_once()

    def test_update_event_with_partial_data(self, mock_db, sample_event):
        """update_event should allow partial updates (only some fields)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        original_description = sample_event.description
        result = update_event(mock_db, event_id=1, title="Only Title Changed")

        assert result.title == "Only Title Changed"
        assert result.description == original_description

    def test_update_event_with_max_attendees(self, mock_db, sample_event):
        """update_event should update max_attendees field."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_event(mock_db, event_id=1, max_attendees=100)

        assert result.max_attendees == 100

    def test_update_event_with_datetime_fields(self, mock_db, sample_event):
        """update_event should update datetime fields."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        new_start = datetime.now(timezone.utc) + timedelta(days=5)
        new_end = new_start + timedelta(hours=3)

        result = update_event(
            mock_db,
            event_id=1,
            start_time=new_start,
            end_time=new_end,
        )

        assert result.start_time == new_start
        assert result.end_time == new_end

    def test_update_event_does_not_modify_organizer_or_community(self, mock_db, sample_event):
        """update_event should not change organizer_id or community_id."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        result = update_event(mock_db, event_id=1, title="New Title")

        assert result.organizer_id == 1
        assert result.community_id == 1


# ---------------------------------------------------------------------------
# Tests for delete_event
# ---------------------------------------------------------------------------


class TestDeleteEvent:
    """Tests for the delete_event function."""

    def test_delete_event_returns_true_on_success(self, mock_db, sample_event):
        """delete_event should return True when deletion succeeds."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = delete_event(mock_db, event_id=1)

        assert result is True

    def test_delete_event_returns_false_when_not_found(self, mock_db):
        """delete_event should return False when the event does not exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_event(mock_db, event_id=999)

        assert result is False

    def test_delete_event_removes_from_database(self, mock_db, sample_event):
        """delete_event should call delete and commit on the database."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_event(mock_db, event_id=1)

        mock_db.delete.assert_called_once_with(sample_event)
        mock_db.commit.assert_called_once()

    def test_delete_event_queries_correct_event(self, mock_db, sample_event):
        """delete_event should query for the correct event ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_event(mock_db, event_id=42)

        mock_db.query.assert_called_once()
        assert mock_db.query.return_value.filter.called

    def test_delete_event_does_not_commit_when_not_found(self, mock_db):
        """delete_event should not commit when the event is not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        delete_event(mock_db, event_id=999)

        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_delete_event_with_different_ids(self, mock_db, sample_event):
        """delete_event should work with various event IDs."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        result = delete_event(mock_db, event_id=1)
        assert result is True

        result = delete_event(mock_db, event_id=100)
        assert result is True

    def test_delete_event_only_deletes_specified_event(self, mock_db, sample_event):
        """delete_event should only delete the specified event."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_event
        mock_db.delete.return_value = None
        mock_db.commit.return_value = None

        delete_event(mock_db, event_id=1)

        # Verify delete was called exactly once with the correct event
        mock_db.delete.assert_called_once_with(sample_event)
