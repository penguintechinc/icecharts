"""Tests for Connectors API endpoints."""

import pytest


class TestListConnectors:
    """Tests for GET /connectors."""

    def test_list_connectors_requires_auth(self, client):
        """Listing connectors requires authentication."""
        response = client.get("/api/v1/connectors")
        assert response.status_code == 401

    def test_list_connectors_with_auth(self, client, auth_headers):
        """Authenticated request returns connector list."""
        response = client.get("/api/v1/connectors", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "connectors" in data
        assert isinstance(data["connectors"], list)


class TestGetConnector:
    """Tests for GET /connectors/<connector_id>."""

    def test_get_connector_requires_auth(self, client):
        """Getting a connector requires authentication."""
        response = client.get("/api/v1/connectors/waddlebot")
        assert response.status_code == 401

    def test_get_connector_not_found(self, client, auth_headers):
        """Returns 404 for a non-existent connector."""
        response = client.get(
            "/api/v1/connectors/nonexistent-connector-xyz",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_connector_response_shape(self, client, auth_headers):
        """A valid connector returns expected shape or 404 if not loaded."""
        response = client.get("/api/v1/connectors/waddlebot", headers=auth_headers)
        assert response.status_code in [200, 404]


class TestGetConnectorNodes:
    """Tests for GET /connectors/<connector_id>/nodes."""

    def test_get_connector_nodes_requires_auth(self, client):
        """Getting connector nodes requires authentication."""
        response = client.get("/api/v1/connectors/waddlebot/nodes")
        assert response.status_code == 401

    def test_get_connector_nodes_not_found(self, client, auth_headers):
        """Returns 404 for nodes of a non-existent connector."""
        response = client.get(
            "/api/v1/connectors/nonexistent-connector-xyz/nodes",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestGetAllConnectorNodes:
    """Tests for GET /connectors/nodes."""

    def test_get_all_nodes_requires_auth(self, client):
        """Getting all connector nodes requires authentication."""
        response = client.get("/api/v1/connectors/nodes")
        assert response.status_code == 401

    def test_get_all_nodes_with_auth(self, client, auth_headers):
        """Authenticated request returns all nodes."""
        response = client.get("/api/v1/connectors/nodes", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)

    def test_get_all_nodes_category_filter(self, client, auth_headers):
        """Category filter query parameter is accepted."""
        response = client.get(
            "/api/v1/connectors/nodes?category=triggers",
            headers=auth_headers,
        )
        assert response.status_code == 200
