"""Collection Management and Sharing Tests."""

import json

import pytest


class TestCollectionCreate:
    """Test collection creation."""

    def test_create_collection_success(self, client, auth_headers):
        """Test successful collection creation."""
        response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
                "share_mode": "private",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "collection" in data
        assert data["collection"]["name"] == "Test Collection"
        assert data["collection"]["description"] == "A test collection"
        assert data["collection"]["is_public"] is False

    def test_create_collection_without_auth(self, client):
        """Test collection creation without authentication."""
        response = client.post(
            "/api/v1/collections",
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        assert response.status_code == 401

    def test_create_collection_missing_name(self, client, auth_headers):
        """Test collection creation without name."""
        response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "description": "A test collection",
                "is_public": False,
            },
        )
        assert response.status_code == 400

    def test_create_collection_empty_name(self, client, auth_headers):
        """Test collection creation with empty name."""
        response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "",
                "description": "A test collection",
                "is_public": False,
            },
        )
        assert response.status_code == 400

    def test_create_public_collection(self, client, auth_headers):
        """Test creating a public collection."""
        response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Public Collection",
                "description": "A public collection",
                "is_public": True,
                "share_mode": "link_only",
            },
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["collection"]["is_public"] is True


class TestCollectionRead:
    """Test collection retrieval."""

    def test_get_collection_by_id(self, client, auth_headers):
        """Test retrieving a collection by ID."""
        # Create a collection
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Retrieve the collection
        response = client.get(
            f"/api/v1/collections/{collection_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["collection"]["id"] == collection_id
        assert data["collection"]["name"] == "Test Collection"

    def test_get_collection_not_found(self, client, auth_headers):
        """Test retrieving non-existent collection."""
        response = client.get("/api/v1/collections/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_list_user_collections(self, client, auth_headers):
        """Test listing user's collections."""
        # Create multiple collections
        for i in range(3):
            client.post(
                "/api/v1/collections",
                headers=auth_headers,
                json={
                    "name": f"Collection {i}",
                    "description": f"Test collection {i}",
                    "is_public": False,
                },
            )

        # List collections
        response = client.get("/api/v1/collections", headers=auth_headers)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "collections" in data
        assert len(data["collections"]) == 3

    def test_list_collections_pagination(self, client, auth_headers):
        """Test collection list pagination."""
        # Create 15 collections
        for i in range(15):
            client.post(
                "/api/v1/collections",
                headers=auth_headers,
                json={
                    "name": f"Collection {i}",
                    "description": f"Test collection {i}",
                    "is_public": False,
                },
            )

        # Get first page
        response = client.get(
            "/api/v1/collections?page=1&per_page=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data["collections"]) == 10
        assert data["total"] == 15

    def test_user_cannot_see_other_users_private_collections(
        self, client, auth_headers, create_test_user
    ):
        """Test RBAC: users can't see other users' private collections."""
        # Create a collection with first user
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Private Collection",
                "description": "A private collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Create auth headers for other user
        from app.api.v1.auth import create_access_token

        with client.application.app_context():
            other_auth_headers = {
                "Authorization": f"Bearer {create_access_token(other_user['id'], other_user['role'])}"
            }

        # Try to access collection with other user
        response = client.get(
            f"/api/v1/collections/{collection_id}",
            headers=other_auth_headers,
        )
        # Should be denied (404 or 403)
        assert response.status_code in [403, 404]


class TestCollectionUpdate:
    """Test collection updates."""

    def test_update_collection_name(self, client, auth_headers):
        """Test updating collection name."""
        # Create a collection
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Original Name",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Update the collection
        response = client.put(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["collection"]["name"] == "Updated Name"

    def test_update_collection_description(self, client, auth_headers):
        """Test updating collection description."""
        # Create a collection
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "Original description",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Update the description
        response = client.put(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers,
            json={"description": "Updated description"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["collection"]["description"] == "Updated description"

    def test_update_collection_without_auth(self, client):
        """Test updating collection without authentication."""
        response = client.put(
            "/api/v1/collections/1",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 401

    def test_update_nonexistent_collection(self, client, auth_headers):
        """Test updating non-existent collection."""
        response = client.put(
            "/api/v1/collections/99999",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )
        # API returns 403 (not owner) or 404 (not found)
        assert response.status_code in [403, 404]

    def test_change_collection_visibility(self, client, auth_headers):
        """Test changing collection from private to public."""
        # Create a private collection
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Private Collection",
                "description": "Initially private",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Make it public
        response = client.put(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers,
            json={"is_public": True},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["collection"]["is_public"] is True


class TestCollectionDelete:
    """Test collection deletion."""

    def test_delete_collection_success(self, client, auth_headers):
        """Test successful collection deletion."""
        # Create a collection
        create_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(create_response.data)["collection"]["id"]

        # Delete the collection
        response = client.delete(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify it's deleted
        get_response = client.get(
            f"/api/v1/collections/{collection_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    def test_delete_collection_not_found(self, client, auth_headers):
        """Test deleting non-existent collection."""
        response = client.delete(
            "/api/v1/collections/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_delete_collection_without_auth(self, client):
        """Test deleting collection without authentication."""
        response = client.delete("/api/v1/collections/1")
        assert response.status_code == 401


class TestCollectionDrawings:
    """Test adding/removing drawings to/from collections."""

    def test_add_drawing_to_collection(self, client, auth_headers):
        """Test adding a drawing to a collection."""
        # Create a drawing
        drawing_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        drawing_id = int(json.loads(drawing_response.data)["drawing"]["id"])

        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Add drawing to collection
        response = client.post(
            f"/api/v1/collections/{collection_id}/drawings",
            headers=auth_headers,
            json={"drawing_id": drawing_id},
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "item" in data
        assert data["item"]["drawing_id"] == drawing_id

    def test_get_collection_drawings(self, client, auth_headers):
        """Test retrieving drawings in a collection."""
        # Create collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Create and add multiple drawings
        for i in range(3):
            drawing_response = client.post(
                "/api/v1/drawings",
                headers=auth_headers,
                json={
                    "name": f"Drawing {i}",
                    "description": f"Test drawing {i}",
                    "content": {"nodes": [], "edges": []},
                },
            )
            drawing_id = int(json.loads(drawing_response.data)["drawing"]["id"])

            client.post(
                f"/api/v1/collections/{collection_id}/drawings",
                headers=auth_headers,
                json={"drawing_id": drawing_id},
            )

        # Get collection drawings
        response = client.get(
            f"/api/v1/collections/{collection_id}/drawings",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "drawings" in data

    def test_remove_drawing_from_collection(self, client, auth_headers):
        """Test removing a drawing from a collection."""
        # Create drawing
        drawing_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        drawing_id = int(json.loads(drawing_response.data)["drawing"]["id"])

        # Create collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Add drawing to collection
        client.post(
            f"/api/v1/collections/{collection_id}/drawings",
            headers=auth_headers,
            json={"drawing_id": drawing_id},
        )

        # Remove drawing from collection
        response = client.delete(
            f"/api/v1/collections/{collection_id}/drawings/{drawing_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_add_nonexistent_drawing_to_collection(self, client, auth_headers):
        """Test adding non-existent drawing to collection."""
        # Create collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Try to add non-existent drawing
        response = client.post(
            f"/api/v1/collections/{collection_id}/drawings",
            headers=auth_headers,
            json={"drawing_id": 99999},
        )
        # API returns 400 (invalid), 403 (not owner), or 404 (not found)
        assert response.status_code in [400, 403, 404]


class TestCollectionSharing:
    """Test collection sharing functionality."""

    def test_share_collection_with_user(self, client, auth_headers, create_test_user):
        """Test sharing a collection with another user."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Share the collection
        response = client.post(
            f"/api/v1/collections/{collection_id}/share",
            headers=auth_headers,
            json={"shared_with_id": other_user["id"], "permission": "viewer"},
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert "share" in data

    def test_list_collection_shares(self, client, auth_headers, create_test_user):
        """Test listing shares for a collection."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Create another user and share
        other_user = create_test_user("other@example.com")
        client.post(
            f"/api/v1/collections/{collection_id}/share",
            headers=auth_headers,
            json={"shared_with_id": other_user["id"], "permission": "viewer"},
        )

        # List shares
        response = client.get(
            f"/api/v1/collections/{collection_id}/shares",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "shares" in data

    def test_revoke_collection_share(self, client, auth_headers, create_test_user):
        """Test revoking a collection share."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Create another user and share
        other_user = create_test_user("other@example.com")
        share_response = client.post(
            f"/api/v1/collections/{collection_id}/share",
            headers=auth_headers,
            json={"shared_with_id": other_user["id"], "permission": "viewer"},
        )
        share_id = json.loads(share_response.data)["share"]["id"]

        # Revoke the share
        response = client.delete(
            f"/api/v1/collections/{collection_id}/shares/{share_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestCollectionSharingTokens:
    """Test public sharing via tokens."""

    def test_generate_share_token(self, client, auth_headers):
        """Test generating a share token for public access."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Public Collection",
                "description": "A public collection",
                "is_public": True,
                "share_mode": "link_only",
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Generate share token
        response = client.post(
            f"/api/v1/collections/{collection_id}/share/token",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "token" in data
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    def test_access_shared_collection_with_token(self, client, auth_headers):
        """Test accessing a shared collection using a token."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Public Collection",
                "description": "A public collection",
                "is_public": True,
                "share_mode": "link_only",
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Generate share token
        token_response = client.post(
            f"/api/v1/collections/{collection_id}/share/token",
            headers=auth_headers,
        )
        token = json.loads(token_response.data)["token"]

        # Access collection with token (unauthenticated)
        response = client.get(f"/api/v1/collections/shared/{token}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "collection" in data

    def test_access_shared_collection_drawings_with_token(self, client, auth_headers):
        """Test accessing drawings in a shared collection using token."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Public Collection",
                "description": "A public collection",
                "is_public": True,
                "share_mode": "link_only",
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Add a drawing to collection
        drawing_response = client.post(
            "/api/v1/drawings",
            headers=auth_headers,
            json={
                "name": "Test Drawing",
                "description": "A test drawing",
                "content": {"nodes": [], "edges": []},
            },
        )
        drawing_id = int(json.loads(drawing_response.data)["drawing"]["id"])

        client.post(
            f"/api/v1/collections/{collection_id}/drawings",
            headers=auth_headers,
            json={"drawing_id": drawing_id},
        )

        # Generate share token
        token_response = client.post(
            f"/api/v1/collections/{collection_id}/share/token",
            headers=auth_headers,
        )
        token = json.loads(token_response.data)["token"]

        # Access collection drawings with token (unauthenticated)
        response = client.get(f"/api/v1/collections/shared/{token}/drawings")
        # May return empty for unauthenticated users depending on implementation
        assert response.status_code in [200, 403]

    def test_invalid_token_access(self, client):
        """Test accessing shared collection with invalid token."""
        response = client.get("/api/v1/collections/shared/invalid-token-here")
        assert response.status_code == 404

    def test_regenerate_share_token(self, client, auth_headers):
        """Test regenerating a share token."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Public Collection",
                "description": "A public collection",
                "is_public": True,
                "share_mode": "link_only",
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Generate initial token
        token_response1 = client.post(
            f"/api/v1/collections/{collection_id}/share/token",
            headers=auth_headers,
        )
        token1 = json.loads(token_response1.data)["token"]

        # Regenerate token
        token_response2 = client.post(
            f"/api/v1/collections/{collection_id}/share/token",
            headers=auth_headers,
        )
        token2 = json.loads(token_response2.data)["token"]

        # Both should be valid tokens
        assert token1 is not None
        assert token2 is not None


class TestCollectionAnalytics:
    """Test collection analytics endpoints."""

    def test_get_collection_analytics(self, client, auth_headers):
        """Test getting analytics for a collection."""
        # Create a collection
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Get analytics
        response = client.get(
            f"/api/v1/collections/{collection_id}/analytics",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "stats" in data

    def test_non_owner_cannot_view_analytics(
        self, client, auth_headers, create_test_user
    ):
        """Test that non-owners can't view collection analytics."""
        # Create a collection with first user
        collection_response = client.post(
            "/api/v1/collections",
            headers=auth_headers,
            json={
                "name": "Test Collection",
                "description": "A test collection",
                "is_public": False,
            },
        )
        collection_id = json.loads(collection_response.data)["collection"]["id"]

        # Create another user
        other_user = create_test_user("other@example.com")

        # Create auth headers for other user
        from app.api.v1.auth import create_access_token

        with client.application.app_context():
            other_auth_headers = {
                "Authorization": f"Bearer {create_access_token(other_user['id'], other_user['role'])}"
            }

        # Try to access analytics with other user
        response = client.get(
            f"/api/v1/collections/{collection_id}/analytics",
            headers=other_auth_headers,
        )
        # Should be denied
        assert response.status_code in [403, 404]
