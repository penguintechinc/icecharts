"""
Darwin Code Reviewer Integration - AI-powered code review service for IceFlows.

This module provides integration with Darwin, an AI-powered code review service,
enabling automated code review capabilities for IceFlows CI/CD pipelines.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ReviewIssue:
    """Represents a single code review issue found by Darwin."""

    issue_id: str
    type: str  # "error", "warning", "style", "security", "optimization"
    severity: str  # "critical", "high", "medium", "low"
    file_path: str
    line_number: int
    message: str
    suggestion: Optional[str] = None


@dataclass(slots=True)
class ReviewStatus:
    """Represents the current status of a code review."""

    review_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress_percent: int
    started_at: datetime


@dataclass(slots=True)
class ReviewResult:
    """Represents the complete result of a code review."""

    review_id: str
    status: str
    success: bool
    total_issues: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    issues: List[ReviewIssue]
    duration_seconds: float
    completed_at: datetime


class DarwinReviewerException(Exception):
    """Base exception for Darwin reviewer operations."""

    pass


class DarwinReviewerConnectionError(DarwinReviewerException):
    """Exception raised when unable to connect to Darwin API."""

    pass


class DarwinReviewerTimeoutError(DarwinReviewerException):
    """Exception raised when Darwin API request times out."""

    pass


class DarwinReviewer:
    """Integration with Darwin AI-powered code review service."""

    # Darwin API endpoints
    ENDPOINT_SUBMIT_REVIEW = "/api/v1/reviews"
    ENDPOINT_REVIEW_STATUS = "/api/v1/reviews/{review_id}"
    ENDPOINT_REVIEW_ISSUES = "/api/v1/reviews/{review_id}/issues"

    # Review type constants
    REVIEW_TYPE_STANDARD = "standard"
    REVIEW_TYPE_SECURITY = "security"
    REVIEW_TYPE_FULL = "full"
    REVIEW_TYPE_MINIMAL = "minimal"

    # Valid review types
    VALID_REVIEW_TYPES = {
        REVIEW_TYPE_STANDARD,
        REVIEW_TYPE_SECURITY,
        REVIEW_TYPE_FULL,
        REVIEW_TYPE_MINIMAL,
    }

    # Issue severity levels
    SEVERITY_CRITICAL = "critical"
    SEVERITY_HIGH = "high"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_LOW = "low"

    def __init__(
        self,
        api_url: str,
        api_key: str,
        timeout_seconds: int = 120,
    ):
        """
        Initialize Darwin code reviewer.

        Args:
            api_url: Darwin API base URL
            api_key: Darwin API authentication key
            timeout_seconds: Default timeout for review processing (default: 120)

        Raises:
            ValueError: If api_url or api_key are empty
        """
        if not api_url or not api_url.strip():
            raise ValueError("api_url cannot be empty")
        if not api_key or not api_key.strip():
            raise ValueError("api_key cannot be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

        logger.info(
            f"DarwinReviewer initialized: api_url={self.api_url}, "
            f"timeout={timeout_seconds}s"
        )

    def submit_review(
        self,
        diff: str,
        context: Dict[str, Any],
        review_type: str = REVIEW_TYPE_STANDARD,
    ) -> str:
        """
        Submit code diff for review.

        Submits a code diff to Darwin for analysis and returns a review ID
        for tracking the review status.

        Args:
            diff: Git diff or code diff content
            context: Additional context about the code change (branch, commit, etc.)
            review_type: Type of review to perform (default: "standard")

        Returns:
            Review ID for tracking the review

        Raises:
            ValueError: If review_type is invalid or diff is empty
            DarwinReviewerConnectionError: If unable to connect to Darwin API
            DarwinReviewerTimeoutError: If request times out
        """
        if not diff or not diff.strip():
            raise ValueError("diff cannot be empty")

        if review_type not in self.VALID_REVIEW_TYPES:
            raise ValueError(
                f"Invalid review_type: {review_type}. "
                f"Must be one of: {self.VALID_REVIEW_TYPES}"
            )

        logger.info(f"Submitting review: review_type={review_type}")
        logger.debug(f"Review context: {context}")

        payload = self._format_diff_for_review(diff, context)
        payload["review_type"] = review_type

        try:
            response = self._make_request(
                "POST",
                self.ENDPOINT_SUBMIT_REVIEW,
                json=payload,
                timeout=self.timeout_seconds,
            )

            if response.status_code not in (200, 201, 202):
                logger.error(
                    f"Submit review failed: status={response.status_code}, "
                    f"response={response.text}"
                )
                raise DarwinReviewerException(
                    f"Failed to submit review: {response.status_code}"
                )

            result = response.json()
            review_id = result.get("review_id")

            if not review_id:
                logger.error("No review_id in Darwin API response")
                raise DarwinReviewerException("No review_id returned from Darwin API")

            logger.info(f"Review submitted successfully: review_id={review_id}")
            return review_id

        except requests.exceptions.Timeout as e:
            logger.error(f"Review submission timeout: {e}")
            raise DarwinReviewerTimeoutError("Review submission timed out") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during review submission: {e}")
            raise DarwinReviewerConnectionError(
                f"Unable to connect to Darwin API: {e}"
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during review submission: {e}")
            raise DarwinReviewerException(f"Review submission failed: {e}") from e

    def get_review_status(self, review_id: str) -> ReviewStatus:
        """
        Get current status of a review.

        Polls Darwin API for the current status of an ongoing review.

        Args:
            review_id: Review ID to check

        Returns:
            ReviewStatus object with current review status

        Raises:
            ValueError: If review_id is empty
            DarwinReviewerConnectionError: If unable to connect to Darwin API
            DarwinReviewerTimeoutError: If request times out
        """
        if not review_id or not review_id.strip():
            raise ValueError("review_id cannot be empty")

        logger.debug(f"Getting review status: review_id={review_id}")

        endpoint = self.ENDPOINT_REVIEW_STATUS.format(review_id=review_id)

        try:
            response = self._make_request(
                "GET",
                endpoint,
                timeout=30,  # Shorter timeout for status check
            )

            if response.status_code == 404:
                logger.warning(f"Review not found: review_id={review_id}")
                raise DarwinReviewerException(f"Review not found: {review_id}")

            if response.status_code != 200:
                logger.error(
                    f"Get review status failed: status={response.status_code}, "
                    f"response={response.text}"
                )
                raise DarwinReviewerException(
                    f"Failed to get review status: {response.status_code}"
                )

            data = response.json()

            status = ReviewStatus(
                review_id=review_id,
                status=data.get("status", "unknown"),
                progress_percent=data.get("progress_percent", 0),
                started_at=datetime.fromisoformat(
                    data.get("started_at", datetime.now().isoformat())
                ),
            )

            logger.debug(
                f"Review status retrieved: status={status.status}, "
                f"progress={status.progress_percent}%"
            )

            return status

        except requests.exceptions.Timeout as e:
            logger.error(f"Review status check timeout: {e}")
            raise DarwinReviewerTimeoutError("Review status check timed out") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during review status check: {e}")
            raise DarwinReviewerConnectionError(
                f"Unable to connect to Darwin API: {e}"
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during review status check: {e}")
            raise DarwinReviewerException(f"Review status check failed: {e}") from e

    def get_review_issues(self, review_id: str) -> List[ReviewIssue]:
        """
        Get issues found in a review.

        Retrieves all issues (errors, warnings, etc.) identified during the review.

        Args:
            review_id: Review ID to retrieve issues for

        Returns:
            List of ReviewIssue objects

        Raises:
            ValueError: If review_id is empty
            DarwinReviewerConnectionError: If unable to connect to Darwin API
            DarwinReviewerTimeoutError: If request times out
        """
        if not review_id or not review_id.strip():
            raise ValueError("review_id cannot be empty")

        logger.debug(f"Getting review issues: review_id={review_id}")

        endpoint = self.ENDPOINT_REVIEW_ISSUES.format(review_id=review_id)

        try:
            response = self._make_request(
                "GET",
                endpoint,
                timeout=30,
            )

            if response.status_code == 404:
                logger.warning(f"Review not found: review_id={review_id}")
                return []

            if response.status_code != 200:
                logger.error(
                    f"Get review issues failed: status={response.status_code}, "
                    f"response={response.text}"
                )
                raise DarwinReviewerException(
                    f"Failed to get review issues: {response.status_code}"
                )

            data = response.json()
            issues_data = data.get("issues", [])

            issues = []
            for issue_data in issues_data:
                try:
                    issue = ReviewIssue(
                        issue_id=issue_data.get("issue_id", ""),
                        type=issue_data.get("type", "warning"),
                        severity=issue_data.get("severity", "low"),
                        file_path=issue_data.get("file_path", ""),
                        line_number=issue_data.get("line_number", 0),
                        message=issue_data.get("message", ""),
                        suggestion=issue_data.get("suggestion"),
                    )
                    issues.append(issue)
                except (KeyError, TypeError) as e:
                    logger.warning(
                        f"Failed to parse review issue: {e}, "
                        f"issue_data={issue_data}"
                    )
                    continue

            logger.info(f"Retrieved {len(issues)} issue(s) from review: review_id={review_id}")
            return issues

        except requests.exceptions.Timeout as e:
            logger.error(f"Review issues retrieval timeout: {e}")
            raise DarwinReviewerTimeoutError("Review issues retrieval timed out") from e
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error during review issues retrieval: {e}")
            raise DarwinReviewerConnectionError(
                f"Unable to connect to Darwin API: {e}"
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during review issues retrieval: {e}")
            raise DarwinReviewerException(f"Review issues retrieval failed: {e}") from e

    def wait_for_review(
        self,
        review_id: str,
        timeout: Optional[int] = None,
        poll_interval: int = 5,
    ) -> ReviewResult:
        """
        Wait for a review to complete.

        Polls Darwin API until the review is complete, then retrieves the full result.

        Args:
            review_id: Review ID to wait for
            timeout: Maximum time to wait in seconds (default: self.timeout_seconds)
            poll_interval: Polling interval in seconds (default: 5)

        Returns:
            Complete ReviewResult object

        Raises:
            ValueError: If review_id is empty
            DarwinReviewerTimeoutError: If review doesn't complete within timeout
            DarwinReviewerException: If review fails or other error occurs
        """
        if not review_id or not review_id.strip():
            raise ValueError("review_id cannot be empty")

        if timeout is None:
            timeout = self.timeout_seconds

        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")

        logger.info(
            f"Waiting for review completion: review_id={review_id}, "
            f"timeout={timeout}s, poll_interval={poll_interval}s"
        )

        start_time = time.time()
        elapsed_time = 0

        while elapsed_time < timeout:
            try:
                status = self.get_review_status(review_id)

                if status.status == "completed":
                    logger.info(
                        f"Review completed: review_id={review_id}, "
                        f"elapsed={elapsed_time}s"
                    )
                    return self._build_review_result(review_id, status)

                elif status.status == "failed":
                    logger.error(f"Review failed: review_id={review_id}")
                    raise DarwinReviewerException(
                        f"Review failed: {review_id}"
                    )

                logger.debug(
                    f"Review in progress: status={status.status}, "
                    f"progress={status.progress_percent}%, elapsed={elapsed_time}s"
                )

                time.sleep(poll_interval)
                elapsed_time = time.time() - start_time

            except DarwinReviewerConnectionError:
                # Retry on connection errors
                logger.warning(
                    f"Connection error, retrying in {poll_interval}s..."
                )
                time.sleep(poll_interval)
                elapsed_time = time.time() - start_time

        logger.error(
            f"Review wait timeout: review_id={review_id}, timeout={timeout}s"
        )
        raise DarwinReviewerTimeoutError(
            f"Review did not complete within {timeout}s"
        )

    def check_review_passes(
        self,
        review_result: ReviewResult,
        config: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """
        Check if a review result meets stage requirements.

        Validates the review against stage configuration requirements including
        issue limits, allowed issue types, and blocking criteria.

        Args:
            review_result: ReviewResult to validate
            config: Review stage configuration dict with:
                - is_required: Whether review is required
                - max_issues_allowed: Maximum non-blocking issues allowed
                - allowed_issue_types: List of issue types that don't block
                - review_type: Type of review that was performed

        Returns:
            Tuple of (passes: bool, reason: str)
            - True if review passes requirements
            - False with reason if review fails
        """
        logger.info(
            f"Checking review against stage requirements: "
            f"review_id={review_result.review_id}, "
            f"total_issues={review_result.total_issues}"
        )

        is_required = config.get("is_required", True)
        max_issues_allowed = config.get("max_issues_allowed", 5)
        allowed_issue_types = set(config.get("allowed_issue_types", []))

        # If review is not required and completed, it passes
        if not is_required and review_result.success:
            logger.info("Review not required and status is success")
            return True, "Review completed successfully"

        # Check if review itself failed
        if not review_result.success:
            reason = f"Review failed: {review_result.status}"
            logger.warning(reason)
            return False, reason

        # Count blocking issues (critical and high severity)
        blocking_count = review_result.critical_count + review_result.high_count

        if blocking_count > 0:
            reason = (
                f"Review has {blocking_count} blocking issue(s): "
                f"{review_result.critical_count} critical, "
                f"{review_result.high_count} high"
            )
            logger.warning(reason)
            return False, reason

        # Count non-blocking issues
        non_blocking_count = 0
        for issue in review_result.issues:
            # Skip blocking issues
            if issue.severity in (self.SEVERITY_CRITICAL, self.SEVERITY_HIGH):
                continue

            # Check if issue type is allowed
            if allowed_issue_types and issue.type not in allowed_issue_types:
                reason = (
                    f"Issue type '{issue.type}' is not allowed. "
                    f"Allowed types: {allowed_issue_types}"
                )
                logger.warning(f"{reason} (issue_id={issue.issue_id})")
                return False, reason

            non_blocking_count += 1

        # Check total non-blocking issues
        if non_blocking_count > max_issues_allowed:
            reason = (
                f"Too many non-blocking issues: {non_blocking_count} > "
                f"{max_issues_allowed}"
            )
            logger.warning(reason)
            return False, reason

        reason = "Review meets all stage requirements"
        logger.info(
            f"{reason}: "
            f"blocking={blocking_count}, "
            f"non_blocking={non_blocking_count}/{max_issues_allowed}"
        )

        return True, reason

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Make HTTP request to Darwin API.

        Helper method that constructs and executes HTTP requests to Darwin API
        with proper authentication and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (relative path)
            **kwargs: Additional arguments to pass to requests

        Returns:
            requests.Response object

        Raises:
            ValueError: If method or endpoint are invalid
        """
        if not method or not method.strip():
            raise ValueError("method cannot be empty")
        if not endpoint or not endpoint.strip():
            raise ValueError("endpoint cannot be empty")

        method = method.upper()
        url = f"{self.api_url}{endpoint}"

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"
        headers["Content-Type"] = "application/json"

        logger.debug(f"Making {method} request to {url}")

        return requests.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

    def _format_diff_for_review(
        self,
        diff: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format diff and context for Darwin API submission.

        Prepares the code diff and contextual information into the format
        expected by Darwin's review submission endpoint.

        Args:
            diff: Git diff or code diff content
            context: Additional context (branch, commit SHA, file paths, etc.)

        Returns:
            Dictionary formatted for Darwin API
        """
        logger.debug("Formatting diff for Darwin API")

        payload = {
            "diff": diff,
            "context": {
                "branch": context.get("branch", "unknown"),
                "commit_sha": context.get("commit_sha", ""),
                "commit_message": context.get("commit_message", ""),
                "author": context.get("author", ""),
                "changed_files": context.get("changed_files", []),
                "additions": context.get("additions", 0),
                "deletions": context.get("deletions", 0),
            },
        }

        return payload

    def _build_review_result(
        self,
        review_id: str,
        status: ReviewStatus,
    ) -> ReviewResult:
        """
        Build complete ReviewResult from status and issues.

        Constructs a ReviewResult object by combining status information
        with retrieved issues and calculating summary statistics.

        Args:
            review_id: Review ID
            status: ReviewStatus object

        Returns:
            Complete ReviewResult object

        Raises:
            DarwinReviewerException: If unable to retrieve issues
        """
        logger.debug(f"Building review result: review_id={review_id}")

        try:
            issues = self.get_review_issues(review_id)
        except DarwinReviewerException as e:
            logger.warning(f"Failed to retrieve issues, using empty list: {e}")
            issues = []

        # Count issues by severity
        critical_count = sum(1 for i in issues if i.severity == self.SEVERITY_CRITICAL)
        high_count = sum(1 for i in issues if i.severity == self.SEVERITY_HIGH)
        medium_count = sum(1 for i in issues if i.severity == self.SEVERITY_MEDIUM)
        low_count = sum(1 for i in issues if i.severity == self.SEVERITY_LOW)

        # Determine if review is successful (no blocking issues)
        success = critical_count == 0 and high_count == 0

        # Calculate duration
        completed_at = datetime.now()
        duration_seconds = (
            completed_at - status.started_at
        ).total_seconds()

        result = ReviewResult(
            review_id=review_id,
            status=status.status,
            success=success,
            total_issues=len(issues),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            issues=issues,
            duration_seconds=duration_seconds,
            completed_at=completed_at,
        )

        logger.info(
            f"Review result built: review_id={review_id}, "
            f"success={success}, total_issues={len(issues)}, "
            f"critical={critical_count}, high={high_count}, "
            f"duration={duration_seconds}s"
        )

        return result
