"""GitOps synchronization service for IceFlows CI/CD pipelines.

Handles syncing IceFlows configurations from YAML files in a GitOps repository.
Supports parsing, validating, and syncing flow definitions including stages, tests,
calls, and approval configurations.

Copyright (c) 2026 Penguin Tech Inc.
License: Limited AGPL3
"""

import json
import logging
import os
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from typing import Optional

import yaml
from app.models import get_db

logger = logging.getLogger(__name__)


class GitOpsSyncError(Exception):
    """Custom exception for GitOps sync failures."""

    pass


@dataclass(slots=True)
class YamlFlowConfig:
    """Data class for parsed YAML flow configuration."""

    api_version: str
    kind: str
    metadata: dict
    spec: dict


@dataclass(slots=True)
class SyncChanges:
    """Data class for tracking sync changes."""

    stages_added: int = 0
    stages_updated: int = 0
    stages_deleted: int = 0
    tests_synced: int = 0
    calls_synced: int = 0
    approvers_synced: int = 0


class GitOpsSyncService:
    """Service for syncing IceFlows configurations from GitOps repositories."""

    SUPPORTED_API_VERSIONS = ["iceflows/v1"]
    SUPPORTED_KINDS = ["Flow"]
    REQUIRED_METADATA_FIELDS = ["name", "description"]
    REQUIRED_SPEC_FIELDS = ["repository", "stages"]

    def __init__(self, git_operations=None, db=None):
        """
        Initialize GitOpsSyncService.

        Args:
            git_operations: GitOperations instance for repository operations
            db: PyDAL database instance (uses get_db() if not provided)
        """
        self.git_operations = git_operations
        self.db = db or get_db()
        logger.info("Initialized GitOpsSyncService")

    def sync_flow_from_yaml(self, yaml_content: str, user_id: int) -> dict:
        """
        Parse YAML and create or update flow.

        Args:
            yaml_content: YAML content as string
            user_id: ID of the user performing the sync

        Returns:
            Dictionary with sync result including flow_id, created status, and changes

        Raises:
            GitOpsSyncError: If YAML is invalid or sync fails
        """
        try:
            # Parse YAML
            yaml_config = self._parse_yaml(yaml_content)

            # Validate schema
            is_valid, errors = self.validate_yaml_schema(yaml_content)
            if not is_valid:
                raise GitOpsSyncError(f"YAML validation failed: {'; '.join(errors)}")

            # Get or create flow
            flow_id, created = self._get_or_create_flow(yaml_config, user_id)

            # Sync stages
            changes = SyncChanges()
            self._sync_stages(flow_id, yaml_config["spec"].get("stages", []), changes)

            logger.info(
                f"Successfully synced flow {flow_id} "
                f"(created={created}, changes={changes})"
            )

            return {
                "success": True,
                "flow_id": flow_id,
                "created": created,
                "changes": {
                    "stages_added": changes.stages_added,
                    "stages_updated": changes.stages_updated,
                    "stages_deleted": changes.stages_deleted,
                    "tests_synced": changes.tests_synced,
                    "calls_synced": changes.calls_synced,
                    "approvers_synced": changes.approvers_synced,
                },
                "errors": [],
            }

        except GitOpsSyncError as e:
            logger.error(f"GitOps sync failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during GitOps sync: {str(e)}")
            raise GitOpsSyncError(f"Sync failed: {str(e)}")

    def sync_from_gitops_repo(self, flow_id: int, git_token: str = None) -> dict:
        """
        Clone GitOps repo, find YAML files, and sync flow.

        Args:
            flow_id: ID of the flow to sync
            git_token: Git API token for authenticated access

        Returns:
            Dictionary with sync result

        Raises:
            GitOpsSyncError: If repo cloning or sync fails
        """
        if not self.git_operations:
            raise GitOpsSyncError("GitOperations instance required for repo syncing")

        repo_path = None
        try:
            # Get flow from database
            flow = self.db(self.db.iceflows.id == flow_id).select().first()
            if not flow:
                raise GitOpsSyncError(f"Flow {flow_id} not found")

            if not flow.gitops_enabled:
                raise GitOpsSyncError(f"GitOps not enabled for flow {flow_id}")

            # Create temporary directory for clone
            repo_path = tempfile.mkdtemp(prefix="iceflows_gitops_")
            logger.info(f"Created temporary directory: {repo_path}")

            # Clone GitOps repository
            logger.info(f"Cloning GitOps repo: {flow.gitops_repo_url}")
            # Note: This assumes git_operations is initialized with the repo
            # In practice, you may need to re-initialize it for the GitOps repo
            clone_path = self.git_operations.clone_repo(
                repo_path, branch=flow.gitops_branch
            )

            # Find YAML files in the specified path
            yaml_files = self._find_yaml_files(clone_path, flow.gitops_path or ".")

            if not yaml_files:
                raise GitOpsSyncError(
                    f"No YAML files found in {flow.gitops_repo_url}:"
                    f"{flow.gitops_path}"
                )

            logger.info(f"Found {len(yaml_files)} YAML files to process")

            # Process each YAML file
            all_errors = []
            changes = SyncChanges()

            for yaml_file in yaml_files:
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    result = self.sync_flow_from_yaml(content, flow.created_by_id)

                    # Aggregate changes
                    changes.stages_added += result["changes"]["stages_added"]
                    changes.stages_updated += result["changes"]["stages_updated"]
                    changes.stages_deleted += result["changes"]["stages_deleted"]
                    changes.tests_synced += result["changes"]["tests_synced"]
                    changes.calls_synced += result["changes"]["calls_synced"]
                    changes.approvers_synced += result["changes"]["approvers_synced"]

                except GitOpsSyncError as e:
                    all_errors.append(f"{yaml_file}: {str(e)}")
                    logger.warning(f"Error syncing {yaml_file}: {str(e)}")

            success = len(all_errors) == 0

            return {
                "success": success,
                "flow_id": flow_id,
                "yaml_files_processed": len(yaml_files),
                "changes": {
                    "stages_added": changes.stages_added,
                    "stages_updated": changes.stages_updated,
                    "stages_deleted": changes.stages_deleted,
                    "tests_synced": changes.tests_synced,
                    "calls_synced": changes.calls_synced,
                    "approvers_synced": changes.approvers_synced,
                },
                "errors": all_errors,
            }

        except GitOpsSyncError as e:
            logger.error(f"GitOps repo sync failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during repo sync: {str(e)}")
            raise GitOpsSyncError(f"Repo sync failed: {str(e)}")
        finally:
            if repo_path and os.path.exists(repo_path):
                try:
                    shutil.rmtree(repo_path)
                    logger.info(f"Cleaned up temporary directory: {repo_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {repo_path}: {str(e)}")

    def validate_yaml_schema(self, yaml_content: str) -> tuple[bool, list[str]]:
        """
        Validate YAML against schema.

        Args:
            yaml_content: YAML content as string

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        try:
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                errors.append("YAML must be a dictionary")
                return False, errors

            # Check apiVersion
            api_version = data.get("apiVersion")
            if api_version not in self.SUPPORTED_API_VERSIONS:
                errors.append(
                    f"Unsupported apiVersion: {api_version}. "
                    f"Must be one of: {self.SUPPORTED_API_VERSIONS}"
                )

            # Check kind
            kind = data.get("kind")
            if kind not in self.SUPPORTED_KINDS:
                errors.append(
                    f"Unsupported kind: {kind}. "
                    f"Must be one of: {self.SUPPORTED_KINDS}"
                )

            # Check metadata
            metadata = data.get("metadata")
            if not metadata:
                errors.append("metadata section is required")
            else:
                for field_name in self.REQUIRED_METADATA_FIELDS:
                    if field_name not in metadata:
                        errors.append(f"metadata.{field_name} is required")

            # Check spec
            spec = data.get("spec")
            if not spec:
                errors.append("spec section is required")
            else:
                for field_name in self.REQUIRED_SPEC_FIELDS:
                    if field_name not in spec:
                        errors.append(f"spec.{field_name} is required")

                # Validate repository spec
                repo = spec.get("repository", {})
                if repo:
                    if "url" not in repo:
                        errors.append("spec.repository.url is required")
                    if "provider" not in repo:
                        errors.append("spec.repository.provider is required")
                    elif repo["provider"] not in ["github", "gitlab"]:
                        errors.append(
                            f"Invalid repository provider: {repo['provider']}"
                        )

                # Validate stages
                stages = spec.get("stages", [])
                if not isinstance(stages, list):
                    errors.append("spec.stages must be a list")
                else:
                    for idx, stage in enumerate(stages):
                        if not isinstance(stage, dict):
                            errors.append(f"spec.stages[{idx}] must be a dictionary")
                        else:
                            if "name" not in stage:
                                errors.append(f"spec.stages[{idx}].name is required")
                            if "branch" not in stage:
                                errors.append(f"spec.stages[{idx}].branch is required")
                            if "order" not in stage:
                                errors.append(f"spec.stages[{idx}].order is required")

        except yaml.YAMLError as e:
            errors.append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return len(errors) == 0, errors

    def diff_flow_config(self, yaml_config: dict, flow_id: int) -> dict:
        """
        Show changes before applying sync.

        Args:
            yaml_config: Parsed YAML configuration
            flow_id: ID of the flow to compare against

        Returns:
            Dictionary showing differences between YAML and current DB state
        """
        try:
            flow = self.db(self.db.iceflows.id == flow_id).select().first()
            if not flow:
                return {
                    "status": "new",
                    "message": "Flow does not exist - will be created",
                }

            diff = {"status": "update", "changes": {}}

            # Compare repository settings
            spec_repo = yaml_config["spec"].get("repository", {})
            if flow.repository_url != spec_repo.get("url"):
                diff["changes"]["repository_url"] = {
                    "old": flow.repository_url,
                    "new": spec_repo.get("url"),
                }

            # Compare stages
            yaml_stages = {s["name"]: s for s in yaml_config["spec"].get("stages", [])}
            db_stages = self.db(self.db.iceflows_stages.flow_id == flow_id).select()
            db_stage_names = {s.display_name: s for s in db_stages}

            diff["changes"]["stages"] = {
                "added": list(set(yaml_stages.keys()) - set(db_stage_names.keys())),
                "removed": list(set(db_stage_names.keys()) - set(yaml_stages.keys())),
                "updated": list(set(yaml_stages.keys()) & set(db_stage_names.keys())),
            }

            return diff

        except Exception as e:
            logger.error(f"Error comparing flow config: {str(e)}")
            return {
                "status": "error",
                "message": f"Error comparing config: {str(e)}",
            }

    def _parse_yaml(self, content: str) -> dict:
        """
        Parse YAML with error handling.

        Args:
            content: YAML content as string

        Returns:
            Parsed YAML as dictionary

        Raises:
            GitOpsSyncError: If parsing fails
        """
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                raise GitOpsSyncError("YAML must contain a dictionary")
            return data
        except yaml.YAMLError as e:
            raise GitOpsSyncError(f"YAML parsing failed: {str(e)}")
        except Exception as e:
            raise GitOpsSyncError(f"Failed to parse YAML: {str(e)}")

    def _get_or_create_flow(self, yaml_config: dict, user_id: int) -> tuple[int, bool]:
        """
        Get or create flow from YAML config.

        Returns:
            Tuple of (flow_id, created) where created is True if newly created
        """
        metadata = yaml_config.get("metadata", {})
        spec = yaml_config.get("spec", {})
        repo = spec.get("repository", {})

        flow_name = metadata.get("name")
        repository_url = repo.get("url")
        repository_provider = repo.get("provider")

        try:
            # Try to find existing flow by name
            existing_flow = self.db(self.db.iceflows.name == flow_name).select().first()

            if existing_flow:
                # Update existing flow
                flow_id = existing_flow.id
                self.db(self.db.iceflows.id == flow_id).update(
                    name=flow_name,
                    description=metadata.get("description", ""),
                    repository_url=repository_url,
                    repository_provider=repository_provider,
                    repository_name=repo.get("name", ""),
                    default_branch=repo.get("defaultBranch", "main"),
                )
                self.db.commit()
                logger.info(f"Updated existing flow: {flow_id}")
                return flow_id, False

            # Create new flow
            flow_id = self.db.iceflows.insert(
                flow_id=str(uuid.uuid4()),
                name=flow_name,
                description=metadata.get("description", ""),
                repository_url=repository_url,
                repository_provider=repository_provider,
                repository_name=repo.get("name", ""),
                default_branch=repo.get("defaultBranch", "main"),
                status="draft",
                created_by_id=user_id,
            )
            self.db.commit()
            logger.info(f"Created new flow: {flow_id}")
            return flow_id, True

        except Exception as e:
            self.db.rollback()
            raise GitOpsSyncError(f"Failed to create/update flow: {str(e)}")

    def _sync_stages(
        self, flow_id: int, stages_config: list, changes: SyncChanges
    ) -> None:
        """
        Sync stages from YAML config.

        Args:
            flow_id: ID of the flow
            stages_config: List of stage configurations from YAML
            changes: SyncChanges object to track changes
        """
        try:
            # Get existing stages
            existing_stages = self.db(
                self.db.iceflows_stages.flow_id == flow_id
            ).select()
            existing_stage_names = {s.display_name: s for s in existing_stages}
            yaml_stage_names = {s.get("name") for s in stages_config}

            # Delete stages not in YAML
            for stage_name, stage in existing_stage_names.items():
                if stage_name not in yaml_stage_names:
                    self.db(self.db.iceflows_stages.id == stage.id).delete()
                    changes.stages_deleted += 1
                    logger.info(f"Deleted stage: {stage_name}")

            # Create/update stages
            for stage_config in stages_config:
                stage_name = stage_config.get("name")
                existing_stage = existing_stage_names.get(stage_name)

                approval_config = stage_config.get("approval", {})
                stage_order = stage_config.get("order", 0)

                if existing_stage:
                    # Update existing stage
                    self.db(self.db.iceflows_stages.id == existing_stage.id).update(
                        stage_order=stage_order,
                        branch_name=stage_config.get("branch", ""),
                        display_name=stage_name,
                        description=stage_config.get("description", ""),
                        is_production=stage_config.get("isProduction", False),
                        require_approval=approval_config.get("required", True),
                        min_approvers=approval_config.get("minApprovers", 1),
                        override_min_approvers=approval_config.get(
                            "overrideMinApprovers", 2
                        ),
                    )
                    self.db.commit()
                    changes.stages_updated += 1
                    logger.info(f"Updated stage: {stage_name}")
                    stage_id = existing_stage.id
                else:
                    # Create new stage
                    stage_id = self.db.iceflows_stages.insert(
                        stage_id=str(uuid.uuid4()),
                        flow_id=flow_id,
                        stage_order=stage_order,
                        branch_name=stage_config.get("branch", ""),
                        display_name=stage_name,
                        description=stage_config.get("description", ""),
                        is_production=stage_config.get("isProduction", False),
                        require_approval=approval_config.get("required", True),
                        min_approvers=approval_config.get("minApprovers", 1),
                        override_min_approvers=approval_config.get(
                            "overrideMinApprovers", 2
                        ),
                    )
                    self.db.commit()
                    changes.stages_added += 1
                    logger.info(f"Created new stage: {stage_name}")

                # Sync tests and calls for this stage
                self._sync_stage_tests(stage_id, stage_config.get("tests", []), changes)
                self._sync_stage_calls(stage_id, stage_config.get("calls", []), changes)

        except Exception as e:
            self.db.rollback()
            raise GitOpsSyncError(f"Failed to sync stages: {str(e)}")

    def _sync_stage_tests(
        self, stage_id: int, tests_config: list, changes: SyncChanges
    ) -> None:
        """
        Sync tests from YAML config.

        Args:
            stage_id: ID of the stage
            tests_config: List of test configurations from YAML
            changes: SyncChanges object to track changes
        """
        try:
            # Delete existing tests for this stage
            self.db(self.db.iceflows_stage_tests.stage_id == stage_id).delete()
            self.db.commit()

            # Create new tests from YAML
            for idx, test_config in enumerate(tests_config):
                test_id = self.db.iceflows_stage_tests.insert(
                    test_id=str(uuid.uuid4()),
                    stage_id=stage_id,
                    name=test_config.get("name", f"Test {idx}"),
                    test_type=test_config.get("type", "custom"),
                    command=test_config.get("command", ""),
                    execution_order=idx,
                    is_blocking=test_config.get("blocking", True),
                    is_required=test_config.get("required", True),
                    timeout_seconds=test_config.get("timeoutSeconds", 600),
                )
                self.db.commit()
                changes.tests_synced += 1

            logger.info(f"Synced {len(tests_config)} tests for stage {stage_id}")

        except Exception as e:
            self.db.rollback()
            raise GitOpsSyncError(f"Failed to sync tests: {str(e)}")

    def _sync_stage_calls(
        self, stage_id: int, calls_config: list, changes: SyncChanges
    ) -> None:
        """
        Sync stage calls (IceStreams/IceRuns triggers) from YAML config.

        Args:
            stage_id: ID of the stage
            calls_config: List of call configurations from YAML
            changes: SyncChanges object to track changes
        """
        try:
            # Delete existing calls for this stage
            self.db(self.db.iceflows_stage_calls.stage_id == stage_id).delete()
            self.db.commit()

            # Create new calls from YAML
            for idx, call_config in enumerate(calls_config):
                call_type = call_config.get("type", "icestreams").lower()
                if call_type == "icestreams":
                    call_type = "icestreams"
                elif call_type == "iceruns":
                    call_type = "iceruns"
                else:
                    logger.warning(
                        f"Unknown call type: {call_type}, defaulting to icestreams"
                    )
                    call_type = "icestreams"

                call_id = self.db.iceflows_stage_calls.insert(
                    call_id=str(uuid.uuid4()),
                    stage_id=stage_id,
                    name=call_config.get("name", f"Call {idx}"),
                    call_type=call_type,
                    target_id=call_config.get("targetId"),
                    trigger_on=call_config.get("triggerOn", "post_merge"),
                    execution_order=idx,
                    is_blocking=call_config.get("blocking", True),
                    timeout_seconds=call_config.get("timeoutSeconds", 300),
                    retry_count=call_config.get("retryCount", 0),
                )
                self.db.commit()
                changes.calls_synced += 1

            logger.info(f"Synced {len(calls_config)} calls for stage {stage_id}")

        except Exception as e:
            self.db.rollback()
            raise GitOpsSyncError(f"Failed to sync calls: {str(e)}")

    @staticmethod
    def _find_yaml_files(root_path: str, target_path: str = ".") -> list[str]:
        """
        Find all YAML files in the specified directory.

        Args:
            root_path: Root path to search in
            target_path: Relative path within root to search (default: ".")

        Returns:
            List of absolute paths to YAML files found
        """
        yaml_files = []
        search_path = os.path.join(root_path, target_path)

        if not os.path.exists(search_path):
            logger.warning(f"Search path does not exist: {search_path}")
            return yaml_files

        try:
            for root, dirs, files in os.walk(search_path):
                for file in files:
                    if file.endswith((".yaml", ".yml")):
                        yaml_files.append(os.path.join(root, file))
                        logger.debug(f"Found YAML file: {os.path.join(root, file)}")
        except Exception as e:
            logger.error(f"Error searching for YAML files: {str(e)}")

        return yaml_files
