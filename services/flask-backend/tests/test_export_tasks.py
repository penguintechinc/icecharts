"""Tests for Celery export tasks.

Tests the background export functionality using Celery tasks with Redis storage.
Since we can't connect to a real broker, tasks are executed via .run() method.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from app.tasks.export_tasks import (export_drawing_task, get_export_metadata,
                                    get_export_result, get_export_status)

_REDIS_PATCH = "redis.Redis"
_EXPORT_PATCH = "app.tasks.export_tasks.ExportService.export"


def _mock_redis():
    """Return (redis_cls_mock, redis_instance_mock) with from_url configured."""
    instance = MagicMock()
    instance.setex.return_value = True
    instance.get.return_value = None
    cls = MagicMock()
    cls.from_url.return_value = instance
    return cls, instance


class TestExportDrawingTask:
    """Test export_drawing_task Celery task."""

    def test_export_png_task_success(self):
        """Test successful PNG export via task."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"PNG_IMAGE_DATA"

            result = export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={"width": 800, "height": 600, "quality": 95},
                drawing_data={"elements": [], "width": 800, "height": 600},
            )

            assert result is not None
            assert result["status"] == "completed"
            assert result["drawing_id"] == 1
            assert result["format"] == "png"
            assert "redis_key" in result
            assert result["size"] == len(b"PNG_IMAGE_DATA")
            assert "task_id" in result

    def test_export_svg_task_success(self):
        """Test successful SVG export via task."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            svg_content = "<svg></svg>"
            mock_export.return_value = svg_content

            result = export_drawing_task.run(
                drawing_id=2,
                format="svg",
                options={"format": "svg"},
                drawing_data={"elements": [], "width": 800, "height": 600},
            )

            assert result["status"] == "completed"
            assert result["format"] == "svg"
            assert result["size"] == len(svg_content)

    def test_export_json_task_success(self):
        """Test successful JSON export via task."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            json_content = '{"elements": [], "width": 800}'
            mock_export.return_value = json_content

            result = export_drawing_task.run(
                drawing_id=3,
                format="json",
                options={"format": "json"},
                drawing_data={"elements": [], "width": 800},
            )

            assert result["status"] == "completed"
            assert result["format"] == "json"
            assert result["size"] == len(json_content)

    def test_export_task_missing_drawing_data_raises_error(self):
        """Test export task with missing drawing data."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls):
            with pytest.raises(ValueError, match="Drawing data is required"):
                export_drawing_task.run(
                    drawing_id=1,
                    format="png",
                    options={"width": 800, "height": 600},
                    drawing_data=None,
                )

    def test_export_task_invalid_format_raises_error(self):
        """Test export task with invalid format."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.side_effect = ValueError("Invalid format. Must be one of:")

            with pytest.raises(ValueError):
                export_drawing_task.run(
                    drawing_id=1,
                    format="invalid_format",
                    options={},
                    drawing_data={"elements": []},
                )

    def test_export_task_stores_result_with_correct_key(self):
        """Test that export task stores result in Redis with correct key."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"TEST_DATA"

            result = export_drawing_task.run(
                drawing_id=123,
                format="png",
                options={},
                drawing_data={"elements": []},
            )

            redis_key = result["redis_key"]
            assert redis_key.startswith("export:result:")
            assert redis_inst.setex.called

    def test_export_task_sets_expiry_on_result(self):
        """Test that export task sets Redis expiry on stored result."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"DATA"

            export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={},
                drawing_data={"elements": []},
            )

            calls = redis_inst.setex.call_args_list
            assert len(calls) > 0
            # Every setex call should have 86400 (24h) as the second positional arg
            for c in calls:
                assert c[0][1] == 86400

    def test_export_task_default_options(self):
        """Test export task with default options."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"PNG_DATA"

            result = export_drawing_task.run(
                drawing_id=1,
                format="png",
                options=None,
                drawing_data={"elements": []},
            )

            assert result["status"] == "completed"
            assert mock_export.called
            export_options = mock_export.call_args[0][0]
            assert export_options.width == 800
            assert export_options.height == 600
            assert export_options.quality == 95

    def test_export_task_with_custom_quality(self):
        """Test export task with custom quality setting."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"JPG_DATA"

            export_drawing_task.run(
                drawing_id=1,
                format="jpg",
                options={"quality": 50},
                drawing_data={"elements": []},
            )

            export_options = mock_export.call_args[0][0]
            assert export_options.quality == 50

    def test_export_task_with_include_background_false(self):
        """Test export task with include_background set to False."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"PNG_TRANSPARENT"

            export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={"include_background": False},
                drawing_data={"elements": []},
            )

            export_options = mock_export.call_args[0][0]
            assert export_options.include_background is False

    def test_export_task_with_custom_page_size(self):
        """Test export task PDF with custom page size."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"PDF_DATA"

            export_drawing_task.run(
                drawing_id=1,
                format="pdf",
                options={"page_size": "A3"},
                drawing_data={"elements": []},
            )

            export_options = mock_export.call_args[0][0]
            assert export_options.page_size == "A3"

    def test_export_task_stores_metadata_in_redis(self):
        """Test that export task stores metadata in Redis."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"DATA"

            result = export_drawing_task.run(
                drawing_id=999,
                format="svg",
                options={},
                drawing_data={"elements": []},
            )

            redis_key = result["redis_key"]
            calls = [c[0] for c in redis_inst.setex.call_args_list]
            metadata_calls = [c for c in calls if "metadata" in c[0]]
            assert len(metadata_calls) > 0

    def test_export_task_updates_status_during_export(self):
        """Test that export task updates status in Redis during execution."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"DATA"

            export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={},
                drawing_data={"elements": []},
            )

            calls = [c[0] for c in redis_inst.setex.call_args_list]
            status_calls = [
                c for c in calls if "export:task:" in c[0] and "error" not in c[0]
            ]
            assert len(status_calls) > 0

    def test_export_task_failure_stores_error_in_redis(self):
        """Test that export task stores error in Redis on failure."""
        redis_cls, redis_inst = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.side_effect = RuntimeError("Export failed")

            with pytest.raises(RuntimeError):
                export_drawing_task.run(
                    drawing_id=1,
                    format="png",
                    options={},
                    drawing_data={"elements": []},
                )

            calls = [c[0] for c in redis_inst.setex.call_args_list]
            error_calls = [c for c in calls if "failed" in str(c[1])]
            assert len(error_calls) > 0

    def test_export_task_binary_vs_text_content_handling(self):
        """Test that export task handles both binary and text content."""
        # Binary content (PNG)
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"BINARY_PNG_DATA"

            result = export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={},
                drawing_data={"elements": []},
            )

            assert result["status"] == "completed"
            assert result["size"] == len(b"BINARY_PNG_DATA")

        # Text content (JSON)
        redis_cls2, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls2), patch(_EXPORT_PATCH) as mock_export2:
            json_str = '{"test": "data"}'
            mock_export2.return_value = json_str

            result2 = export_drawing_task.run(
                drawing_id=2,
                format="json",
                options={},
                drawing_data={"elements": []},
            )

            assert result2["status"] == "completed"
            assert result2["size"] == len(json_str)

    def test_export_task_large_dimensions(self):
        """Test export task with large drawing dimensions."""
        redis_cls, _ = _mock_redis()
        with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
            mock_export.return_value = b"LARGE_DATA" * 100

            result = export_drawing_task.run(
                drawing_id=1,
                format="png",
                options={"width": 4000, "height": 3000},
                drawing_data={"elements": []},
            )

            assert result["status"] == "completed"
            export_options = mock_export.call_args[0][0]
            assert export_options.width == 4000
            assert export_options.height == 3000

    def test_export_task_multiple_formats_sequentially(self):
        """Test exporting same drawing to multiple formats."""
        formats = ["png", "svg", "json"]
        drawing_data = {"elements": []}

        for fmt in formats:
            redis_cls, _ = _mock_redis()
            with patch(_REDIS_PATCH, redis_cls), patch(_EXPORT_PATCH) as mock_export:
                mock_export.return_value = (
                    b"DATA" if fmt != "json" else '{"data": "test"}'
                )

                result = export_drawing_task.run(
                    drawing_id=1,
                    format=fmt,
                    options={},
                    drawing_data=drawing_data,
                )

                assert result["status"] == "completed"
                assert result["format"] == fmt


class TestExportHelperFunctions:
    """Tests for get_export_status, get_export_result, get_export_metadata."""

    def test_get_export_status_returns_dict_when_found(self):
        """Test get_export_status returns parsed dict when key exists in Redis."""
        redis_cls, redis_inst = _mock_redis()
        status_data = {"task_id": "t1", "status": "completed", "progress": 100}
        redis_inst.get.return_value = json.dumps(status_data).encode()

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_status("t1")

        assert result is not None
        assert result["status"] == "completed"
        assert result["progress"] == 100

    def test_get_export_status_returns_none_when_missing(self):
        """Test get_export_status returns None when key absent from Redis."""
        redis_cls, redis_inst = _mock_redis()
        redis_inst.get.return_value = None

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_status("nonexistent")

        assert result is None

    def test_get_export_result_returns_bytes_when_found(self):
        """Test get_export_result returns raw bytes from Redis."""
        redis_cls, redis_inst = _mock_redis()
        redis_inst.get.return_value = b"BINARYDATA"

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_result("t1")

        assert result == b"BINARYDATA"

    def test_get_export_result_returns_none_when_missing(self):
        """Test get_export_result returns None when key absent."""
        redis_cls, redis_inst = _mock_redis()
        redis_inst.get.return_value = None

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_result("nonexistent")

        assert result is None

    def test_get_export_metadata_returns_dict_when_found(self):
        """Test get_export_metadata returns parsed dict when key exists."""
        redis_cls, redis_inst = _mock_redis()
        meta = {"task_id": "t1", "format": "png", "drawing_id": 5}
        redis_inst.get.return_value = json.dumps(meta).encode()

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_metadata("t1")

        assert result is not None
        assert result["format"] == "png"
        assert result["drawing_id"] == 5

    def test_get_export_metadata_returns_none_when_missing(self):
        """Test get_export_metadata returns None when key absent."""
        redis_cls, redis_inst = _mock_redis()
        redis_inst.get.return_value = None

        with patch(_REDIS_PATCH, redis_cls):
            result = get_export_metadata("nonexistent")

        assert result is None
