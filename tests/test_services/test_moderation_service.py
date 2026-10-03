"""Tests for the Moderation Service."""

import pytest
from datetime import datetime, timezone

from gated_communities.services.moderation_service import (
    ModerationError,
    ModerationItemNotFoundError,
    ModerationItemAlreadyResolvedError,
    InvalidModerationDecisionError,
    get_moderation_item,
    list_moderation_items,
    create_moderation_item,
    resolve_moderation_item,
    delete_moderation_item,
    _moderation_store,
)


@pytest.fixture(autouse=True)
def clear_moderation_store():
    """Clear the in-memory moderation store before and after each test."""
    _moderation_store.clear()
    yield
    _moderation_store.clear()


@pytest.fixture
def sample_moderation_data():
    """Provide valid data for creating a moderation item."""
    return {
        "community_id": "comm-001",
        "reporter_id": "user-001",
        "target_type": "post",
        "target_id": "post-001",
        "reason": "spam",
    }


@pytest.fixture
def created_moderation_item(sample_moderation_data):
    """Create and return a moderation item for testing."""
    return create_moderation_item(sample_moderation_data)


# ---------------------------------------------------------------------------
# get_moderation_item
# ---------------------------------------------------------------------------


class TestGetModerationItem:
    """Test suite for get_moderation_item."""

    def test_get_moderation_item_success(self, created_moderation_item):
        """Test retrieving an existing moderation item by ID."""
        item_id = created_moderation_item["id"]
        result = get_moderation_item(item_id)

        assert result is not None
        assert result["id"] == item_id
        assert result["community_id"] == "comm-001"
        assert result["reporter_id"] == "user-001"
        assert result["target_type"] == "post"
        assert result["target_id"] == "post-001"
        assert result["reason"] == "spam"
        assert result["status"] == "pending"
        assert result["decision"] is None
        assert result["moderator_id"] is None
        assert result["resolved_at"] is None
        assert "created_at" in result
        assert "metadata" in result

    def test_get_moderation_item_not_found(self):
        """Test retrieving a non-existent moderation item raises error."""
        with pytest.raises(ModerationItemNotFoundError) as exc_info:
            get_moderation_item("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)
        assert "not found" in str(exc_info.value)

    def test_get_moderation_item_empty_id(self):
        """Test that empty string ID raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            get_moderation_item("")

    def test_get_moderation_item_none_id(self):
        """Test that None ID raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            get_moderation_item(None)

    def test_get_moderation_item_non_string_id(self):
        """Test that non-string ID raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            get_moderation_item(123)

    def test_get_moderation_item_returns_copy(self, created_moderation_item):
        """Test that returned item is a copy, not the original reference."""
        item_id = created_moderation_item["id"]
        result = get_moderation_item(item_id)

        # Mutating the returned dict should not affect the store
        result["status"] = "modified"
        fresh = get_moderation_item(item_id)
        assert fresh["status"] == "pending"


# ---------------------------------------------------------------------------
# list_moderation_items
# ---------------------------------------------------------------------------


class TestListModerationItems:
    """Test suite for list_moderation_items."""

    def test_list_moderation_items_empty(self):
        """Test listing when no items exist."""
        result = list_moderation_items(filters={}, page=1, page_size=10)
        assert result == []

    def test_list_moderation_items_single(self, created_moderation_item):
        """Test listing with a single item."""
        result = list_moderation_items(filters={}, page=1, page_size=10)
        assert len(result) == 1
        assert result[0]["id"] == created_moderation_item["id"]

    def test_list_moderation_items_multiple(self, sample_moderation_data):
        """Test listing with multiple items."""
        for i in range(5):
            data = {**sample_moderation_data, "reason": f"reason-{i}"}
            create_moderation_item(data)

        result = list_moderation_items(filters={}, page=1, page_size=10)
        assert len(result) == 5

    def test_list_moderation_items_with_status_filter(self, sample_moderation_data):
        """Test filtering by status."""
        # Create pending items
        item1 = create_moderation_item({**sample_moderation_data, "reason": "spam"})
        item2 = create_moderation_item({**sample_moderation_data, "reason": "abuse"})

        # Resolve one item
        resolve_moderation_item(item1["id"], "approve")

        # Filter by pending
        pending = list_moderation_items(filters={"status": "pending"}, page=1, page_size=10)
        assert len(pending) == 1
        assert pending[0]["id"] == item2["id"]

        # Filter by resolved
        resolved = list_moderation_items(filters={"status": "resolved"}, page=1, page_size=10)
        assert len(resolved) == 1
        assert resolved[0]["id"] == item1["id"]

    def test_list_moderation_items_with_community_filter(self, sample_moderation_data):
        """Test filtering by community_id."""
        create_moderation_item({**sample_moderation_data, "community_id": "comm-001"})
        create_moderation_item({**sample_moderation_data, "community_id": "comm-002"})
        create_moderation_item({**sample_moderation_data, "community_id": "comm-001"})

        result = list_moderation_items(filters={"community_id": "comm-001"}, page=1, page_size=10)
        assert len(result) == 2
        assert all(item["community_id"] == "comm-001" for item in result)

    def test_list_moderation_items_with_target_type_filter(self, sample_moderation_data):
        """Test filtering by target_type."""
        create_moderation_item({**sample_moderation_data, "target_type": "post"})
        create_moderation_item({**sample_moderation_data, "target_type": "comment"})
        create_moderation_item({**sample_moderation_data, "target_type": "post"})

        result = list_moderation_items(filters={"target_type": "post"}, page=1, page_size=10)
        assert len(result) == 2
        assert all(item["target_type"] == "post" for item in result)

    def test_list_moderation_items_with_multiple_filters(self, sample_moderation_data):
        """Test filtering by multiple criteria simultaneously."""
        create_moderation_item({
            **sample_moderation_data,
            "community_id": "comm-001",
            "target_type": "post",
        })
        create_moderation_item({
            **sample_moderation_data,
            "community_id": "comm-001",
            "target_type": "comment",
        })
        create_moderation_item({
            **sample_moderation_data,
            "community_id": "comm-002",
            "target_type": "post",
        })

        result = list_moderation_items(
            filters={"community_id": "comm-001", "target_type": "post"},
            page=1,
            page_size=10,
        )
        assert len(result) == 1
        assert result[0]["community_id"] == "comm-001"
        assert result[0]["target_type"] == "post"

    def test_list_moderation_items_pagination(self, sample_moderation_data):
        """Test pagination with page and page_size."""
        for i in range(10):
            create_moderation_item({**sample_moderation_data, "reason": f"reason-{i}"})

        # Page 1, size 3
        page1 = list_moderation_items(filters={}, page=1, page_size=3)
        assert len(page1) == 3

        # Page 2, size 3
        page2 = list_moderation_items(filters={}, page=2, page_size=3)
        assert len(page2) == 3

        # Page 4, size 3 (only 1 item left)
        page4 = list_moderation_items(filters={}, page=4, page_size=3)
        assert len(page4) == 1

        # Page 5, size 3 (no items left)
        page5 = list_moderation_items(filters={}, page=5, page_size=3)
        assert len(page5) == 0

    def test_list_moderation_items_sorted_by_created_at_desc(self, sample_moderation_data):
        """Test that items are sorted by created_at descending (newest first)."""
        item1 = create_moderation_item({**sample_moderation_data, "reason": "first"})
        item2 = create_moderation_item({**sample_moderation_data, "reason": "second"})
        item3 = create_moderation_item({**sample_moderation_data, "reason": "third"})

        result = list_moderation_items(filters={}, page=1, page_size=10)
        assert len(result) == 3
        # Newest first
        assert result[0]["id"] == item3["id"]
        assert result[1]["id"] == item2["id"]
        assert result[2]["id"] == item1["id"]

    def test_list_moderation_items_invalid_page(self):
        """Test that invalid page number raises ValueError."""
        with pytest.raises(ValueError, match="page must be a positive integer"):
            list_moderation_items(filters={}, page=0, page_size=10)

    def test_list_moderation_items_negative_page(self):
        """Test that negative page number raises ValueError."""
        with pytest.raises(ValueError, match="page must be a positive integer"):
            list_moderation_items(filters={}, page=-1, page_size=10)

    def test_list_moderation_items_invalid_page_size(self):
        """Test that invalid page_size raises ValueError."""
        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            list_moderation_items(filters={}, page=1, page_size=0)

    def test_list_moderation_items_negative_page_size(self):
        """Test that negative page_size raises ValueError."""
        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            list_moderation_items(filters={}, page=1, page_size=-5)

    def test_list_moderation_items_non_dict_filters(self):
        """Test that non-dict filters raises ValueError."""
        with pytest.raises(ValueError, match="filters must be a dictionary"):
            list_moderation_items(filters="invalid", page=1, page_size=10)

    def test_list_moderation_items_non_int_page(self):
        """Test that non-integer page raises ValueError."""
        with pytest.raises(ValueError, match="page must be a positive integer"):
            list_moderation_items(filters={}, page="1", page_size=10)

    def test_list_moderation_items_non_int_page_size(self):
        """Test that non-integer page_size raises ValueError."""
        with pytest.raises(ValueError, match="page_size must be a positive integer"):
            list_moderation_items(filters={}, page=1, page_size="10")


# ---------------------------------------------------------------------------
# create_moderation_item
# ---------------------------------------------------------------------------


class TestCreateModerationItem:
    """Test suite for create_moderation_item."""

    def test_create_moderation_item_success(self, sample_moderation_data):
        """Test creating a moderation item with valid data."""
        result = create_moderation_item(sample_moderation_data)

        assert result is not None
        assert "id" in result
        assert result["id"]  # non-empty
        assert result["community_id"] == "comm-001"
        assert result["reporter_id"] == "user-001"
        assert result["target_type"] == "post"
        assert result["target_id"] == "post-001"
        assert result["reason"] == "spam"
        assert result["status"] == "pending"
        assert result["decision"] is None
        assert result["moderator_id"] is None
        assert result["resolved_at"] is None
        assert "created_at" in result
        assert result["metadata"] == {}

    def test_create_moderation_item_with_metadata(self, sample_moderation_data):
        """Test creating a moderation item with custom metadata."""
        data = {**sample_moderation_data, "metadata": {"priority": "high", "tags": ["spam", "urgent"]}}
        result = create_moderation_item(data)

        assert result["metadata"] == {"priority": "high", "tags": ["spam", "urgent"]}

    def test_create_moderation_item_generates_unique_ids(self, sample_moderation_data):
        """Test that each created item gets a unique ID."""
        item1 = create_moderation_item(sample_moderation_data)
        item2 = create_moderation_item(sample_moderation_data)

        assert item1["id"] != item2["id"]

    def test_create_moderation_item_stores_in_store(self, sample_moderation_data):
        """Test that created item is stored and retrievable."""
        result = create_moderation_item(sample_moderation_data)
        stored = get_moderation_item(result["id"])

        assert stored["id"] == result["id"]
        assert stored["community_id"] == result["community_id"]

    def test_create_moderation_item_empty_data(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="data must be a non-empty dictionary"):
            create_moderation_item({})

    def test_create_moderation_item_none_data(self):
        """Test that None data raises ValueError."""
        with pytest.raises(ValueError, match="data must be a non-empty dictionary"):
            create_moderation_item(None)

    def test_create_moderation_item_non_dict_data(self):
        """Test that non-dict data raises ValueError."""
        with pytest.raises(ValueError, match="data must be a non-empty dictionary"):
            create_moderation_item("invalid")

    def test_create_moderation_item_missing_community_id(self, sample_moderation_data):
        """Test that missing community_id raises ValueError."""
        del sample_moderation_data["community_id"]
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_missing_reporter_id(self, sample_moderation_data):
        """Test that missing reporter_id raises ValueError."""
        del sample_moderation_data["reporter_id"]
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_missing_target_type(self, sample_moderation_data):
        """Test that missing target_type raises ValueError."""
        del sample_moderation_data["target_type"]
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_missing_target_id(self, sample_moderation_data):
        """Test that missing target_id raises ValueError."""
        del sample_moderation_data["target_id"]
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_missing_reason(self, sample_moderation_data):
        """Test that missing reason raises ValueError."""
        del sample_moderation_data["reason"]
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_empty_string_fields(self, sample_moderation_data):
        """Test that empty string required fields raise ValueError."""
        sample_moderation_data["community_id"] = ""
        with pytest.raises(ValueError, match="Missing required fields"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_multiple_missing_fields(self, sample_moderation_data):
        """Test that multiple missing fields are all reported."""
        del sample_moderation_data["community_id"]
        del sample_moderation_data["reporter_id"]
        del sample_moderation_data["reason"]
        with pytest.raises(ValueError, match="community_id.*reporter_id.*reason"):
            create_moderation_item(sample_moderation_data)

    def test_create_moderation_item_returns_copy(self, sample_moderation_data):
        """Test that returned item is a copy, not the original reference."""
        result = create_moderation_item(sample_moderation_data)
        result["status"] = "modified"

        stored = get_moderation_item(result["id"])
        assert stored["status"] == "pending"


# ---------------------------------------------------------------------------
# resolve_moderation_item
# ---------------------------------------------------------------------------


class TestResolveModerationItem:
    """Test suite for resolve_moderation_item."""

    def test_resolve_moderation_item_approve(self, created_moderation_item):
        """Test resolving with 'approve' decision."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "approve")

        assert result["id"] == item_id
        assert result["status"] == "resolved"
        assert result["decision"] == "approve"
        assert result["resolved_at"] is not None

    def test_resolve_moderation_item_reject(self, created_moderation_item):
        """Test resolving with 'reject' decision."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "reject")

        assert result["status"] == "resolved"
        assert result["decision"] == "reject"

    def test_resolve_moderation_item_dismiss(self, created_moderation_item):
        """Test resolving with 'dismiss' decision."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "dismiss")

        assert result["status"] == "resolved"
        assert result["decision"] == "dismiss"

    def test_resolve_moderation_item_escalate(self, created_moderation_item):
        """Test resolving with 'escalate' decision."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "escalate")

        assert result["status"] == "resolved"
        assert result["decision"] == "escalate"

    def test_resolve_moderation_item_case_insensitive(self, created_moderation_item):
        """Test that decision is case-insensitive."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "APPROVE")

        assert result["decision"] == "approve"

    def test_resolve_moderation_item_not_found(self):
        """Test resolving a non-existent item raises error."""
        with pytest.raises(ModerationItemNotFoundError) as exc_info:
            resolve_moderation_item("nonexistent-id", "approve")

        assert "nonexistent-id" in str(exc_info.value)

    def test_resolve_moderation_item_already_resolved(self, created_moderation_item):
        """Test that resolving an already-resolved item raises error."""
        item_id = created_moderation_item["id"]
        resolve_moderation_item(item_id, "approve")

        with pytest.raises(ModerationItemAlreadyResolvedError) as exc_info:
            resolve_moderation_item(item_id, "reject")

        assert "already resolved" in str(exc_info.value)

    def test_resolve_moderation_item_invalid_decision(self, created_moderation_item):
        """Test that invalid decision raises error."""
        item_id = created_moderation_item["id"]
        with pytest.raises(InvalidModerationDecisionError) as exc_info:
            resolve_moderation_item(item_id, "invalid_decision")

        assert "Invalid decision" in str(exc_info.value)

    def test_resolve_moderation_item_empty_decision(self, created_moderation_item):
        """Test that empty decision raises error."""
        item_id = created_moderation_item["id"]
        with pytest.raises(InvalidModerationDecisionError):
            resolve_moderation_item(item_id, "")

    def test_resolve_moderation_item_none_decision(self, created_moderation_item):
        """Test that None decision raises error."""
        item_id = created_moderation_item["id"]
        with pytest.raises(InvalidModerationDecisionError):
            resolve_moderation_item(item_id, None)

    def test_resolve_moderation_item_empty_item_id(self):
        """Test that empty item_id raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            resolve_moderation_item("", "approve")

    def test_resolve_moderation_item_none_item_id(self):
        """Test that None item_id raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            resolve_moderation_item(None, "approve")

    def test_resolve_moderation_item_persists_in_store(self, created_moderation_item):
        """Test that resolution is persisted in the store."""
        item_id = created_moderation_item["id"]
        resolve_moderation_item(item_id, "reject")

        stored = get_moderation_item(item_id)
        assert stored["status"] == "resolved"
        assert stored["decision"] == "reject"
        assert stored["resolved_at"] is not None

    def test_resolve_moderation_item_returns_copy(self, created_moderation_item):
        """Test that returned item is a copy, not the original reference."""
        item_id = created_moderation_item["id"]
        result = resolve_moderation_item(item_id, "approve")
        result["status"] = "modified"

        stored = get_moderation_item(item_id)
        assert stored["status"] == "resolved"


# ---------------------------------------------------------------------------
# delete_moderation_item
# ---------------------------------------------------------------------------


class TestDeleteModerationItem:
    """Test suite for delete_moderation_item."""

    def test_delete_moderation_item_success(self, created_moderation_item):
        """Test deleting an existing moderation item."""
        item_id = created_moderation_item["id"]
        result = delete_moderation_item(item_id)

        assert result is True

    def test_delete_moderation_item_removes_from_store(self, created_moderation_item):
        """Test that deleted item is no longer retrievable."""
        item_id = created_moderation_item["id"]
        delete_moderation_item(item_id)

        with pytest.raises(ModerationItemNotFoundError):
            get_moderation_item(item_id)

    def test_delete_moderation_item_not_found(self):
        """Test deleting a non-existent item raises error."""
        with pytest.raises(ModerationItemNotFoundError) as exc_info:
            delete_moderation_item("nonexistent-id")

        assert "nonexistent-id" in str(exc_info.value)

    def test_delete_moderation_item_empty_id(self):
        """Test that empty item_id raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            delete_moderation_item("")

    def test_delete_moderation_item_none_id(self):
        """Test that None item_id raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            delete_moderation_item(None)

    def test_delete_moderation_item_non_string_id(self):
        """Test that non-string item_id raises ValueError."""
        with pytest.raises(ValueError, match="item_id must be a non-empty string"):
            delete_moderation_item(123)

    def test_delete_moderation_item_already_deleted(self, created_moderation_item):
        """Test that deleting an already-deleted item raises error."""
        item_id = created_moderation_item["id"]
        delete_moderation_item(item_id)

        with pytest.raises(ModerationItemNotFoundError):
            delete_moderation_item(item_id)

    def test_delete_moderation_item_only_deletes_target(self, sample_moderation_data):
        """Test that deleting one item does not affect others."""
        item1 = create_moderation_item({**sample_moderation_data, "reason": "spam"})
        item2 = create_moderation_item({**sample_moderation_data, "reason": "abuse"})

        delete_moderation_item(item1["id"])

        # item2 should still exist
        result = get_moderation_item(item2["id"])
        assert result["id"] == item2["id"]

        # item1 should be gone
        with pytest.raises(ModerationItemNotFoundError):
            get_moderation_item(item1["id"])


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------


class TestModerationServiceIntegration:
    """Integration tests for the moderation service workflow."""

    def test_full_moderation_lifecycle(self, sample_moderation_data):
        """Test the complete lifecycle: create -> get -> list -> resolve -> delete."""
        # Create
        item = create_moderation_item(sample_moderation_data)
        item_id = item["id"]
        assert item["status"] == "pending"

        # Get
        fetched = get_moderation_item(item_id)
        assert fetched["status"] == "pending"

        # List
        items = list_moderation_items(filters={}, page=1, page_size=10)
        assert len(items) == 1

        # Resolve
        resolved = resolve_moderation_item(item_id, "approve")
        assert resolved["status"] == "resolved"
        assert resolved["decision"] == "approve"

        # Delete
        deleted = delete_moderation_item(item_id)
        assert deleted is True

        # Verify deletion
        with pytest.raises(ModerationItemNotFoundError):
            get_moderation_item(item_id)

    def test_multiple_items_workflow(self, sample_moderation_data):
        """Test workflow with multiple items."""
        items = []
        for i in range(3):
            item = create_moderation_item({
                **sample_moderation_data,
                "reason": f"reason-{i}",
                "community_id": f"comm-{i}",
            })
            items.append(item)

        # Resolve first item
        resolve_moderation_item(items[0]["id"], "approve")

        # Check filters
        pending = list_moderation_items(filters={"status": "pending"}, page=1, page_size=10)
        assert len(pending) == 2

        resolved = list_moderation_items(filters={"status": "resolved"}, page=1, page_size=10)
        assert len(resolved) == 1

        # Delete all
        for item in items:
            delete_moderation_item(item["id"])

        # Verify all deleted
        all_items = list_moderation_items(filters={}, page=1, page_size=10)
        assert len(all_items) == 0
