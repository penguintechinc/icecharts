"""Tests for GitOperations - GitHub and GitLab repository management."""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from git_operations import GitOperations, GitOperationError


@pytest.fixture
def github_ops():
    """Create GitOperations for GitHub with mocked subprocess/requests."""
    with patch("git_operations.subprocess") as mock_sub, \
         patch("git_operations.requests") as mock_req:
        mock_sub.run.return_value = MagicMock(stdout="abc123\n", stderr="", returncode=0)
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_req.request.return_value = mock_response
        ops = GitOperations(
            provider="github",
            api_token="ghp-token",
            repo_url="https://github.com/org/myrepo",
        )
        ops._mock_sub = mock_sub
        ops._mock_req = mock_req
        yield ops


@pytest.fixture
def gitlab_ops():
    """Create GitOperations for GitLab with mocked subprocess/requests."""
    with patch("git_operations.subprocess") as mock_sub, \
         patch("git_operations.requests") as mock_req:
        mock_sub.run.return_value = MagicMock(stdout="def456\n", stderr="", returncode=0)
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_req.request.return_value = mock_response
        ops = GitOperations(
            provider="gitlab",
            api_token="glpat-token",
            repo_url="https://gitlab.com/group/subgroup/myrepo",
        )
        ops._mock_sub = mock_sub
        ops._mock_req = mock_req
        yield ops


class TestProviderValidation:
    """Tests for provider validation."""

    def test_github_provider_accepted(self):
        """'github' provider is accepted."""
        ops = GitOperations(
            provider="github",
            api_token="tok",
            repo_url="https://github.com/org/repo",
        )
        assert ops.provider == "github"

    def test_gitlab_provider_accepted(self):
        """'gitlab' provider is accepted."""
        ops = GitOperations(
            provider="gitlab",
            api_token="tok",
            repo_url="https://gitlab.com/org/repo",
        )
        assert ops.provider == "gitlab"

    def test_invalid_provider_raises(self):
        """Invalid provider raises GitOperationError."""
        with pytest.raises(GitOperationError, match="Invalid provider"):
            GitOperations(
                provider="bitbucket",
                api_token="tok",
                repo_url="https://bitbucket.org/org/repo",
            )

    def test_provider_case_insensitive(self):
        """Provider is normalized to lowercase."""
        ops = GitOperations(
            provider="GitHub",
            api_token="tok",
            repo_url="https://github.com/org/repo",
        )
        assert ops.provider == "github"


class TestParseRepoUrl:
    """Tests for URL parsing."""

    def test_parse_github_url(self):
        """GitHub URL parsed to owner/repo."""
        ops = GitOperations(
            provider="github",
            api_token="tok",
            repo_url="https://github.com/myorg/myrepo",
        )
        assert ops.repo_owner == "myorg"
        assert ops.repo_name == "myrepo"

    def test_parse_github_url_with_git_suffix(self):
        """GitHub URL with .git suffix strips suffix."""
        ops = GitOperations(
            provider="github",
            api_token="tok",
            repo_url="https://github.com/myorg/myrepo.git",
        )
        assert ops.repo_name == "myrepo"

    def test_parse_gitlab_group_subgroup_url(self):
        """GitLab URL with group/subgroup parsed correctly."""
        ops = GitOperations(
            provider="gitlab",
            api_token="tok",
            repo_url="https://gitlab.com/group/subgroup/myrepo",
        )
        assert ops.repo_name == "myrepo"
        assert "group" in ops.repo_owner


class TestValidateBranchName:
    """Tests for branch name validation."""

    def test_valid_branch_name(self, github_ops):
        """Valid branch names pass validation."""
        github_ops._validate_branch_name("feature/my-feature")
        github_ops._validate_branch_name("main")
        github_ops._validate_branch_name("release/v1.2.3")

    def test_invalid_branch_name_with_special_chars(self, github_ops):
        """Branch names with shell special chars raise GitOperationError."""
        with pytest.raises(GitOperationError, match="Invalid branch name"):
            github_ops._validate_branch_name("feature; rm -rf /")

    def test_empty_branch_name_raises(self, github_ops):
        """Empty branch name raises GitOperationError."""
        with pytest.raises(GitOperationError):
            github_ops._validate_branch_name("")


class TestCloneRepo:
    """Tests for clone_repo."""

    def test_clone_repo_calls_git(self, github_ops, tmp_path):
        """clone_repo invokes git clone subprocess."""
        target = str(tmp_path / "cloned")
        with patch("os.makedirs"):
            github_ops.clone_repo(target)
        github_ops._mock_sub.run.assert_called_once()
        call_args = github_ops._mock_sub.run.call_args[0][0]
        assert "clone" in call_args

    def test_clone_repo_with_branch(self, github_ops, tmp_path):
        """clone_repo passes --branch when branch is specified."""
        target = str(tmp_path / "cloned")
        with patch("os.makedirs"):
            github_ops.clone_repo(target, branch="feature/x")
        call_args = github_ops._mock_sub.run.call_args[0][0]
        assert "--branch" in call_args
        assert "feature/x" in call_args

    def test_clone_repo_failure_raises(self, github_ops, tmp_path):
        """clone_repo raises GitOperationError on git failure."""
        github_ops._mock_sub.run.return_value = MagicMock(
            stdout="", stderr="fatal: repo not found", returncode=1
        )
        with patch("os.makedirs"):
            with pytest.raises(GitOperationError, match="Failed to clone"):
                github_ops.clone_repo(str(tmp_path / "cloned"))


class TestCheckoutBranch:
    """Tests for checkout_branch."""

    def test_checkout_branch_success(self, github_ops):
        """checkout_branch invokes git checkout."""
        github_ops.checkout_branch("/repo", "main")
        call_args = github_ops._mock_sub.run.call_args[0][0]
        assert "checkout" in call_args
        assert "main" in call_args

    def test_checkout_branch_failure_raises(self, github_ops):
        """checkout_branch raises GitOperationError on failure."""
        github_ops._mock_sub.run.return_value = MagicMock(
            stdout="", stderr="error: pathspec 'bad' did not match", returncode=1
        )
        with pytest.raises(GitOperationError, match="Failed to checkout"):
            github_ops.checkout_branch("/repo", "bad-branch")


class TestGetCommitSha:
    """Tests for get_commit_sha."""

    def test_get_commit_sha_head(self, github_ops):
        """get_commit_sha returns SHA for HEAD."""
        sha = github_ops.get_commit_sha("/repo")
        assert sha == "abc123"

    def test_get_commit_sha_branch(self, github_ops):
        """get_commit_sha returns SHA for named branch."""
        sha = github_ops.get_commit_sha("/repo", "main")
        assert sha == "abc123"

    def test_get_commit_sha_failure_raises(self, github_ops):
        """get_commit_sha raises GitOperationError on failure."""
        github_ops._mock_sub.run.return_value = MagicMock(
            stdout="", stderr="error", returncode=1
        )
        with pytest.raises(GitOperationError, match="Failed to get commit SHA"):
            github_ops.get_commit_sha("/repo", "HEAD")


class TestMergeBranches:
    """Tests for merge_branches."""

    def test_merge_branches_success(self, github_ops):
        """merge_branches returns result dict on success."""
        result = github_ops.merge_branches("/repo", "feature/x", "main", "Merge feature")
        assert result["source_branch"] == "feature/x"
        assert result["target_branch"] == "main"
        assert "merge_commit" in result

    def test_merge_conflict_raises(self, github_ops):
        """Merge conflict raises GitOperationError."""
        # First call (checkout) succeeds, second call (merge) fails
        github_ops._mock_sub.run.side_effect = [
            MagicMock(stdout="", stderr="", returncode=0),  # checkout
            MagicMock(stdout="", stderr="CONFLICT (content): Merge conflict", returncode=1),
        ]
        with pytest.raises(GitOperationError, match="Failed to merge"):
            github_ops.merge_branches("/repo", "feature/x", "main", "Merge")


class TestPushChanges:
    """Tests for push_changes."""

    def test_push_changes_success(self, github_ops):
        """push_changes calls git push."""
        github_ops.push_changes("/repo", "main")
        call_args = github_ops._mock_sub.run.call_args[0][0]
        assert "push" in call_args
        assert "main" in call_args

    def test_push_with_force(self, github_ops):
        """push_changes with force=True passes --force flag."""
        github_ops.push_changes("/repo", "main", force=True)
        call_args = github_ops._mock_sub.run.call_args[0][0]
        assert "--force" in call_args

    def test_push_failure_raises(self, github_ops):
        """push_changes raises GitOperationError on failure."""
        github_ops._mock_sub.run.return_value = MagicMock(
            stdout="", stderr="error: failed to push", returncode=1
        )
        with pytest.raises(GitOperationError, match="Failed to push"):
            github_ops.push_changes("/repo", "main")


class TestCreatePullRequest:
    """Tests for create_pull_request."""

    def test_create_pull_request_github(self, github_ops):
        """create_pull_request calls GitHub pulls API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"number": 42, "title": "Test PR"}
        mock_response.raise_for_status = MagicMock()
        github_ops._mock_req.request.return_value = mock_response

        result = github_ops.create_pull_request(
            title="Test PR",
            source_branch="feature/x",
            target_branch="main",
            body="Description",
        )
        assert mock_response.json.return_value == result
        call_kwargs = github_ops._mock_req.request.call_args
        assert "pulls" in str(call_kwargs)

    def test_create_pull_request_gitlab(self, gitlab_ops):
        """create_pull_request (GitLab MR) calls merge_requests API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"iid": 10, "title": "Test MR"}
        mock_response.raise_for_status = MagicMock()
        gitlab_ops._mock_req.request.return_value = mock_response

        result = gitlab_ops.create_pull_request(
            title="Test MR",
            source_branch="feature/x",
            target_branch="main",
        )
        assert mock_response.json.return_value == result
        call_kwargs = gitlab_ops._mock_req.request.call_args
        assert "merge_requests" in str(call_kwargs)
