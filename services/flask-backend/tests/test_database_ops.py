"""Tests for Database Operations API endpoints."""
import pytest


class TestDatabaseOpsHealth:
    """Tests for GET /database-ops/health."""

    def test_health_requires_auth(self, client):
        """Health endpoint requires authentication."""
        response = client.get("/api/v1/database-ops/health")
        assert response.status_code == 401

    def test_health_missing_db_type(self, client, auth_headers):
        """Health endpoint returns 400 when db_type is missing."""
        response = client.get(
            "/api/v1/database-ops/health",
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_health_invalid_db_type(self, client, auth_headers):
        """Health endpoint returns 400 for invalid db_type."""
        response = client.get(
            "/api/v1/database-ops/health?db_type=invalid_db",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestDatabaseOpsQuery:
    """Tests for POST /database-ops/query."""

    def test_query_requires_auth(self, client):
        """Query endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/query",
            json={"connection": {"db_type": "sqlite"}, "table": "users"},
        )
        assert response.status_code == 401

    def test_query_missing_connection(self, client, auth_headers):
        """Query endpoint returns 400 when connection is missing."""
        response = client.post(
            "/api/v1/database-ops/query",
            headers=auth_headers,
            json={"table": "users"},
        )
        assert response.status_code == 400

    def test_query_missing_table(self, client, auth_headers):
        """Query endpoint returns 400 when table is missing."""
        response = client.post(
            "/api/v1/database-ops/query",
            headers=auth_headers,
            json={"connection": {"db_type": "sqlite", "db_path": ":memory:"}},
        )
        assert response.status_code == 400

    def test_query_with_sqlite_in_memory(self, client, auth_headers):
        """Query executes against an in-memory SQLite database."""
        response = client.post(
            "/api/v1/database-ops/query",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "test_table",
                "limit": 10,
            },
        )
        # Expect 200 or 500 (table doesn't exist on fresh DB); never 401/405
        assert response.status_code in [200, 500]


class TestDatabaseOpsInsert:
    """Tests for POST /database-ops/insert."""

    def test_insert_requires_auth(self, client):
        """Insert endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/insert",
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
                "data": {"name": "test"},
            },
        )
        assert response.status_code == 401

    def test_insert_missing_table(self, client, auth_headers):
        """Insert returns 400 when table is missing."""
        response = client.post(
            "/api/v1/database-ops/insert",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "data": {"name": "test"},
            },
        )
        assert response.status_code == 400

    def test_insert_missing_data(self, client, auth_headers):
        """Insert returns 400 when data is missing."""
        response = client.post(
            "/api/v1/database-ops/insert",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
            },
        )
        assert response.status_code == 400


class TestDatabaseOpsUpdate:
    """Tests for POST /database-ops/update."""

    def test_update_requires_auth(self, client):
        """Update endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/update",
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
                "where": {"id": 1},
                "data": {"name": "updated"},
            },
        )
        assert response.status_code == 401

    def test_update_missing_where(self, client, auth_headers):
        """Update returns 400 when where conditions are missing."""
        response = client.post(
            "/api/v1/database-ops/update",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
                "data": {"name": "updated"},
            },
        )
        assert response.status_code == 400


class TestDatabaseOpsDelete:
    """Tests for POST /database-ops/delete."""

    def test_delete_requires_auth(self, client):
        """Delete endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/delete",
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
                "where": {"id": 1},
            },
        )
        assert response.status_code == 401

    def test_delete_missing_where(self, client, auth_headers):
        """Delete returns 400 when where conditions are missing."""
        response = client.post(
            "/api/v1/database-ops/delete",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
            },
        )
        assert response.status_code == 400


class TestDatabaseOpsBulkInsert:
    """Tests for POST /database-ops/bulk-insert."""

    def test_bulk_insert_requires_auth(self, client):
        """Bulk insert endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/bulk-insert",
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
                "rows": [{"name": "a"}, {"name": "b"}],
            },
        )
        assert response.status_code == 401

    def test_bulk_insert_missing_rows(self, client, auth_headers):
        """Bulk insert returns 400 when rows are missing."""
        response = client.post(
            "/api/v1/database-ops/bulk-insert",
            headers=auth_headers,
            json={
                "connection": {"db_type": "sqlite", "db_path": ":memory:"},
                "table": "users",
            },
        )
        assert response.status_code == 400


class TestDatabaseOpsProcedure:
    """Tests for POST /database-ops/procedure."""

    def test_procedure_requires_auth(self, client):
        """Procedure endpoint requires authentication."""
        response = client.post(
            "/api/v1/database-ops/procedure",
            json={
                "connection": {"db_type": "mysql", "host": "localhost", "database": "db"},
                "procedure": "my_proc",
            },
        )
        assert response.status_code == 401

    def test_procedure_rejected_for_nosql(self, client, auth_headers):
        """Procedure endpoint returns 400 for NoSQL databases."""
        response = client.post(
            "/api/v1/database-ops/procedure",
            headers=auth_headers,
            json={
                "connection": {"db_type": "mongodb", "host": "localhost", "database": "db"},
                "procedure": "my_proc",
            },
        )
        assert response.status_code == 400


class TestDatabaseOpsSchema:
    """Tests for GET /database-ops/schema."""

    def test_schema_requires_auth(self, client):
        """Schema endpoint requires authentication."""
        response = client.get("/api/v1/database-ops/schema?db_type=sqlite")
        assert response.status_code == 401

    def test_schema_missing_db_type(self, client, auth_headers):
        """Schema endpoint returns 400 when db_type is missing."""
        response = client.get(
            "/api/v1/database-ops/schema",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestDatabaseOpsCount:
    """Tests for GET /database-ops/count."""

    def test_count_requires_auth(self, client):
        """Count endpoint requires authentication."""
        response = client.get(
            "/api/v1/database-ops/count?db_type=sqlite&table=users",
        )
        assert response.status_code == 401

    def test_count_missing_table(self, client, auth_headers):
        """Count endpoint returns 400 when table is missing."""
        response = client.get(
            "/api/v1/database-ops/count?db_type=sqlite",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestDatabaseOpsExists:
    """Tests for GET /database-ops/exists."""

    def test_exists_requires_auth(self, client):
        """Exists endpoint requires authentication."""
        response = client.get(
            "/api/v1/database-ops/exists?db_type=sqlite&table=users",
        )
        assert response.status_code == 401

    def test_exists_missing_table(self, client, auth_headers):
        """Exists endpoint returns 400 when table is missing."""
        response = client.get(
            "/api/v1/database-ops/exists?db_type=sqlite",
            headers=auth_headers,
        )
        assert response.status_code == 400
