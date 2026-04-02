"""Test suite for GitOps synchronization service.

Tests cover YAML parsing, validation, flow creation/update, stage syncing,
and error handling in the GitOpsSyncService.
"""

import pytest
import yaml
from app.services.gitops_sync import (GitOpsSyncError, GitOpsSyncService,
                                      SyncChanges)


class TestGitOpsSyncYAMLParsing:
    """Tests for YAML parsing and validation."""

    @pytest.fixture
    def sync_service(self, app):
        """Create a GitOpsSyncService instance."""
        with app.app_context():
            return GitOpsSyncService()

    def test_parse_valid_yaml_returns_dict(self, sync_service):
        """Test parsing valid YAML returns dictionary."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow description
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        result = sync_service._parse_yaml(yaml_content)
        assert isinstance(result, dict)
        assert result["apiVersion"] == "iceflows/v1"
        assert result["kind"] == "Flow"
        assert result["metadata"]["name"] == "test-flow"

    def test_parse_invalid_yaml_raises_error(self, sync_service):
        """Test parsing invalid YAML raises GitOpsSyncError."""
        invalid_yaml = "invalid: yaml: content: [unclosed"
        with pytest.raises(GitOpsSyncError):
            sync_service._parse_yaml(invalid_yaml)

    def test_parse_non_dict_yaml_raises_error(self, sync_service):
        """Test parsing YAML that is not a dict raises error."""
        yaml_content = "- item1\n- item2"
        with pytest.raises(GitOpsSyncError, match="must contain a dictionary"):
            sync_service._parse_yaml(yaml_content)

    def test_parse_empty_yaml_raises_error(self, sync_service):
        """Test parsing empty YAML raises error."""
        with pytest.raises(GitOpsSyncError):
            sync_service._parse_yaml("")

    def test_validate_yaml_schema_valid_flow(self, sync_service):
        """Test validation passes for valid flow YAML."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_yaml_missing_apiversion(self, sync_service):
        """Test validation fails when apiVersion is missing."""
        yaml_content = """
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("apiVersion" in error for error in errors)

    def test_validate_yaml_unsupported_apiversion(self, sync_service):
        """Test validation fails with unsupported apiVersion."""
        yaml_content = """
apiVersion: iceflows/v2
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("Unsupported apiVersion" in error for error in errors)

    def test_validate_yaml_wrong_kind(self, sync_service):
        """Test validation fails with wrong kind."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Pipeline
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("kind" in error for error in errors)

    def test_validate_yaml_missing_metadata(self, sync_service):
        """Test validation fails when metadata section missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("metadata" in error for error in errors)

    def test_validate_yaml_missing_metadata_name(self, sync_service):
        """Test validation fails when metadata.name is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("metadata.name" in error for error in errors)

    def test_validate_yaml_missing_spec(self, sync_service):
        """Test validation fails when spec section missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("spec" in error for error in errors)

    def test_validate_yaml_missing_repository_url(self, sync_service):
        """Test validation fails when repository.url is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("repository.url" in error for error in errors)

    def test_validate_yaml_invalid_provider(self, sync_service):
        """Test validation fails with invalid repository provider."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: bitbucket
  stages:
    - name: build
      branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("provider" in error for error in errors)

    def test_validate_yaml_missing_stages(self, sync_service):
        """Test validation fails when stages is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("stages" in error for error in errors)

    def test_validate_yaml_stage_missing_name(self, sync_service):
        """Test validation fails when stage.name is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - branch: main
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("stages[0].name" in error for error in errors)

    def test_validate_yaml_stage_missing_branch(self, sync_service):
        """Test validation fails when stage.branch is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      order: 1
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("stages[0].branch" in error for error in errors)

    def test_validate_yaml_stage_missing_order(self, sync_service):
        """Test validation fails when stage.order is missing."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Test flow
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
"""
        is_valid, errors = sync_service.validate_yaml_schema(yaml_content)
        assert is_valid is False
        assert any("stages[0].order" in error for error in errors)


class TestGitOpsSyncFlow:
    """Tests for GitOps flow synchronization."""

    @pytest.fixture
    def sync_service(self, app):
        """Create a GitOpsSyncService instance."""
        with app.app_context():
            return GitOpsSyncService()

    def test_sync_creates_new_flow(self, app, sync_service, test_user):
        """Test syncing YAML creates a new flow when it doesn't exist."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: new-flow
  description: New flow description
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["created"] is True
        assert result["flow_id"] is not None
        assert result["changes"]["stages_added"] == 1

    def test_sync_updates_existing_flow(self, app, sync_service, test_user, db):
        """Test syncing YAML updates an existing flow."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: existing-flow
  description: Original description
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        with app.app_context():
            # Create initial flow
            result1 = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])
            flow_id = result1["flow_id"]

            # Update YAML
            updated_yaml = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: existing-flow
  description: Updated description
spec:
  repository:
    url: https://github.com/test/repo-updated
    provider: github
  stages:
    - name: build
      branch: develop
      order: 1
"""
            result2 = sync_service.sync_flow_from_yaml(updated_yaml, test_user["id"])

        assert result2["success"] is True
        assert result2["created"] is False
        assert result2["flow_id"] == flow_id

    def test_sync_adds_multiple_stages(self, app, sync_service, test_user):
        """Test syncing YAML with multiple stages."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: multi-stage-flow
  description: Flow with multiple stages
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
    - name: test
      branch: develop
      order: 2
    - name: deploy
      branch: production
      order: 3
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["changes"]["stages_added"] == 3

    def test_sync_with_stage_approval_config(self, app, sync_service, test_user):
        """Test syncing YAML with approval configuration."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: approval-flow
  description: Flow with approval config
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: deploy
      branch: production
      order: 1
      isProduction: true
      approval:
        required: true
        minApprovers: 2
        overrideMinApprovers: 3
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["changes"]["stages_added"] == 1

    def test_sync_with_tests_in_stage(self, app, sync_service, test_user):
        """Test syncing YAML with tests in stages."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: test-flow
  description: Flow with tests
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
      tests:
        - name: unit-tests
          type: custom
          command: pytest
          blocking: true
          required: true
          timeoutSeconds: 600
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["changes"]["tests_synced"] == 1

    def test_sync_with_calls_in_stage(self, app, sync_service, test_user):
        """Test syncing YAML with calls (IceStreams/IceRuns) in stages."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: call-flow
  description: Flow with calls
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
      calls:
        - name: trigger-icestreams
          type: icestreams
          targetId: stream-1
          triggerOn: post_merge
          blocking: true
          timeoutSeconds: 300
          retryCount: 1
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["changes"]["calls_synced"] == 1

    def test_sync_invalid_yaml_raises_error(self, app, sync_service, test_user):
        """Test syncing invalid YAML raises GitOpsSyncError."""
        with app.app_context():
            with pytest.raises(GitOpsSyncError):
                sync_service.sync_flow_from_yaml("invalid: [yaml", test_user["id"])

    def test_sync_missing_required_fields_raises_error(
        self, app, sync_service, test_user
    ):
        """Test syncing YAML missing required fields raises error."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  description: Missing name
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
"""
        with app.app_context():
            with pytest.raises(GitOpsSyncError, match="validation failed"):
                sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

    def test_sync_wrong_apiversion_raises_error(self, app, sync_service, test_user):
        """Test syncing YAML with wrong apiVersion raises error."""
        yaml_content = """
apiVersion: iceflows/v2
kind: Flow
metadata:
  name: test
  description: Test
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        with app.app_context():
            with pytest.raises(GitOpsSyncError, match="validation failed"):
                sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

    def test_sync_wrong_kind_raises_error(self, app, sync_service, test_user):
        """Test syncing YAML with wrong kind raises error."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Pipeline
metadata:
  name: test
  description: Test
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        with app.app_context():
            with pytest.raises(GitOpsSyncError, match="validation failed"):
                sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

    def test_sync_with_metadata_labels(self, app, sync_service, test_user):
        """Test syncing YAML with metadata labels and annotations."""
        yaml_content = """
apiVersion: iceflows/v1
kind: Flow
metadata:
  name: labeled-flow
  description: Flow with labels
  labels:
    team: engineering
    environment: production
  annotations:
    owner: devops
spec:
  repository:
    url: https://github.com/test/repo
    provider: github
  stages:
    - name: build
      branch: main
      order: 1
"""
        with app.app_context():
            result = sync_service.sync_flow_from_yaml(yaml_content, test_user["id"])

        assert result["success"] is True
        assert result["created"] is True


class TestSyncChangesTracking:
    """Tests for SyncChanges data class."""

    def test_sync_changes_initialization(self):
        """Test SyncChanges initializes with zeros."""
        changes = SyncChanges()
        assert changes.stages_added == 0
        assert changes.stages_updated == 0
        assert changes.stages_deleted == 0
        assert changes.tests_synced == 0
        assert changes.calls_synced == 0
        assert changes.approvers_synced == 0

    def test_sync_changes_increments(self):
        """Test SyncChanges can track increments."""
        changes = SyncChanges()
        changes.stages_added += 2
        changes.tests_synced += 3
        assert changes.stages_added == 2
        assert changes.tests_synced == 3
