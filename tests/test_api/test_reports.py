"""API tests for the Reports endpoints.

Real shipped route (mounted at ROOT):

    GET /reports  -> 200 []   (src/gated_communities/api/reports.py is a stub
                               that returns an empty list)

Endpoint coverage note:

* ``POST /reports/generate`` and ``GET /reports/{id}/download`` are NOT
  implemented — the shipped router exposes only ``GET /reports``.  Those
  routes must fail closed (404/405), and ``GET /reports/{id}`` is likewise
  unrouted.
"""


class TestListReports:
    """Tests for GET /reports."""

    def test_list_reports_success(self, client):
        """GET /reports returns 200 and a (currently empty) list."""
        response = client.get("/reports")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_reports_is_empty_stub(self, client):
        """The shipped router is a stub that returns no reports."""
        response = client.get("/reports")
        assert response.json() == []

    def test_list_reports_content_type(self, client):
        response = client.get("/reports")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_list_reports_pagination_params_accepted(self, client):
        """Unknown query params are ignored without error."""
        response = client.get("/reports?skip=0&limit=10")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGenerateReport:
    """POST /reports/generate is not implemented in the shipped router."""

    def test_generate_report_route_absent(self, client):
        response = client.post("/reports/generate", json={"report_id": "rpt_001"})
        assert response.status_code in (404, 405)


class TestGetReport:
    """Tests for GET /reports/{id}.

    Only the shipped router (``GET /reports``) exists, so any ``/{id}`` path is
    unrouted and must fail closed (404/405).
    """

    def test_get_report_invalid_id(self, client):
        response = client.get("/reports/nonexistent_id")
        assert response.status_code in (404, 405)

    def test_get_report_empty_id(self, client):
        # A trailing slash redirects to /reports, which TestClient follows -> 200.
        response = client.get("/reports/")
        assert response.status_code in (200, 307, 404)

    def test_get_report_route_absent(self, client):
        response = client.get("/reports/some-instance")
        assert response.status_code in (404, 405)


class TestDownloadReport:
    """GET /reports/{id}/download is not implemented in the shipped router."""

    def test_download_report_route_absent(self, client):
        response = client.get("/reports/some-instance/download")
        assert response.status_code in (404, 405)
