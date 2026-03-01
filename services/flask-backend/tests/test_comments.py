"""Tests for Drawing Comments API endpoints."""
import pytest


class TestListComments:
    def test_list_requires_auth(self, client):
        response = client.get("/api/v1/drawings/1/comments")
        assert response.status_code == 401

    def test_list_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.get("/api/v1/drawings/999999/comments", headers=auth_headers)
        assert response.status_code == 404

    def test_list_with_auth(self, client, auth_headers):
        response = client.get("/api/v1/drawings/999999/comments", headers=auth_headers)
        assert response.status_code != 401


class TestCreateComment:
    def test_create_requires_auth(self, client):
        response = client.post(
            "/api/v1/drawings/1/comments",
            json={"content": "This is a comment"},
        )
        assert response.status_code == 401

    def test_create_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/comments",
            json={"content": "This is a comment"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_empty_content_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Comment Test Drawing",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/comments",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_missing_body_returns_400(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/comments",
            json=None,
            headers=auth_headers,
        )
        assert response.status_code in (400, 404)


class TestGetComment:
    def test_get_requires_auth(self, client):
        response = client.get("/api/v1/drawings/1/comments/1")
        assert response.status_code == 401

    def test_get_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/drawings/999999/comments/1", headers=auth_headers
        )
        assert response.status_code == 404

    def test_get_nonexistent_comment_returns_404(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Drawing for Comment Get Test",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        response = client.get(
            f"/api/v1/drawings/{drawing_id}/comments/999999", headers=auth_headers
        )
        assert response.status_code == 404


class TestUpdateComment:
    def test_update_requires_auth(self, client):
        response = client.put(
            "/api/v1/drawings/1/comments/1", json={"content": "Updated"}
        )
        assert response.status_code == 401

    def test_update_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/drawings/999999/comments/1",
            json={"content": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteComment:
    def test_delete_requires_auth(self, client):
        response = client.delete("/api/v1/drawings/1/comments/1")
        assert response.status_code == 401

    def test_delete_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.delete(
            "/api/v1/drawings/999999/comments/1", headers=auth_headers
        )
        assert response.status_code == 404


class TestResolveComment:
    def test_resolve_requires_auth(self, client):
        response = client.post("/api/v1/drawings/1/comments/1/resolve")
        assert response.status_code == 401

    def test_resolve_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/comments/1/resolve", headers=auth_headers
        )
        assert response.status_code == 404

    def test_resolve_nonexistent_comment_returns_404(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Drawing for Resolve Test",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            db.commit()

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/comments/999999/resolve",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestCommentReplies:
    def test_list_replies_requires_auth(self, client):
        response = client.get("/api/v1/drawings/1/comments/1/replies")
        assert response.status_code == 401

    def test_list_replies_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.get(
            "/api/v1/drawings/999999/comments/1/replies", headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_reply_requires_auth(self, client):
        response = client.post(
            "/api/v1/drawings/1/comments/1/replies",
            json={"content": "A reply"},
        )
        assert response.status_code == 401

    def test_create_reply_nonexistent_drawing_returns_404(self, client, auth_headers):
        response = client.post(
            "/api/v1/drawings/999999/comments/1/replies",
            json={"content": "A reply"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_reply_empty_content_returns_400(self, client, auth_headers, app):
        with app.app_context():
            from app.models import get_db
            db = get_db()
            drawing_id = db.drawings.insert(
                tenant_id=1,
                title="Drawing for Reply Test",
                owner_id=1,
                user_id=1,
                created_by_id=1,
            )
            comment_id = db.comments.insert(
                drawing_id=drawing_id,
                author_id=1,
                comment_text="Original comment",
                is_resolved=False,
            )
            db.commit()

        response = client.post(
            f"/api/v1/drawings/{drawing_id}/comments/{comment_id}/replies",
            json={"content": ""},
            headers=auth_headers,
        )
        assert response.status_code == 400
