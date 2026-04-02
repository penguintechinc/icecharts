"""Tests for DarwinReviewer - AI-powered code review integration."""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests as req_module
from darwin_reviewer import (DarwinReviewer, DarwinReviewerConnectionError,
                             DarwinReviewerException,
                             DarwinReviewerTimeoutError, ReviewIssue,
                             ReviewResult, ReviewStatus)


@pytest.fixture
def reviewer():
    """Create DarwinReviewer instance."""
    return DarwinReviewer(api_url="http://darwin:8080", api_key="test-key-123")


@pytest.fixture
def mock_response():
    """Create mock HTTP response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"review_id": "rev-abc"}
    resp.text = ""
    return resp


class TestDarwinReviewerInit:
    """Tests for DarwinReviewer initialization validation."""

    def test_valid_init(self):
        """Valid api_url and api_key create instance."""
        reviewer = DarwinReviewer(api_url="http://darwin:8080", api_key="key-123")
        assert reviewer.api_url == "http://darwin:8080"
        assert reviewer.api_key == "key-123"

    def test_empty_api_url_raises(self):
        """Empty api_url raises ValueError."""
        with pytest.raises(ValueError, match="api_url cannot be empty"):
            DarwinReviewer(api_url="", api_key="key")

    def test_whitespace_api_url_raises(self):
        """Whitespace-only api_url raises ValueError."""
        with pytest.raises(ValueError, match="api_url cannot be empty"):
            DarwinReviewer(api_url="   ", api_key="key")

    def test_empty_api_key_raises(self):
        """Empty api_key raises ValueError."""
        with pytest.raises(ValueError, match="api_key cannot be empty"):
            DarwinReviewer(api_url="http://darwin:8080", api_key="")

    def test_timeout_must_be_positive(self):
        """Non-positive timeout raises ValueError."""
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            DarwinReviewer(
                api_url="http://darwin:8080", api_key="key", timeout_seconds=0
            )
        with pytest.raises(ValueError, match="timeout_seconds must be positive"):
            DarwinReviewer(
                api_url="http://darwin:8080", api_key="key", timeout_seconds=-5
            )

    def test_trailing_slash_stripped(self):
        """Trailing slash stripped from api_url."""
        reviewer = DarwinReviewer(api_url="http://darwin:8080/", api_key="key")
        assert reviewer.api_url == "http://darwin:8080"


class TestSubmitReview:
    """Tests for submit_review."""

    def test_submit_review_posts_diff(self, reviewer, mock_response):
        """submit_review POSTs diff to /api/v1/reviews."""
        with patch("requests.request", return_value=mock_response) as mock_req:
            review_id = reviewer.submit_review("diff content", {})
        mock_req.assert_called_once()
        assert review_id == "rev-abc"
        call_url = mock_req.call_args[0][1]
        assert "/api/v1/reviews" in call_url

    def test_submit_review_empty_diff_raises(self, reviewer):
        """Empty diff raises ValueError."""
        with pytest.raises(ValueError, match="diff cannot be empty"):
            reviewer.submit_review("", {})

    def test_submit_review_invalid_type_raises(self, reviewer):
        """Invalid review_type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid review_type"):
            reviewer.submit_review("diff", {}, review_type="invalid")

    def test_submit_review_returns_review_id(self, reviewer, mock_response):
        """submit_review returns the review_id string."""
        mock_response.json.return_value = {"review_id": "test-review-123"}
        with patch("requests.request", return_value=mock_response):
            review_id = reviewer.submit_review("some diff", {})
        assert review_id == "test-review-123"

    def test_submit_review_timeout_raises(self, reviewer):
        """Timeout raises DarwinReviewerTimeoutError."""
        with patch(
            "requests.request", side_effect=req_module.exceptions.Timeout("timed out")
        ):
            with pytest.raises(DarwinReviewerTimeoutError):
                reviewer.submit_review("diff", {})

    def test_submit_review_connection_error_raises(self, reviewer):
        """ConnectionError raises DarwinReviewerConnectionError."""
        with patch(
            "requests.request",
            side_effect=req_module.exceptions.ConnectionError("conn refused"),
        ):
            with pytest.raises(DarwinReviewerConnectionError):
                reviewer.submit_review("diff", {})


class TestGetReviewStatus:
    """Tests for get_review_status."""

    def test_get_review_status_returns_status_object(self, reviewer, mock_response):
        """get_review_status returns ReviewStatus object."""
        mock_response.json.return_value = {
            "status": "processing",
            "progress_percent": 50,
            "started_at": datetime.now().isoformat(),
        }
        with patch("requests.request", return_value=mock_response):
            status = reviewer.get_review_status("rev-123")
        assert isinstance(status, ReviewStatus)
        assert status.status == "processing"
        assert status.progress_percent == 50

    def test_get_review_status_empty_id_raises(self, reviewer):
        """Empty review_id raises ValueError."""
        with pytest.raises(ValueError, match="review_id cannot be empty"):
            reviewer.get_review_status("")


class TestGetReviewIssues:
    """Tests for get_review_issues."""

    def test_get_review_issues_returns_list(self, reviewer, mock_response):
        """get_review_issues returns list of ReviewIssue objects."""
        mock_response.json.return_value = {
            "issues": [
                {
                    "issue_id": "i1",
                    "type": "error",
                    "severity": "critical",
                    "file_path": "main.py",
                    "line_number": 42,
                    "message": "Undefined variable",
                    "suggestion": "Define it",
                }
            ]
        }
        with patch("requests.request", return_value=mock_response):
            issues = reviewer.get_review_issues("rev-123")
        assert len(issues) == 1
        assert isinstance(issues[0], ReviewIssue)
        assert issues[0].severity == "critical"

    def test_get_review_issues_404_returns_empty(self, reviewer, mock_response):
        """404 response returns empty list."""
        mock_response.status_code = 404
        with patch("requests.request", return_value=mock_response):
            issues = reviewer.get_review_issues("rev-not-found")
        assert issues == []


class TestWaitForReview:
    """Tests for wait_for_review polling."""

    def test_wait_for_review_polls_until_completed(self, reviewer, mock_response):
        """wait_for_review polls and returns ReviewResult when completed."""
        status_resp = MagicMock()
        status_resp.status_code = 200
        status_resp.json.return_value = {
            "status": "completed",
            "progress_percent": 100,
            "started_at": datetime.now().isoformat(),
        }
        issues_resp = MagicMock()
        issues_resp.status_code = 200
        issues_resp.json.return_value = {"issues": []}

        def side_effect(method, url, **kwargs):
            if "issues" in url:
                return issues_resp
            return status_resp

        with patch("requests.request", side_effect=side_effect):
            with patch("time.sleep"):
                result = reviewer.wait_for_review(
                    "rev-123", timeout=60, poll_interval=1
                )
        assert isinstance(result, ReviewResult)
        assert result.status == "completed"

    def test_wait_for_review_timeout_raises(self, reviewer, mock_response):
        """wait_for_review raises DarwinReviewerTimeoutError on timeout."""
        mock_response.json.return_value = {
            "status": "processing",
            "progress_percent": 10,
            "started_at": datetime.now().isoformat(),
        }
        with patch("requests.request", return_value=mock_response):
            with patch("time.sleep"):
                with patch("time.time", side_effect=[0, 200, 200]):
                    with pytest.raises(DarwinReviewerTimeoutError):
                        reviewer.wait_for_review("rev-123", timeout=5, poll_interval=1)


class TestCheckReviewPasses:
    """Tests for check_review_passes."""

    def _make_result(self, issues=None, success=True):
        """Helper to create ReviewResult."""
        issues = issues or []
        critical = sum(1 for i in issues if i.severity == "critical")
        high = sum(1 for i in issues if i.severity == "high")
        medium = sum(1 for i in issues if i.severity == "medium")
        low = sum(1 for i in issues if i.severity == "low")
        return ReviewResult(
            review_id="rev-1",
            status="completed",
            success=success,
            total_issues=len(issues),
            critical_count=critical,
            high_count=high,
            medium_count=medium,
            low_count=low,
            issues=issues,
            duration_seconds=1.0,
            completed_at=datetime.now(),
        )

    def test_passes_with_no_critical_issues(self, reviewer):
        """Review with no critical/high issues passes."""
        result = self._make_result()
        passes, reason = reviewer.check_review_passes(result, {"is_required": True})
        assert passes is True

    def test_fails_with_critical_issue(self, reviewer):
        """Review with critical issue fails."""
        issue = ReviewIssue(
            issue_id="i1",
            type="error",
            severity="critical",
            file_path="main.py",
            line_number=1,
            message="critical bug",
        )
        result = self._make_result(issues=[issue])
        passes, reason = reviewer.check_review_passes(result, {"is_required": True})
        assert passes is False
        assert "critical" in reason.lower()

    def test_fails_when_review_failed(self, reviewer):
        """Review that failed is not passing."""
        result = self._make_result(success=False)
        passes, reason = reviewer.check_review_passes(result, {"is_required": True})
        assert passes is False


class TestFormatDiffForReview:
    """Tests for _format_diff_for_review."""

    def test_format_diff_includes_diff_field(self, reviewer):
        """Formatted payload includes diff field."""
        payload = reviewer._format_diff_for_review("diff content", {"branch": "main"})
        assert payload["diff"] == "diff content"

    def test_format_diff_includes_context(self, reviewer):
        """Formatted payload includes context with branch."""
        payload = reviewer._format_diff_for_review(
            "diff", {"branch": "feature/x", "commit_sha": "abc123"}
        )
        assert payload["context"]["branch"] == "feature/x"
        assert payload["context"]["commit_sha"] == "abc123"


class TestBuildReviewResult:
    """Tests for _build_review_result severity counting."""

    def test_build_review_result_counts_severities(self, reviewer):
        """_build_review_result correctly counts issues by severity."""
        issues_data = [
            ReviewIssue("i1", "error", "critical", "a.py", 1, "crit msg"),
            ReviewIssue("i2", "warning", "high", "b.py", 2, "high msg"),
            ReviewIssue("i3", "style", "medium", "c.py", 3, "med msg"),
            ReviewIssue("i4", "style", "low", "d.py", 4, "low msg"),
        ]
        # Mock get_review_issues to return our issues
        with patch.object(reviewer, "get_review_issues", return_value=issues_data):
            status = ReviewStatus(
                review_id="rev-1",
                status="completed",
                progress_percent=100,
                started_at=datetime.now(),
            )
            result = reviewer._build_review_result("rev-1", status)

        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 1
        assert result.total_issues == 4
        assert result.success is False  # Has critical and high issues
