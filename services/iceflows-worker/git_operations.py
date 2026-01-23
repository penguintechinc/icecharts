"""
Git Operations Module for IceFlows CI/CD Pipeline

Supports both GitHub and GitLab for repository operations including cloning,
branching, merging, and pull request/merge request management.

Copyright (c) 2026 Penguin Tech Inc.
License: Limited AGPL3
"""

import logging
import os
import re
import subprocess
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

import requests


logger = logging.getLogger(__name__)


class GitOperationError(Exception):
    """Custom exception for git operation failures"""
    pass


class GitOperations:
    """
    Git operations manager supporting GitHub and GitLab.

    Provides unified interface for repository operations and API interactions
    across GitHub and GitLab platforms.
    """

    # API base URLs
    GITHUB_API_BASE = "https://api.github.com"
    GITLAB_API_BASE = "https://gitlab.com/api/v4"

    # API timeout (seconds)
    API_TIMEOUT = 30

    # Valid branch name pattern (prevent injection)
    BRANCH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9._/-]+$')

    def __init__(self, provider: str, api_token: str, repo_url: str):
        """
        Initialize GitOperations.

        Args:
            provider: Git provider ("github" or "gitlab")
            api_token: Personal access token for API authentication
            repo_url: Repository URL (https://github.com/org/repo or
                     https://gitlab.com/org/repo)

        Raises:
            GitOperationError: If provider is invalid or URL cannot be parsed
        """
        if provider.lower() not in ("github", "gitlab"):
            raise GitOperationError(
                f"Invalid provider: {provider}. Must be 'github' or 'gitlab'"
            )

        self.provider = provider.lower()
        self.api_token = api_token
        self.repo_url = repo_url

        # Parse repository owner and name from URL
        self.repo_owner, self.repo_name = self._parse_repo_url(repo_url)

        # Set API base URL
        if self.provider == "github":
            self.api_base = self.GITHUB_API_BASE
        else:
            # Support custom GitLab instances
            parsed = urlparse(repo_url)
            if parsed.hostname and parsed.hostname != "gitlab.com":
                self.api_base = f"{parsed.scheme}://{parsed.hostname}/api/v4"
            else:
                self.api_base = self.GITLAB_API_BASE

        logger.info(
            f"Initialized GitOperations for {self.provider}: "
            f"{self.repo_owner}/{self.repo_name}"
        )

    def _parse_repo_url(self, url: str) -> Tuple[str, str]:
        """
        Parse repository owner and name from URL.

        Args:
            url: Repository URL

        Returns:
            Tuple of (owner, repo_name)

        Raises:
            GitOperationError: If URL format is invalid
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')

            # Remove .git suffix if present
            if path.endswith('.git'):
                path = path[:-4]

            parts = path.split('/')
            if len(parts) < 2:
                raise ValueError("URL must contain owner and repository name")

            # For GitHub: owner/repo
            # For GitLab: can be owner/repo or group/subgroup/repo
            if self.provider == "github":
                owner = parts[0]
                repo = parts[1]
            else:
                # GitLab: take last part as repo, everything else as owner
                owner = '/'.join(parts[:-1])
                repo = parts[-1]

            return owner, repo

        except Exception as e:
            raise GitOperationError(
                f"Failed to parse repository URL '{url}': {str(e)}"
            )

    def _validate_branch_name(self, branch: str) -> None:
        """
        Validate branch name to prevent command injection.

        Args:
            branch: Branch name to validate

        Raises:
            GitOperationError: If branch name is invalid
        """
        if not branch or not self.BRANCH_NAME_PATTERN.match(branch):
            raise GitOperationError(
                f"Invalid branch name: '{branch}'. "
                "Branch names must contain only alphanumeric characters, "
                "dots, underscores, hyphens, and forward slashes."
            )

    def _get_auth_url(self) -> str:
        """
        Get repository URL with embedded authentication token.

        Returns:
            URL with token for authenticated clone operations
        """
        parsed = urlparse(self.repo_url)

        # Embed token in URL based on provider
        if self.provider == "github":
            # GitHub: https://TOKEN@github.com/owner/repo.git
            netloc = f"{self.api_token}@{parsed.hostname}"
        else:
            # GitLab: https://oauth2:TOKEN@gitlab.com/owner/repo.git
            netloc = f"oauth2:{self.api_token}@{parsed.hostname}"

        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"

        auth_url = urlunparse((
            parsed.scheme,
            netloc,
            parsed.path if parsed.path.endswith('.git') else f"{parsed.path}.git",
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

        return auth_url

    def _run_git_command(
        self,
        repo_path: str,
        *args
    ) -> Tuple[str, str, int]:
        """
        Execute git command safely using subprocess.

        Args:
            repo_path: Path to git repository
            *args: Git command arguments

        Returns:
            Tuple of (stdout, stderr, returncode)

        Raises:
            GitOperationError: If command execution fails
        """
        cmd = ['git', '-C', repo_path] + list(args)

        # Log command (but not if it contains tokens)
        log_cmd = cmd.copy()
        if any('http' in str(arg) for arg in cmd):
            log_cmd = [arg if 'http' not in str(arg) else '[REDACTED_URL]'
                      for arg in cmd]
        logger.debug(f"Executing git command: {' '.join(log_cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for git operations
                check=False
            )

            if result.returncode != 0:
                logger.error(
                    f"Git command failed with code {result.returncode}: "
                    f"{result.stderr}"
                )

            return result.stdout, result.stderr, result.returncode

        except subprocess.TimeoutExpired:
            raise GitOperationError(
                f"Git command timed out after 300 seconds: {' '.join(log_cmd)}"
            )
        except Exception as e:
            raise GitOperationError(
                f"Failed to execute git command: {str(e)}"
            )

    def _github_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make authenticated request to GitHub API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/repos/owner/repo/pulls")
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            GitOperationError: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers.update({
            'Authorization': f'token {self.api_token}',
            'Accept': 'application/vnd.github.v3+json'
        })

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.API_TIMEOUT,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            raise GitOperationError(
                f"GitHub API request timed out after {self.API_TIMEOUT} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise GitOperationError(
                f"GitHub API request failed: {str(e)}"
            )

    def _gitlab_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make authenticated request to GitLab API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/projects/:id/merge_requests")
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            GitOperationError: If request fails
        """
        url = f"{self.api_base}{endpoint}"
        headers = kwargs.pop('headers', {})
        headers.update({
            'PRIVATE-TOKEN': self.api_token
        })

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                timeout=self.API_TIMEOUT,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            raise GitOperationError(
                f"GitLab API request timed out after {self.API_TIMEOUT} seconds"
            )
        except requests.exceptions.RequestException as e:
            raise GitOperationError(
                f"GitLab API request failed: {str(e)}"
            )

    def clone_repo(
        self,
        target_path: str,
        branch: Optional[str] = None
    ) -> str:
        """
        Clone repository with authentication.

        Args:
            target_path: Local path to clone repository
            branch: Optional branch to checkout after clone

        Returns:
            Path to cloned repository

        Raises:
            GitOperationError: If clone fails
        """
        if branch:
            self._validate_branch_name(branch)

        # Ensure target directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Clone with authentication
        auth_url = self._get_auth_url()

        args = ['clone', auth_url, target_path]
        if branch:
            args.extend(['--branch', branch])

        stdout, stderr, returncode = self._run_git_command('.', *args)

        if returncode != 0:
            raise GitOperationError(
                f"Failed to clone repository: {stderr}"
            )

        logger.info(f"Successfully cloned repository to {target_path}")
        return target_path

    def checkout_branch(self, repo_path: str, branch: str) -> None:
        """
        Checkout specified branch.

        Args:
            repo_path: Path to git repository
            branch: Branch name to checkout

        Raises:
            GitOperationError: If checkout fails
        """
        self._validate_branch_name(branch)

        stdout, stderr, returncode = self._run_git_command(
            repo_path, 'checkout', branch
        )

        if returncode != 0:
            raise GitOperationError(
                f"Failed to checkout branch '{branch}': {stderr}"
            )

        logger.info(f"Checked out branch: {branch}")

    def get_commit_sha(
        self,
        repo_path: str,
        branch: str = "HEAD"
    ) -> str:
        """
        Get commit SHA for specified branch or HEAD.

        Args:
            repo_path: Path to git repository
            branch: Branch name or "HEAD" for current commit

        Returns:
            Commit SHA string

        Raises:
            GitOperationError: If operation fails
        """
        if branch != "HEAD":
            self._validate_branch_name(branch)

        stdout, stderr, returncode = self._run_git_command(
            repo_path, 'rev-parse', branch
        )

        if returncode != 0:
            raise GitOperationError(
                f"Failed to get commit SHA for '{branch}': {stderr}"
            )

        sha = stdout.strip()
        logger.debug(f"Commit SHA for {branch}: {sha}")
        return sha

    def merge_branches(
        self,
        repo_path: str,
        source_branch: str,
        target_branch: str,
        commit_message: str
    ) -> dict:
        """
        Perform local merge of source branch into target branch.

        Args:
            repo_path: Path to git repository
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            commit_message: Commit message for merge

        Returns:
            Dictionary with merge result information

        Raises:
            GitOperationError: If merge fails
        """
        self._validate_branch_name(source_branch)
        self._validate_branch_name(target_branch)

        # Checkout target branch
        self.checkout_branch(repo_path, target_branch)

        # Perform merge
        stdout, stderr, returncode = self._run_git_command(
            repo_path, 'merge', source_branch, '-m', commit_message
        )

        if returncode != 0:
            raise GitOperationError(
                f"Failed to merge '{source_branch}' into '{target_branch}': "
                f"{stderr}"
            )

        # Get merge commit SHA
        merge_sha = self.get_commit_sha(repo_path, "HEAD")

        result = {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'merge_commit': merge_sha,
            'message': commit_message
        }

        logger.info(
            f"Successfully merged {source_branch} into {target_branch}: "
            f"{merge_sha}"
        )
        return result

    def push_changes(
        self,
        repo_path: str,
        branch: str,
        force: bool = False
    ) -> None:
        """
        Push changes to remote repository.

        Args:
            repo_path: Path to git repository
            branch: Branch name to push
            force: Whether to force push

        Raises:
            GitOperationError: If push fails
        """
        self._validate_branch_name(branch)

        args = ['push', 'origin', branch]
        if force:
            args.append('--force')

        stdout, stderr, returncode = self._run_git_command(repo_path, *args)

        if returncode != 0:
            raise GitOperationError(
                f"Failed to push branch '{branch}': {stderr}"
            )

        logger.info(f"Successfully pushed branch: {branch}")

    def get_branch_info(self, branch: str) -> dict:
        """
        Get branch details via API.

        Args:
            branch: Branch name

        Returns:
            Dictionary with branch information

        Raises:
            GitOperationError: If API request fails
        """
        self._validate_branch_name(branch)

        if self.provider == "github":
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/branches/{branch}"
            response = self._github_request('GET', endpoint)
        else:
            # GitLab uses project ID (URL encoded namespace/repo)
            project_id = f"{self.repo_owner}%2F{self.repo_name}"
            endpoint = f"/projects/{project_id}/repository/branches/{branch}"
            response = self._gitlab_request('GET', endpoint)

        return response.json()

    def get_commit_info(self, sha: str) -> dict:
        """
        Get commit details via API.

        Args:
            sha: Commit SHA

        Returns:
            Dictionary with commit information

        Raises:
            GitOperationError: If API request fails
        """
        if self.provider == "github":
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/commits/{sha}"
            response = self._github_request('GET', endpoint)
        else:
            project_id = f"{self.repo_owner}%2F{self.repo_name}"
            endpoint = f"/projects/{project_id}/repository/commits/{sha}"
            response = self._gitlab_request('GET', endpoint)

        return response.json()

    def create_pull_request(
        self,
        title: str,
        source_branch: str,
        target_branch: str,
        body: str = ""
    ) -> dict:
        """
        Create pull request (GitHub) or merge request (GitLab).

        Args:
            title: PR/MR title
            source_branch: Source branch name
            target_branch: Target branch name
            body: PR/MR description

        Returns:
            Dictionary with PR/MR information

        Raises:
            GitOperationError: If creation fails
        """
        self._validate_branch_name(source_branch)
        self._validate_branch_name(target_branch)

        if self.provider == "github":
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/pulls"
            data = {
                'title': title,
                'head': source_branch,
                'base': target_branch,
                'body': body
            }
            response = self._github_request('POST', endpoint, json=data)
        else:
            project_id = f"{self.repo_owner}%2F{self.repo_name}"
            endpoint = f"/projects/{project_id}/merge_requests"
            data = {
                'title': title,
                'source_branch': source_branch,
                'target_branch': target_branch,
                'description': body
            }
            response = self._gitlab_request('POST', endpoint, json=data)

        result = response.json()
        pr_number = result.get('number') or result.get('iid')
        logger.info(
            f"Created {'pull request' if self.provider == 'github' else 'merge request'} "
            f"#{pr_number}: {title}"
        )
        return result

    def get_pull_request(self, pr_number: int) -> dict:
        """
        Get pull request or merge request details.

        Args:
            pr_number: PR/MR number

        Returns:
            Dictionary with PR/MR information

        Raises:
            GitOperationError: If API request fails
        """
        if self.provider == "github":
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}"
            response = self._github_request('GET', endpoint)
        else:
            project_id = f"{self.repo_owner}%2F{self.repo_name}"
            endpoint = f"/projects/{project_id}/merge_requests/{pr_number}"
            response = self._gitlab_request('GET', endpoint)

        return response.json()

    def merge_pull_request(
        self,
        pr_number: int,
        merge_method: str = "merge"
    ) -> dict:
        """
        Merge pull request or merge request via API.

        Args:
            pr_number: PR/MR number
            merge_method: Merge method ("merge", "squash", "rebase")

        Returns:
            Dictionary with merge result

        Raises:
            GitOperationError: If merge fails
        """
        valid_methods = {"merge", "squash", "rebase"}
        if merge_method not in valid_methods:
            raise GitOperationError(
                f"Invalid merge method: {merge_method}. "
                f"Must be one of: {valid_methods}"
            )

        if self.provider == "github":
            endpoint = f"/repos/{self.repo_owner}/{self.repo_name}/pulls/{pr_number}/merge"
            data = {'merge_method': merge_method}
            response = self._github_request('PUT', endpoint, json=data)
        else:
            project_id = f"{self.repo_owner}%2F{self.repo_name}"
            endpoint = f"/projects/{project_id}/merge_requests/{pr_number}/merge"
            # GitLab uses different parameter names
            gitlab_method_map = {
                'merge': 'merge',
                'squash': 'merge',  # Squash is a parameter, not method
                'rebase': 'rebase_merge'
            }
            data = {}
            if merge_method == 'squash':
                data['squash'] = True
            else:
                data['merge_when_pipeline_succeeds'] = False

            response = self._gitlab_request('PUT', endpoint, json=data)

        result = response.json()
        logger.info(
            f"Merged {'pull request' if self.provider == 'github' else 'merge request'} "
            f"#{pr_number} using method: {merge_method}"
        )
        return result
