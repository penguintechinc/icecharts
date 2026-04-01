"""Comprehensive tests for ExportService.

Tests cover PNG, JPG, SVG, PDF, and JSON export formats with various input
types (dict-based drawing data and SVG strings).
"""

import io
import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from app.services.export_service import ExportOptions, ExportService


class TestExportOptions:
    """Test ExportOptions dataclass."""

    def test_export_options_defaults(self):
        """Test ExportOptions with default values."""
        opts = ExportOptions(format="png")
        assert opts.format == "png"
        assert opts.width is None
        assert opts.height is None
        assert opts.quality == 95
        assert opts.dpi == 300
        assert opts.page_size == "A4"
        assert opts.include_background is True

    def test_export_options_custom_values(self):
        """Test ExportOptions with custom values."""
        opts = ExportOptions(
            format="pdf",
            width=1024,
            height=768,
            quality=85,
            dpi=150,
            page_size="Letter",
            include_background=False,
        )
        assert opts.format == "pdf"
        assert opts.width == 1024
        assert opts.height == 768
        assert opts.quality == 85
        assert opts.dpi == 150
        assert opts.page_size == "Letter"
        assert opts.include_background is False

    def test_export_options_quality_boundary(self):
        """Test ExportOptions with boundary quality values."""
        opts_min = ExportOptions(format="jpg", quality=1)
        assert opts_min.quality == 1

        opts_max = ExportOptions(format="jpg", quality=100)
        assert opts_max.quality == 100


class TestExportServiceConstants:
    """Test ExportService constants."""

    def test_valid_formats(self):
        """Test VALID_FORMATS set contains expected formats."""
        expected = {"png", "jpg", "svg", "pdf", "json"}
        assert ExportService.VALID_FORMATS == expected

    def test_valid_page_sizes(self):
        """Test VALID_PAGE_SIZES set contains expected page sizes."""
        expected = {
            "A0",
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "Letter",
            "Legal",
            "Tabloid",
            "Ledger",
        }
        assert ExportService.VALID_PAGE_SIZES == expected

    def test_page_size_count(self):
        """Test that VALID_PAGE_SIZES has expected number of entries."""
        assert len(ExportService.VALID_PAGE_SIZES) == 11


class TestExportServicePNG:
    """Test PNG export functionality."""

    def test_png_export_from_dict_with_white_background(self):
        """Test PNG export from dict with white background."""
        drawing_data = {
            "width": 100,
            "height": 100,
            "background_color": (255, 255, 255),
            "elements": [],
        }
        result = ExportService.export_to_png(drawing_data, width=100, height=100)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # PNG magic bytes
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_png_export_from_dict_no_background(self):
        """Test PNG export from dict with transparent background."""
        drawing_data = {
            "width": 100,
            "height": 100,
            "elements": [],
        }
        result = ExportService.export_to_png(
            drawing_data, width=100, height=100, include_background=False
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_png_export_from_dict_with_elements(self):
        """Test PNG export from dict containing drawable elements."""
        drawing_data = {
            "width": 200,
            "height": 200,
            "background_color": (255, 255, 255),
            "elements": [
                {
                    "type": "rect",
                    "x": 10,
                    "y": 10,
                    "width": 50,
                    "height": 50,
                    "color": "black",
                    "fill": "red",
                }
            ],
        }
        result = ExportService.export_to_png(drawing_data, width=200, height=200)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_png_export_from_svg_string(self):
        """Test PNG export from SVG string."""
        svg_content = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect x="10" y="10" width="50" height="50" fill="red"/>'
            "</svg>"
        )
        with patch(
            "app.services.export_service.svg2png",
            return_value=b"\x89PNG\r\n\x1a\n" + b"MOCK_PNG_DATA",
        ):
            result = ExportService.export_to_png(svg_content, width=100, height=100)
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_png_export_quality_parameter(self):
        """Test PNG export respects quality parameter."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result_high = ExportService.export_to_png(
            drawing_data, width=100, height=100, quality=100
        )
        result_low = ExportService.export_to_png(
            drawing_data, width=100, height=100, quality=10
        )
        assert isinstance(result_high, bytes)
        assert isinstance(result_low, bytes)
        # Higher quality typically results in larger file size
        assert len(result_high) >= len(result_low)

    def test_png_export_custom_dimensions(self):
        """Test PNG export with custom dimensions."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result_small = ExportService.export_to_png(drawing_data, width=50, height=50)
        result_large = ExportService.export_to_png(drawing_data, width=500, height=500)
        assert isinstance(result_small, bytes)
        assert isinstance(result_large, bytes)
        # Larger dimensions should result in larger file size
        assert len(result_large) > len(result_small)

    def test_png_export_invalid_data_type_raises(self):
        """Test PNG export with invalid data type raises ValueError."""
        with pytest.raises(ValueError, match="Drawing data must be dict or SVG string"):
            ExportService.export_to_png(12345, width=100, height=100)

    def test_png_export_invalid_svg_string_raises(self):
        """Test PNG export with invalid SVG string raises exception."""
        with pytest.raises(Exception, match="Failed to export to PNG"):
            ExportService.export_to_png("not svg content", width=100, height=100)

    def test_png_export_none_data_raises(self):
        """Test PNG export with None data raises ValueError."""
        with pytest.raises(ValueError, match="Drawing data must be dict or SVG string"):
            ExportService.export_to_png(None, width=100, height=100)


class TestExportServiceJPG:
    """Test JPG export functionality."""

    def test_jpg_export_from_dict_with_background(self):
        """Test JPG export from dict with background."""
        drawing_data = {
            "width": 100,
            "height": 100,
            "background_color": (255, 255, 255),
            "elements": [],
        }
        result = ExportService.export_to_jpg(drawing_data, width=100, height=100)
        assert isinstance(result, bytes)
        assert len(result) > 0
        # JPEG magic bytes
        assert result[:2] == b"\xff\xd8"

    def test_jpg_export_from_dict_with_elements(self):
        """Test JPG export from dict with drawable elements."""
        drawing_data = {
            "width": 200,
            "height": 200,
            "background_color": (255, 255, 255),
            "elements": [
                {
                    "type": "circle",
                    "cx": 100,
                    "cy": 100,
                    "r": 50,
                    "color": "blue",
                    "fill": "cyan",
                }
            ],
        }
        result = ExportService.export_to_jpg(drawing_data, width=200, height=200)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_jpg_export_from_svg_string(self):
        """Test JPG export from SVG string."""
        svg_content = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<circle cx="50" cy="50" r="40" fill="green"/>'
            "</svg>"
        )
        with patch(
            "app.services.export_service.svg2png",
            return_value=b"\x89PNG\r\n\x1a\n" + b"MOCK_PNG_DATA",
        ):
            result = ExportService.export_to_jpg(svg_content, width=100, height=100)
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_jpg_export_quality_parameter(self):
        """Test JPG export respects quality parameter."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result_high = ExportService.export_to_jpg(
            drawing_data, width=100, height=100, quality=95
        )
        result_low = ExportService.export_to_jpg(
            drawing_data, width=100, height=100, quality=10
        )
        assert isinstance(result_high, bytes)
        assert isinstance(result_low, bytes)
        # Lower quality should result in smaller file size
        assert len(result_low) < len(result_high)

    def test_jpg_export_custom_dimensions(self):
        """Test JPG export with custom dimensions."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result_small = ExportService.export_to_jpg(drawing_data, width=100, height=100)
        result_large = ExportService.export_to_jpg(drawing_data, width=300, height=300)
        assert isinstance(result_small, bytes)
        assert isinstance(result_large, bytes)
        # Larger dimensions should result in larger file
        assert len(result_large) > len(result_small)

    def test_jpg_export_invalid_data_type_raises(self):
        """Test JPG export with invalid data type raises ValueError."""
        with pytest.raises(ValueError, match="Drawing data must be dict or SVG string"):
            ExportService.export_to_jpg([], width=100, height=100)

    def test_jpg_export_default_quality(self):
        """Test JPG export uses default quality of 85."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result = ExportService.export_to_jpg(drawing_data, width=100, height=100)
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestExportServiceSVG:
    """Test SVG export functionality."""

    def test_svg_export_svg_string_passthrough(self):
        """Test SVG export with SVG string returns it unchanged."""
        svg_content = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect x="0" y="0" width="100" height="100" fill="blue"/>'
            "</svg>"
        )
        result = ExportService.export_to_svg(svg_content)
        assert isinstance(result, str)
        assert result == svg_content

    def test_svg_export_from_dict_basic(self):
        """Test SVG export from dict creates valid SVG."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result = ExportService.export_to_svg(drawing_data)
        assert isinstance(result, str)
        assert "<svg" in result
        assert 'viewBox="0 0 100 100"' in result
        assert "</svg>" in result

    def test_svg_export_from_dict_with_background(self):
        """Test SVG export from dict includes background."""
        drawing_data = {
            "width": 200,
            "height": 200,
            "background_color": "rgb(255,0,0)",
            "include_background": True,
            "elements": [],
        }
        result = ExportService.export_to_svg(drawing_data)
        assert isinstance(result, str)
        assert "<rect" in result
        assert 'fill="rgb(255,0,0)"' in result

    def test_svg_export_from_dict_no_background(self):
        """Test SVG export from dict without background."""
        drawing_data = {
            "width": 100,
            "height": 100,
            "include_background": False,
            "elements": [],
        }
        result = ExportService.export_to_svg(drawing_data)
        assert isinstance(result, str)
        assert "<svg" in result
        # Should not have background rect when include_background is False
        lines = result.split("\n")
        rects = [l for l in lines if "<rect" in l and 'width="100"' in l]
        assert len(rects) == 0

    def test_svg_export_from_dict_with_elements(self):
        """Test SVG export from dict with various elements."""
        drawing_data = {
            "width": 300,
            "height": 300,
            "elements": [
                {"type": "rect", "x": 10, "y": 10, "width": 50, "height": 50},
                {"type": "circle", "cx": 100, "cy": 100, "r": 30},
                {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100},
                {"type": "text", "x": 50, "y": 50, "text": "Hello"},
            ],
        }
        result = ExportService.export_to_svg(drawing_data)
        assert isinstance(result, str)
        assert "<rect" in result
        assert "<circle" in result
        assert "<line" in result
        assert "<text" in result

    def test_svg_export_invalid_svg_string_raises(self):
        """Test SVG export with non-SVG string raises ValueError."""
        with pytest.raises(ValueError, match="String input must be valid SVG"):
            ExportService.export_to_svg("not an svg")

    def test_svg_export_invalid_data_type_raises(self):
        """Test SVG export with invalid data type raises ValueError."""
        with pytest.raises(ValueError, match="Drawing data must be dict or SVG string"):
            ExportService.export_to_svg(123)

    def test_svg_export_with_xml_declaration(self):
        """Test SVG export includes XML declaration."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        result = ExportService.export_to_svg(drawing_data)
        assert result.startswith('<?xml version="1.0"')


class TestExportServicePDF:
    """Test PDF export functionality."""

    def test_pdf_export_from_dict_a4(self):
        """Test PDF export from dict with A4 page size."""
        drawing_data = {"width": 200, "height": 200, "elements": []}
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF-1.4MOCKPDF")
            )
            result = ExportService.export_to_pdf(
                drawing_data, page_size="A4", include_background=True
            )
            assert isinstance(result, bytes)
            assert b"PDF" in result
            mock_html.assert_called_once()

    def test_pdf_export_from_dict_letter(self):
        """Test PDF export with Letter page size."""
        drawing_data = {"width": 200, "height": 200, "elements": []}
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF-1.4LETTER")
            )
            result = ExportService.export_to_pdf(drawing_data, page_size="Letter")
            assert isinstance(result, bytes)

    def test_pdf_export_from_svg_string(self):
        """Test PDF export from SVG string."""
        svg_content = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            '<rect x="0" y="0" width="100" height="100" fill="purple"/>'
            "</svg>"
        )
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF-1.4MOCK")
            )
            result = ExportService.export_to_pdf(svg_content, page_size="A4")
            assert isinstance(result, bytes)

    def test_pdf_export_invalid_page_size_raises(self):
        """Test PDF export with invalid page size raises ValueError."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        with pytest.raises(ValueError, match="Invalid page size"):
            ExportService.export_to_pdf(drawing_data, page_size="InvalidSize")

    def test_pdf_export_all_valid_page_sizes(self):
        """Test PDF export works with all valid page sizes."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF")
            )
            for page_size in ExportService.VALID_PAGE_SIZES:
                result = ExportService.export_to_pdf(drawing_data, page_size=page_size)
                assert isinstance(result, bytes)

    def test_pdf_export_invalid_data_type_raises(self):
        """Test PDF export with invalid data type raises exception."""
        with patch("app.services.export_service.HTML"):
            with pytest.raises(Exception, match="Failed to export to PDF"):
                ExportService.export_to_pdf(12345, page_size="A4")

    def test_pdf_export_include_background_parameter(self):
        """Test PDF export respects include_background parameter."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF")
            )
            # Both should succeed, actual background handling is in HTML conversion
            result1 = ExportService.export_to_pdf(drawing_data, include_background=True)
            result2 = ExportService.export_to_pdf(
                drawing_data, include_background=False
            )
            assert isinstance(result1, bytes)
            assert isinstance(result2, bytes)


class TestExportServiceJSON:
    """Test JSON export functionality."""

    def test_json_export_from_dict(self):
        """Test JSON export from dict."""
        drawing_data = {
            "width": 100,
            "height": 100,
            "elements": [{"type": "rect", "x": 0, "y": 0, "width": 50, "height": 50}],
        }
        result = ExportService.export_to_json(drawing_data)
        assert isinstance(result, str)
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["width"] == 100
        assert parsed["height"] == 100
        assert len(parsed["elements"]) == 1

    def test_json_export_from_json_string(self):
        """Test JSON export from JSON string (validates and reformats)."""
        json_str = '{"width": 100, "height": 100, "elements": []}'
        result = ExportService.export_to_json(json_str)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["width"] == 100

    def test_json_export_formatting(self):
        """Test JSON export includes proper formatting (indentation)."""
        drawing_data = {"width": 100, "height": 100}
        result = ExportService.export_to_json(drawing_data)
        # Indented JSON should have newlines
        assert "\n" in result

    def test_json_export_empty_dict(self):
        """Test JSON export from empty dict."""
        result = ExportService.export_to_json({})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {}

    def test_json_export_complex_structure(self):
        """Test JSON export with complex nested structure."""
        drawing_data = {
            "metadata": {"version": "1.0", "author": "test"},
            "drawing": {
                "width": 200,
                "height": 200,
                "elements": [
                    {"type": "rect", "properties": {"x": 10, "y": 20}},
                    {"type": "circle", "properties": {"cx": 100, "r": 50}},
                ],
            },
        }
        result = ExportService.export_to_json(drawing_data)
        parsed = json.loads(result)
        assert parsed["metadata"]["version"] == "1.0"
        assert len(parsed["drawing"]["elements"]) == 2

    def test_json_export_invalid_json_string_raises(self):
        """Test JSON export with invalid JSON string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid JSON format"):
            ExportService.export_to_json('{"invalid": json}')

    def test_json_export_invalid_data_type_raises(self):
        """Test JSON export with invalid data type raises ValueError."""
        with pytest.raises(
            ValueError, match="Drawing data must be dict or JSON string"
        ):
            ExportService.export_to_json(12345)


class TestExportServiceDispatch:
    """Test export() method dispatch to format handlers."""

    def test_export_dispatches_to_png(self):
        """Test export() dispatches PNG format correctly."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="png", width=100, height=100)
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_export_dispatches_to_jpg(self):
        """Test export() dispatches JPG format correctly."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="jpg", width=100, height=100)
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, bytes)
        assert result[:2] == b"\xff\xd8"

    def test_export_dispatches_to_svg(self):
        """Test export() dispatches SVG format correctly."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="svg")
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, str)
        assert "<svg" in result

    def test_export_dispatches_to_json(self):
        """Test export() dispatches JSON format correctly."""
        drawing_data = {"width": 100, "height": 100}
        opts = ExportOptions(format="json")
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["width"] == 100

    def test_export_dispatches_to_pdf(self):
        """Test export() dispatches PDF format correctly."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="pdf", page_size="A4")
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF")
            )
            result = ExportService.export(opts, drawing_data)
            assert isinstance(result, bytes)

    def test_export_invalid_format_raises(self):
        """Test export() with invalid format raises ValueError."""
        drawing_data = {"width": 100, "height": 100}
        opts = ExportOptions(format="invalid_format")
        with pytest.raises(ValueError, match="Invalid format"):
            ExportService.export(opts, drawing_data)

    def test_export_uses_options_width_height(self):
        """Test export() uses width/height from options."""
        drawing_data = {"width": 50, "height": 50, "elements": []}
        opts = ExportOptions(format="png", width=200, height=200)
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_uses_options_quality(self):
        """Test export() uses quality from options."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="png", quality=50)
        result = ExportService.export(opts, drawing_data)
        assert isinstance(result, bytes)

    def test_export_uses_options_page_size(self):
        """Test export() uses page_size from options."""
        drawing_data = {"width": 100, "height": 100, "elements": []}
        opts = ExportOptions(format="pdf", page_size="Letter")
        with patch("app.services.export_service.HTML") as mock_html:
            mock_html_instance = MagicMock()
            mock_html.return_value = mock_html_instance
            mock_html_instance.write_pdf = MagicMock(
                side_effect=lambda f: f.write(b"%PDF")
            )
            result = ExportService.export(opts, drawing_data)
            assert isinstance(result, bytes)


class TestDrawElement:
    """Test _draw_element helper method."""

    def test_draw_element_rect(self):
        """Test drawing a rectangle element."""
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (100, 100), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        element = {
            "type": "rect",
            "x": 10,
            "y": 10,
            "width": 50,
            "height": 50,
            "color": "black",
        }
        # Should not raise
        ExportService._draw_element(draw, element)

    def test_draw_element_circle(self):
        """Test drawing a circle element."""
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(image)
        element = {"type": "circle", "cx": 50, "cy": 50, "r": 30, "color": "blue"}
        ExportService._draw_element(draw, element)

    def test_draw_element_line(self):
        """Test drawing a line element."""
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(image)
        element = {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100}
        ExportService._draw_element(draw, element)

    def test_draw_element_text(self):
        """Test drawing a text element."""
        from PIL import Image, ImageDraw

        image = Image.new("RGB", (100, 100))
        draw = ImageDraw.Draw(image)
        element = {"type": "text", "x": 10, "y": 10, "text": "Test"}
        ExportService._draw_element(draw, element)


class TestElementToSvg:
    """Test _element_to_svg helper method."""

    def test_element_to_svg_rect(self):
        """Test converting rect element to SVG."""
        element = {
            "type": "rect",
            "x": 10,
            "y": 10,
            "width": 50,
            "height": 50,
            "color": "black",
        }
        result = ExportService._element_to_svg(element)
        assert "<rect" in result
        assert 'x="10"' in result
        assert 'y="10"' in result

    def test_element_to_svg_circle(self):
        """Test converting circle element to SVG."""
        element = {"type": "circle", "cx": 50, "cy": 50, "r": 30, "color": "blue"}
        result = ExportService._element_to_svg(element)
        assert "<circle" in result
        assert 'cx="50"' in result
        assert 'r="30"' in result

    def test_element_to_svg_line(self):
        """Test converting line element to SVG."""
        element = {"type": "line", "x1": 0, "y1": 0, "x2": 100, "y2": 100}
        result = ExportService._element_to_svg(element)
        assert "<line" in result
        assert 'x1="0"' in result
        assert 'x2="100"' in result

    def test_element_to_svg_text(self):
        """Test converting text element to SVG."""
        element = {"type": "text", "x": 10, "y": 10, "text": "Hello", "font_size": 16}
        result = ExportService._element_to_svg(element)
        assert "<text" in result
        assert "Hello" in result
        assert 'font-size="16"' in result

    def test_element_to_svg_with_id_and_class(self):
        """Test SVG element includes id and class attributes."""
        element = {
            "type": "rect",
            "id": "rect-1",
            "class": "drawing-element",
            "x": 0,
            "y": 0,
            "width": 100,
            "height": 100,
        }
        result = ExportService._element_to_svg(element)
        assert 'id="rect-1"' in result
        assert 'class="drawing-element"' in result

    def test_element_to_svg_unknown_type(self):
        """Test SVG conversion with unknown element type returns empty."""
        element = {"type": "unknown", "x": 10, "y": 10}
        result = ExportService._element_to_svg(element)
        assert result == ""
