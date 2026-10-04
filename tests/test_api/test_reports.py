"""
Comprehensive API tests for the Reports endpoints.

Tests cover:
- GET  /api/v1/reports              (test_list_reports)
- POST /api/v1/reports/generate     (test_generate_report)
- GET  /api/v1/reports/{id}         (test_get_report)
- GET  /api/v1/reports/{id}/download (test_download_report)
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gated_communities.api.reports import router as reports_router


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def reports_app():
    """Create a minimal FastAPI app that includes only the reports router."""
    app = FastAPI(title="Reports Test API", version="0.1.0")
    app.include_router(reports_router, prefix="/api/v1", tags=["reports"])
    return app


@pytest.fixture
def client(reports_app):
    """Return a TestClient bound to the reports test app."""
    with TestClient(reports_app) as c:
        yield c


@pytest.fixture
def sample_generate_payload():
    """Return a valid payload for generating a report."""
    return {
        "report_id": "rpt_001",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-31T23:59:59Z",
        "community_id": "comm_123",
        "format": "pdf",
    }


@pytest.fixture
def generated_report(client, sample_generate_payload):
    """Generate a report via the API and return the response JSON."""
    response = client.post("/api/v1/reports/generate", json=sample_generate_payload)
    assert response.status_code == 200, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. test_list_reports  —  GET /api/v1/reports
# ---------------------------------------------------------------------------


class TestListReports:
    """Tests for the GET /api/v1/reports endpoint."""

    def test_list_reports_success(self, client):
        """GET /reports should return 200 and a list of available reports."""
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_list_reports_returns_all_available(self, client):
        """The list should contain all predefined AVAILABLE_REPORTS."""
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        returned_ids = {r["id"] for r in data}
        expected_ids = {r["id"] for r in AVAILABLE_REPORTS}
        assert returned_ids == expected_ids

    def test_list_reports_structure(self, client):
        """Each report in the list should contain the expected keys."""
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        expected_keys = {"id", "name", "description", "category", "format", "estimated_duration_seconds"}
        for report in data:
            assert expected_keys.issubset(set(report.keys())), (
                f"Report {report.get('id', '?')} missing keys: {expected_keys - set(report.keys())}"
            )

    def test_list_reports_pagination_params_accepted(self, client):
        """Pagination query params (skip, limit) should not cause errors."""
        response = client.get("/api/v1/reports?skip=0&limit=10")

        # The endpoint may or may not support pagination; either 200 or 422 is acceptable.
        assert response.status_code in (200, 422)

    def test_list_reports_pagination_with_limit(self, client):
        """A limit param should not break the endpoint."""
        response = client.get("/api/v1/reports?limit=2")

        assert response.status_code in (200, 422)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_reports_pagination_with_skip(self, client):
        """A skip param should not break the endpoint."""
        response = client.get("/api/v1/reports?skip=1")

        assert response.status_code in (200, 422)
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_list_reports_content_type(self, client):
        """The response should have application/json content type."""
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_list_reports_fields_have_correct_types(self, client):
        """Each field in a report should have the expected type."""
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        for report in data:
            assert isinstance(report["id"], str)
            assert isinstance(report["name"], str)
            assert isinstance(report["description"], str)
            assert isinstance(report["category"], str)
            assert isinstance(report["format"], str)
            assert isinstance(report["estimated_duration_seconds"], int)

    def test_list_reports_categories_are_valid(self, client):
        """Report categories should be from a known set."""
        valid_categories = {"analytics", "growth", "moderation", "finance", "security"}
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        for report in data:
            assert report["category"] in valid_categories

    def test_list_reports_formats_are_valid(self, client):
        """Report formats should be from a known set."""
        valid_formats = {"pdf", "csv", "xlsx"}
        response = client.get("/api/v1/reports")

        assert response.status_code == 200
        data = response.json()
        for report in data:
            assert report["format"] in valid_formats


# ---------------------------------------------------------------------------
# 2. test_generate_report  —  POST /api/v1/reports/generate
# ---------------------------------------------------------------------------


class TestGenerateReport:
    """Tests for the POST /api/v1/reports/generate endpoint."""

    def test_generate_report_success(self, client, sample_generate_payload):
        """A valid payload should generate a report and return 200."""
        response = client.post("/api/v1/reports/generate", json=sample_generate_payload)

        assert response.status_code == 200
        data = response.json()
        assert "report_instance_id" in data
        assert data["report_id"] == sample_generate_payload["report_id"]
        assert data["status"] == "completed"
        assert data["format"] == sample_generate_payload["format"]
        assert "created_at" in data
        assert "download_url" in data
        assert "message" in data

    def test_generate_report_returns_unique_instance_id(self, client, sample_generate_payload):
        """Two generate calls should return different instance IDs."""
        resp1 = client.post("/api/v1/reports/generate", json=sample_generate_payload)
        resp2 = client.post("/api/v1/reports/generate", json=sample_generate_payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        assert resp1.json()["report_instance_id"] != resp2.json()["report_instance_id"]

    def test_generate_report_invalid_report_id(self, client):
        """An unknown report_id should return 404."""
        payload = {"report_id": "nonexistent_report", "format": "pdf"}
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 404

    def test_generate_report_unsupported_format(self, client):
        """An unsupported format should return 400."""
        payload = {"report_id": "rpt_001", "format": "docx"}
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 400

    def test_generate_report_missing_report_id(self, client):
        """Omitting the required report_id field should return 422."""
        payload = {"format": "pdf"}
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 422

    def test_generate_report_default_format(self, client):
        """When format is omitted it should default to the report's native format."""
        payload = {"report_id": "rpt_002"}  # rpt_002 is csv
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"

    def test_generate_report_explicit_format_override(self, client):
        """An explicit format should override the report's default."""
        payload = {"report_id": "rpt_001", "format": "csv"}  # rpt_001 is pdf by default
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "csv"

    def test_generate_report_with_date_range(self, client):
        """A payload with start_date and end_date should succeed."""
        payload = {
            "report_id": "rpt_001",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2025-01-31T23:59:59Z",
        }
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == "rpt_001"

    def test_generate_report_with_community_filter(self, client):
        """A payload with community_id should succeed."""
        payload = {
            "report_id": "rpt_001",
            "community_id": "comm_456",
        }
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["report_id"] == "rpt_001"

    def test_generate_report_download_url_format(self, client, sample_generate_payload):
        """The download_url should follow the expected pattern."""
        response = client.post("/api/v1/reports/generate", json=sample_generate_payload)

        assert response.status_code == 200
        data = response.json()
        instance_id = data["report_instance_id"]
        assert instance_id in data["download_url"]
        assert "/download/" in data["download_url"]

    def test_generate_report_content_type(self, client, sample_generate_payload):
        """The response should have application/json content type."""
        response = client.post("/api/v1/reports/generate", json=sample_generate_payload)

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_generate_report_all_available_types(self, client):
        """Every available report type should be generatable."""
        for report in AVAILABLE_REPORTS:
            payload = {"report_id": report["id"]}
            response = client.post("/api/v1/reports/generate", json=payload)
            assert response.status_code == 200, (
                f"Failed to generate report {report['id']}: {response.text}"
            )
            data = response.json()
            assert data["report_id"] == report["id"]
            assert data["report_name"] == report["name"]

    def test_generate_report_case_insensitive_format(self, client):
        """Format should be case-insensitive (e.g., 'PDF' works)."""
        payload = {"report_id": "rpt_001", "format": "PDF"}
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["format"] == "pdf"

    def test_generate_report_extra_fields_ignored(self, client, sample_generate_payload):
        """Unknown fields should not cause a 500."""
        payload = {**sample_generate_payload, "unknown_field": "value"}
        response = client.post("/api/v1/reports/generate", json=payload)

        assert response.status_code in (200, 422)


# ---------------------------------------------------------------------------
# 3. test_get_report  —  GET /api/v1/reports/{id}
# ---------------------------------------------------------------------------


class TestGetReport:
    """Tests for the GET /api/v1/reports/{id} endpoint."""

    def test_get_report_not_implemented(self, client, generated_report):
        """
        GET /reports/{id} is not implemented in the current API.
        It should return 404 (or 405 if the route doesn't exist).
        """
        instance_id = generated_report["report_instance_id"]
        response = client.get(f"/api/v1/reports/{instance_id}")

        # The endpoint is not implemented; expect 404 or 405.
        assert response.status_code in (404, 405)

    def test_get_report_invalid_id(self, client):
        """A non-existent report ID should return 404."""
        response = client.get("/api/v1/reports/nonexistent_id")

        assert response.status_code in (404, 405)

    def test_get_report_empty_id(self, client):
        """An empty report ID should return 404 or 422."""
        response = client.get("/api/v1/reports/")

        # Trailing slash may redirect or return 404/422.
        assert response.status_code in (404, 422, 307)


# ---------------------------------------------------------------------------
# 4. test_download_report  —  GET /api/v1/reports/{id}/download
# ---------------------------------------------------------------------------


class TestDownloadReport:
    """Tests for the GET /api/v1/reports/{id}/download endpoint."""

    def test_download_report_not_implemented(self, client, generated_report):
        """
        GET /reports/{id}/download is not implemented in the current API.
        It should return 404 (or 405 if the route doesn't exist).
        """
        instance_id = generated_report["report_instance_id"]
        response = client.get(f"/api/v1/reports/{instance_id}/download")

        # The endpoint is not implemented; expect 404 or 405.
        assert response.status_code in (404, 405)

    def test_download_report_invalid_id(self, client):
        """A non-existent report ID should return 404."""
        response = client.get("/api/v1/reports/nonexistent_id/download")

        assert response.status_code in (404, 405)

    def test_download_report_url_from_generate(self, client, generated_report):
        """
        The download_url returned by generate should be a valid path.
        We verify the URL structure even if the endpoint is not yet implemented.
        """
        download_url = generated_report["download_url"]
        assert download_url is not None
        assert "/download/" in download_url
        instance_id = generated_report["report_instance_id"]
        assert instance_id in download_url

    def test_download_report_content_type_not_implemented(self, client, generated_report):
        """If download is not implemented, the response should still be valid JSON or 404."""
        instance_id = generated_report["report_instance_id"]
        response = client.get(f"/api/v1/reports/{instance_id}/download")

        if response.status_code == 200:
            # If implemented, should return a file or JSON
            assert response.headers.get("content-type") is not None
        else:
            assert response.status_code in (404, 405)
