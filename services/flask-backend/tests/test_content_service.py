"""Tests for ContentService - drawing content and version management."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models import get_db
from app.services.content_service import ContentService, VersionData
from app.storage import StorageError


class TestStoragePath:
    """Test storage path generation."""

    def test_get_storage_path_format(self):
        """Test that storage path follows correct format."""
        path = ContentService._get_storage_path(tenant_id=1, drawing_id=42, version=3)
        assert path == "tenants/1/drawings/42/versions/v3.json"

    def test_get_storage_path_with_large_ids(self):
        """Test storage path with large ID values."""
        path = ContentService._get_storage_path(
            tenant_id=99999, drawing_id=888888, version=1000
        )
        assert "tenants/99999/drawings/888888" in path
        assert "v1000.json" in path


class TestSaveContent:
    """Test saving drawing content and version creation."""

    def test_save_content_creates_version(self, app, db, create_test_user):
        """Test that saving content creates a version record."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            # Create a drawing
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            # Mock storage provider
            with patch(
                "app.services.content_service.get_storage_provider"
            ) as mock_storage:
                mock_storage_instance = MagicMock()
                mock_storage.return_value = mock_storage_instance

                # Save content
                content = {"shapes": [{"id": "1", "type": "rect"}]}
                version = ContentService.save_content(
                    drawing_id=drawing,
                    content_json=content,
                    user_id=user["id"],
                    change_summary="Initial version",
                )

                # Verify version was created
                assert version == 1
                version_record = (
                    db(db.drawing_versions.drawing_id == drawing).select().first()
                )
                assert version_record is not None
                assert version_record.version_number == 1
                assert version_record.change_summary == "Initial version"

    def test_save_content_increments_version(self, app, db, create_test_user):
        """Test that successive saves increment version number."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            # Create a drawing
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Save first version
                content1 = {"shapes": [{"id": "1"}]}
                v1 = ContentService.save_content(
                    drawing_id=drawing,
                    content_json=content1,
                    user_id=user["id"],
                )
                assert v1 == 1

                # Save second version
                content2 = {"shapes": [{"id": "1"}, {"id": "2"}]}
                v2 = ContentService.save_content(
                    drawing_id=drawing,
                    content_json=content2,
                    user_id=user["id"],
                )
                assert v2 == 2

                # Save third version
                content3 = {"shapes": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}
                v3 = ContentService.save_content(
                    drawing_id=drawing,
                    content_json=content3,
                    user_id=user["id"],
                )
                assert v3 == 3

    def test_save_content_not_found_raises_error(self, app, create_test_user):
        """Test that saving to nonexistent drawing raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            content = {"shapes": []}
            with pytest.raises(ValueError, match="Drawing not found"):
                ContentService.save_content(
                    drawing_id=99999,
                    content_json=content,
                    user_id=user["id"],
                )

    def test_save_content_empty_json_raises_error(self, app, db, create_test_user):
        """Test that empty content raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with pytest.raises(ValueError, match="Content must be a valid"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json=None,
                    user_id=user["id"],
                )

    def test_save_content_invalid_json_raises_error(self, app, db, create_test_user):
        """Test that non-dict content raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with pytest.raises(ValueError, match="Content must be a valid"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json="not a dict",
                    user_id=user["id"],
                )

    def test_save_content_storage_failure_raises_error(self, app, db, create_test_user):
        """Test that storage failure raises StorageError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch(
                "app.services.content_service.get_storage_provider"
            ) as mock_storage:
                mock_storage_instance = MagicMock()
                mock_storage_instance.upload.side_effect = Exception("Upload failed")
                mock_storage.return_value = mock_storage_instance

                content = {"shapes": []}
                with pytest.raises(ValueError, match="Failed to save content"):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json=content,
                        user_id=user["id"],
                    )

    def test_save_content_updates_drawing_updated_by(self, app, db, create_test_user):
        """Test that saving content updates drawing's updated_by_id."""
        user1 = create_test_user(email="user1@example.com")
        user2 = create_test_user(email="user2@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user1["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"shapes": []},
                    user_id=user2["id"],
                )

                updated_drawing = db(db.drawings.id == drawing).select().first()
                assert updated_drawing.updated_by_id == user2["id"]


class TestGetContent:
    """Test retrieving drawing content."""

    def test_get_content_latest_version(self, app, db, create_test_user):
        """Test getting content without version spec returns latest."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Create multiple versions
                for i in range(3):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1},
                        user_id=user["id"],
                    )

                # Get latest without specifying version
                content = ContentService.get_content(
                    drawing_id=drawing,
                    user_id=user["id"],
                )
                assert content["version"] == 3

    def test_get_content_specific_version(self, app, db, create_test_user):
        """Test getting content for a specific version number."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Create multiple versions with distinct content
                for i in range(3):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1, "data": f"content-{i+1}"},
                        user_id=user["id"],
                    )

                # Get specific version
                content_v2 = ContentService.get_content(
                    drawing_id=drawing,
                    user_id=user["id"],
                    version=2,
                )
                assert content_v2["version"] == 2
                assert content_v2["data"] == "content-2"

    def test_get_content_not_found_raises_error(self, app, create_test_user):
        """Test getting content for nonexistent drawing raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            with pytest.raises(ValueError, match="Drawing not found"):
                ContentService.get_content(
                    drawing_id=99999,
                    user_id=user["id"],
                )

    def test_get_content_version_not_found_raises_error(
        self, app, db, create_test_user
    ):
        """Test getting nonexistent version raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )

                with pytest.raises(ValueError, match="Version not found"):
                    ContentService.get_content(
                        drawing_id=drawing,
                        user_id=user["id"],
                        version=99,
                    )

    def test_get_content_from_database_json(self, app, db, create_test_user):
        """Test that content is retrieved from database JSON field."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            # Insert version directly with content_json
            content_data = {"shapes": [{"id": "1", "label": "Test"}]}
            db.drawing_versions.insert(
                drawing_id=drawing,
                version_number=1,
                created_by_id=user["id"],
                content_json=content_data,
                storage_path="tenants/1/drawings/1/versions/v1.json",
            )
            db.commit()

            content = ContentService.get_content(
                drawing_id=drawing,
                user_id=user["id"],
            )
            assert content == content_data


class TestListVersions:
    """Test listing versions of a drawing."""

    def test_list_versions_empty_drawing(self, app, db, create_test_user):
        """Test listing versions for drawing with no versions."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            versions, total = ContentService.list_versions(
                drawing_id=drawing,
                user_id=user["id"],
            )
            assert versions == []
            assert total == 0

    def test_list_versions_returns_all(self, app, db, create_test_user):
        """Test that list_versions returns all versions."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Create multiple versions
                for i in range(5):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1},
                        user_id=user["id"],
                        change_summary=f"Change {i+1}",
                    )

                versions, total = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                )
                assert total == 5
                assert len(versions) == 5

    def test_list_versions_descending_order(self, app, db, create_test_user):
        """Test that versions are returned in descending order."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                for i in range(3):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1},
                        user_id=user["id"],
                    )

                versions, _ = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                )
                version_numbers = [v["version_number"] for v in versions]
                assert version_numbers == [3, 2, 1]

    def test_list_versions_includes_creator_info(self, app, db, create_test_user):
        """Test that list_versions includes creator information."""
        user = create_test_user(email="test@example.com", full_name="Test User")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )

                versions, _ = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                )
                assert len(versions) > 0
                assert "created_by" in versions[0]
                assert versions[0]["created_by"]["id"] == user["id"]
                assert versions[0]["created_by"]["full_name"] == "Test User"

    def test_list_versions_pagination(self, app, db, create_test_user):
        """Test pagination of versions."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                for i in range(25):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1},
                        user_id=user["id"],
                    )

                # Get first page (default per_page=20)
                page1, total = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                    page=1,
                    per_page=20,
                )
                assert total == 25
                assert len(page1) == 20

                # Get second page
                page2, _ = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                    page=2,
                    per_page=20,
                )
                assert len(page2) == 5

    def test_list_versions_drawing_not_found(self, app, create_test_user):
        """Test listing versions for nonexistent drawing raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            with pytest.raises(ValueError, match="Drawing not found"):
                ContentService.list_versions(
                    drawing_id=99999,
                    user_id=user["id"],
                )


class TestRestoreVersion:
    """Test restoring previous versions."""

    def test_restore_version_creates_new_version(self, app, db, create_test_user):
        """Test that restoring a version creates a new version."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Create versions
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 2},
                    user_id=user["id"],
                )

                # Restore version 1
                new_version = ContentService.restore_version(
                    drawing_id=drawing,
                    version=1,
                    user_id=user["id"],
                )
                assert new_version == 3

                # Verify content matches version 1
                content = ContentService.get_content(
                    drawing_id=drawing,
                    user_id=user["id"],
                    version=3,
                )
                assert content["version"] == 1

    def test_restore_version_with_summary(self, app, db, create_test_user):
        """Test restore with custom change summary."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )

                ContentService.restore_version(
                    drawing_id=drawing,
                    version=1,
                    user_id=user["id"],
                    change_summary="Manual restore",
                )

                versions, _ = ContentService.list_versions(
                    drawing_id=drawing,
                    user_id=user["id"],
                )
                assert versions[0]["change_summary"] == "Manual restore"


class TestDeleteVersion:
    """Test deleting versions."""

    def test_delete_version_removes_version(self, app, db, create_test_user):
        """Test that deleting a version removes it."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                # Create multiple versions
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 2},
                    user_id=user["id"],
                )

                # Delete version 1
                result = ContentService.delete_version(
                    drawing_id=drawing,
                    version=1,
                    user_id=user["id"],
                )
                assert result is True

                # Verify version is deleted
                with pytest.raises(ValueError):
                    ContentService.get_content(
                        drawing_id=drawing,
                        user_id=user["id"],
                        version=1,
                    )

    def test_delete_version_not_found_returns_false(self, app, db, create_test_user):
        """Test that deleting nonexistent version returns False."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                result = ContentService.delete_version(
                    drawing_id=drawing,
                    version=99,
                    user_id=user["id"],
                )
                assert result is False

    def test_delete_last_version_raises_error(self, app, db, create_test_user):
        """Test that deleting the only version raises ValueError."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1},
                    user_id=user["id"],
                )

                with pytest.raises(ValueError, match="Cannot delete the only"):
                    ContentService.delete_version(
                        drawing_id=drawing,
                        version=1,
                        user_id=user["id"],
                    )


class TestCompareVersions:
    """Test comparing versions."""

    def test_compare_versions_returns_both_contents(self, app, db, create_test_user):
        """Test that compare returns both version contents."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 1, "shapes": ["a"]},
                    user_id=user["id"],
                )
                ContentService.save_content(
                    drawing_id=drawing,
                    content_json={"version": 2, "shapes": ["a", "b"]},
                    user_id=user["id"],
                )

                result = ContentService.compare_versions(
                    drawing_id=drawing,
                    version1=1,
                    version2=2,
                    user_id=user["id"],
                )

                assert result["drawing_id"] == drawing
                assert result["version1"]["version_number"] == 1
                assert result["version1"]["content"]["version"] == 1
                assert result["version2"]["version_number"] == 2
                assert result["version2"]["content"]["version"] == 2


class TestGetLatestVersionNumber:
    """Test getting latest version number."""

    def test_get_latest_version_number_no_versions(self, app, db, create_test_user):
        """Test that latest version returns 0 when no versions exist."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            latest = ContentService.get_latest_version_number(drawing_id=drawing)
            assert latest == 0

    def test_get_latest_version_number_with_versions(self, app, db, create_test_user):
        """Test that latest version returns highest version number."""
        user = create_test_user(email="test@example.com")

        with app.app_context():
            drawing = db.drawings.insert(
                tenant_id=1,
                name="Test Drawing",
                created_by_id=user["id"],
            )
            db.commit()

            with patch("app.services.content_service.get_storage_provider"):
                for i in range(5):
                    ContentService.save_content(
                        drawing_id=drawing,
                        content_json={"version": i + 1},
                        user_id=user["id"],
                    )

                latest = ContentService.get_latest_version_number(drawing_id=drawing)
                assert latest == 5
