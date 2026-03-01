"""Tests for Elder integration API endpoints."""
import pytest


class TestElderValidateConnection:
    """Tests for POST /elder/validate-connection."""

    def test_validate_connection_requires_auth(self, client):
        """Validate connection endpoint requires authentication."""
        response = client.post(
            "/api/v1/elder/validate-connection",
            json={"base_url": "https://elder.example.com", "api_key": "test-key"},
        )
        assert response.status_code == 401

    def test_validate_connection_missing_fields(self, client, auth_headers):
        """Validate connection returns 400 when required fields are missing."""
        response = client.post(
            "/api/v1/elder/validate-connection",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400

    def test_validate_connection_missing_api_key(self, client, auth_headers):
        """Validate connection returns 400 when api_key is missing."""
        response = client.post(
            "/api/v1/elder/validate-connection",
            headers=auth_headers,
            json={"base_url": "https://elder.example.com"},
        )
        assert response.status_code == 400


class TestElderEntities:
    """Tests for GET /elder/entities."""

    def test_get_entities_requires_auth(self, client):
        """Getting entities requires authentication."""
        response = client.get("/api/v1/elder/entities?org_id=1")
        assert response.status_code == 401

    def test_get_entities_missing_required_params(self, client, auth_headers):
        """Returns 400 when required query params are missing."""
        response = client.get(
            "/api/v1/elder/entities",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestElderRelationships:
    """Tests for GET /elder/relationships."""

    def test_get_relationships_requires_auth(self, client):
        """Getting relationships requires authentication."""
        response = client.get("/api/v1/elder/relationships?org_id=1")
        assert response.status_code == 401

    def test_get_relationships_missing_params(self, client, auth_headers):
        """Returns 400 when required query params are missing."""
        response = client.get(
            "/api/v1/elder/relationships",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestElderGraph:
    """Tests for GET /elder/graph."""

    def test_get_graph_requires_auth(self, client):
        """Getting graph requires authentication."""
        response = client.get("/api/v1/elder/graph?org_id=1")
        assert response.status_code == 401

    def test_get_graph_missing_params(self, client, auth_headers):
        """Returns 400 when required query params are missing."""
        response = client.get(
            "/api/v1/elder/graph",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestElderImport:
    """Tests for POST /elder/import."""

    def test_import_entities_requires_auth(self, client):
        """Importing entities requires authentication."""
        response = client.post(
            "/api/v1/elder/import",
            json={
                "drawing_id": "test",
                "base_url": "https://elder.example.com",
                "api_key": "key",
                "org_id": 1,
            },
        )
        assert response.status_code == 401

    def test_import_entities_missing_fields(self, client, auth_headers):
        """Returns 400 when required fields are missing."""
        response = client.post(
            "/api/v1/elder/import",
            headers=auth_headers,
            json={},
        )
        assert response.status_code == 400


class TestElderHealth:
    """Tests for GET /elder/health."""

    def test_health_check_no_auth_required(self, client):
        """Elder health check is public (no auth required)."""
        response = client.get("/api/v1/elder/health")
        assert response.status_code == 200

    def test_health_check_response_format(self, client):
        """Elder health returns a healthy status."""
        response = client.get("/api/v1/elder/health")
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "elder-integration"
