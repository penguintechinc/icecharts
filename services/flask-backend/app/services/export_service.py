"""Export Service for IceCharts Drawings.

Provides functionality to export drawing content to various formats:
- PNG (raster image)
- SVG (vector image)
- PDF (portable document - requires weasyprint)
- JSON (data interchange)
"""

import io
import json
from dataclasses import dataclass
from typing import Optional, Union

from PIL import Image, ImageDraw

# Optional PDF export support - requires weasyprint (heavy dependencies)
try:
    from weasyprint import CSS, HTML

    PDF_EXPORT_AVAILABLE = True
except ImportError:
    PDF_EXPORT_AVAILABLE = False
    CSS = None  # type: ignore
    HTML = None  # type: ignore


@dataclass(slots=True)
class ExportOptions:
    """Export options for drawings."""

    format: str  # png, jpg, svg, pdf, json
    width: Optional[int] = None
    height: Optional[int] = None
    quality: int = 95  # For PNG and JPG (1-100)
    dpi: int = 300  # For PDF and high-res exports
    page_size: str = "A4"  # A4, Letter, A3, etc. for PDF
    include_background: bool = True


class ExportService:
    """Service for exporting drawing content to various formats."""

    VALID_FORMATS = {"png", "jpg", "svg", "pdf", "json"}
    VALID_PAGE_SIZES = {
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

    @staticmethod
    def export_to_png(
        drawing_data: Union[dict, str],
        width: int = 800,
        height: int = 600,
        quality: int = 95,
        include_background: bool = True,
    ) -> bytes:
        """Export drawing to PNG format.

        Args:
            drawing_data: Drawing content (dict with structure or SVG string)
            width: Image width in pixels
            height: Image height in pixels
            quality: PNG compression quality (1-100)
            include_background: Whether to include background

        Returns:
            PNG image bytes

        Raises:
            ValueError: If drawing_data format is invalid
            Exception: If PNG generation fails
        """
        try:
            # Handle different input formats
            if isinstance(drawing_data, str):
                # Assume it's SVG content - convert via CairoSVG
                from cairosvg import svg2png

                png_bytes = svg2png(
                    bytestring=drawing_data.encode("utf-8"),
                    write_to=io.BytesIO(),
                    output_width=width,
                    output_height=height,
                )
                return png_bytes

            # Handle dict-based drawing data
            if isinstance(drawing_data, dict):
                # Create blank image with optional background
                if include_background:
                    bg_color = drawing_data.get("background_color", (255, 255, 255))
                    image = Image.new("RGB", (width, height), bg_color)
                else:
                    # Force RGBA with fully transparent background
                    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

                # Draw elements from drawing_data
                draw = ImageDraw.Draw(image)
                elements = drawing_data.get("elements", [])

                for element in elements:
                    ExportService._draw_element(draw, element)

                # Convert to PNG bytes
                png_bytes = io.BytesIO()
                image.save(png_bytes, format="PNG", quality=quality)
                png_bytes.seek(0)
                return png_bytes.getvalue()

            raise ValueError("Drawing data must be dict or SVG string")

        except Exception as e:
            raise Exception(f"Failed to export to PNG: {str(e)}") from e

    @staticmethod
    def export_to_jpg(
        drawing_data: Union[dict, str],
        width: int = 800,
        height: int = 600,
        quality: int = 85,
    ) -> bytes:
        """Export drawing to JPG format.

        Args:
            drawing_data: Drawing content (dict with structure or SVG string)
            width: Image width in pixels
            height: Image height in pixels
            quality: JPG quality (1-100, default 85)

        Returns:
            JPG image bytes

        Raises:
            ValueError: If drawing_data format is invalid
            Exception: If JPG generation fails
        """
        try:
            # Handle different input formats
            if isinstance(drawing_data, str):
                # Assume it's SVG content - convert via CairoSVG
                from cairosvg import svg2png

                png_bytes = svg2png(
                    bytestring=drawing_data.encode("utf-8"),
                    write_to=io.BytesIO(),
                    output_width=width,
                    output_height=height,
                )
                # Convert PNG bytes to PIL Image, then to JPG
                png_image = Image.open(io.BytesIO(png_bytes))
                if png_image.mode in ("RGBA", "LA", "P"):
                    # Convert RGBA to RGB with white background
                    rgb_image = Image.new("RGB", png_image.size, (255, 255, 255))
                    rgb_image.paste(
                        png_image,
                        mask=(
                            png_image.split()[-1]
                            if png_image.mode in ("RGBA", "LA")
                            else None
                        ),
                    )
                    png_image = rgb_image
                jpg_bytes = io.BytesIO()
                png_image.save(jpg_bytes, format="JPEG", quality=quality)
                jpg_bytes.seek(0)
                return jpg_bytes.getvalue()

            # Handle dict-based drawing data
            if isinstance(drawing_data, dict):
                # Create blank RGB image (JPG doesn't support transparency)
                bg_color = drawing_data.get("background_color", (255, 255, 255))
                image = Image.new("RGB", (width, height), bg_color)

                # Draw elements from drawing_data
                draw = ImageDraw.Draw(image)
                elements = drawing_data.get("elements", [])

                for element in elements:
                    ExportService._draw_element(draw, element)

                # Convert to JPG bytes
                jpg_bytes = io.BytesIO()
                image.save(jpg_bytes, format="JPEG", quality=quality)
                jpg_bytes.seek(0)
                return jpg_bytes.getvalue()

            raise ValueError("Drawing data must be dict or SVG string")

        except Exception as e:
            raise Exception(f"Failed to export to JPG: {str(e)}") from e

    @staticmethod
    def export_to_svg(drawing_data: Union[dict, str]) -> str:
        """Export drawing to SVG format.

        Args:
            drawing_data: Drawing content (dict or SVG string)

        Returns:
            SVG content as string

        Raises:
            ValueError: If drawing_data format is invalid
            Exception: If SVG generation fails
        """
        try:
            # If already SVG string, return it
            if isinstance(drawing_data, str):
                if drawing_data.strip().startswith("<svg"):
                    return drawing_data
                raise ValueError("String input must be valid SVG")

            # Build SVG from dict-based drawing data
            if isinstance(drawing_data, dict):
                width = drawing_data.get("width", 800)
                height = drawing_data.get("height", 600)
                viewbox = f"0 0 {width} {height}"

                # Start SVG element
                svg_lines = [
                    '<?xml version="1.0" encoding="UTF-8"?>',
                    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" '
                    f'width="{width}" height="{height}">',
                ]

                # Add background if present
                if drawing_data.get("include_background", True):
                    bg_color = drawing_data.get("background_color", "rgb(255,255,255)")
                    svg_lines.append(
                        f'<rect width="{width}" height="{height}" fill="{bg_color}"/>'
                    )

                # Add elements
                elements = drawing_data.get("elements", [])
                for element in elements:
                    svg_element = ExportService._element_to_svg(element)
                    if svg_element:
                        svg_lines.append(svg_element)

                # Close SVG
                svg_lines.append("</svg>")

                return "\n".join(svg_lines)

            raise ValueError("Drawing data must be dict or SVG string")

        except Exception as e:
            raise Exception(f"Failed to export to SVG: {str(e)}") from e

    @staticmethod
    def export_to_pdf(
        drawing_data: Union[dict, str],
        page_size: str = "A4",
        include_background: bool = True,
    ) -> bytes:
        """Export drawing to PDF format.

        Args:
            drawing_data: Drawing content (dict or SVG string)
            page_size: PDF page size (A4, Letter, A3, etc.)
            include_background: Whether to include background

        Returns:
            PDF document bytes

        Raises:
            ValueError: If page_size is invalid or drawing_data format is invalid
            Exception: If PDF generation fails
        """
        try:
            if page_size not in ExportService.VALID_PAGE_SIZES:
                raise ValueError(
                    f"Invalid page size. Must be one of: {ExportService.VALID_PAGE_SIZES}"
                )

            # Get SVG content
            if isinstance(drawing_data, dict):
                svg_content = ExportService.export_to_svg(drawing_data)
            else:
                svg_content = drawing_data

            # Create HTML with SVG for WeasyPrint
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    @page {{
                        size: {page_size};
                        margin: 0;
                    }}
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                {svg_content}
            </body>
            </html>
            """

            # Generate PDF
            pdf_bytes = io.BytesIO()
            HTML(string=html_content).write_pdf(pdf_bytes)
            pdf_bytes.seek(0)
            return pdf_bytes.getvalue()

        except Exception as e:
            raise Exception(f"Failed to export to PDF: {str(e)}") from e

    @staticmethod
    def export_to_json(drawing_data: Union[dict, str]) -> str:
        """Export drawing to JSON format.

        Args:
            drawing_data: Drawing content (dict or JSON string)

        Returns:
            JSON string

        Raises:
            ValueError: If drawing_data format is invalid
            Exception: If JSON generation fails
        """
        try:
            if isinstance(drawing_data, str):
                # Validate and reformat JSON
                parsed = json.loads(drawing_data)
                return json.dumps(parsed, indent=2)

            if isinstance(drawing_data, dict):
                return json.dumps(drawing_data, indent=2)

            raise ValueError("Drawing data must be dict or JSON string")

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}") from e
        except Exception as e:
            raise Exception(f"Failed to export to JSON: {str(e)}") from e

    @staticmethod
    def export(
        options: ExportOptions, drawing_data: Union[dict, str]
    ) -> Union[bytes, str]:
        """Export drawing using specified format and options.

        Args:
            options: Export options
            drawing_data: Drawing content

        Returns:
            Exported content (bytes for binary formats, str for text formats)

        Raises:
            ValueError: If format is invalid or options are invalid
            Exception: If export fails
        """
        if options.format not in ExportService.VALID_FORMATS:
            raise ValueError(
                f"Invalid format. Must be one of: {ExportService.VALID_FORMATS}"
            )

        if options.format == "png":
            return ExportService.export_to_png(
                drawing_data,
                width=options.width or 800,
                height=options.height or 600,
                quality=options.quality,
                include_background=options.include_background,
            )

        if options.format == "jpg":
            return ExportService.export_to_jpg(
                drawing_data,
                width=options.width or 800,
                height=options.height or 600,
                quality=options.quality,
            )

        if options.format == "svg":
            return ExportService.export_to_svg(drawing_data)

        if options.format == "pdf":
            return ExportService.export_to_pdf(
                drawing_data,
                page_size=options.page_size,
                include_background=options.include_background,
            )

        if options.format == "json":
            return ExportService.export_to_json(drawing_data)

        raise ValueError(f"Unsupported format: {options.format}")

    @staticmethod
    def _draw_element(draw: ImageDraw.ImageDraw, element: dict) -> None:
        """Draw a single element on PIL Image.

        Args:
            draw: PIL ImageDraw object
            element: Element data with type and properties
        """
        element_type = element.get("type", "").lower()
        color = element.get("color", "black")
        fill = element.get("fill", None)

        if element_type == "rect":
            x = element.get("x", 0)
            y = element.get("y", 0)
            width = element.get("width", 100)
            height = element.get("height", 100)
            draw.rectangle(
                [(x, y), (x + width, y + height)],
                fill=fill,
                outline=color,
                width=element.get("stroke_width", 1),
            )

        elif element_type == "circle":
            cx = element.get("cx", 0)
            cy = element.get("cy", 0)
            radius = element.get("r", 50)
            draw.ellipse(
                [(cx - radius, cy - radius), (cx + radius, cy + radius)],
                fill=fill,
                outline=color,
                width=element.get("stroke_width", 1),
            )

        elif element_type == "line":
            x1 = element.get("x1", 0)
            y1 = element.get("y1", 0)
            x2 = element.get("x2", 100)
            y2 = element.get("y2", 100)
            draw.line(
                [(x1, y1), (x2, y2)],
                fill=color,
                width=element.get("stroke_width", 1),
            )

        elif element_type == "text":
            x = element.get("x", 0)
            y = element.get("y", 0)
            text = element.get("text", "")
            draw.text((x, y), text, fill=color)

    @staticmethod
    def _element_to_svg(element: dict) -> str:
        """Convert element dict to SVG string.

        Args:
            element: Element data

        Returns:
            SVG element string
        """
        element_type = element.get("type", "").lower()
        attrs = []

        # Common attributes
        if "id" in element:
            attrs.append(f'id="{element["id"]}"')
        if "class" in element:
            attrs.append(f'class="{element["class"]}"')

        stroke = element.get("color", "black")
        stroke_width = element.get("stroke_width", 1)
        fill = element.get("fill", "none")

        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{stroke_width}"')

        if element_type == "rect":
            attrs.append(f'x="{element.get("x", 0)}"')
            attrs.append(f'y="{element.get("y", 0)}"')
            attrs.append(f'width="{element.get("width", 100)}"')
            attrs.append(f'height="{element.get("height", 100)}"')
            attrs.append(f'fill="{fill}"')
            return f'<rect {" ".join(attrs)} />'

        elif element_type == "circle":
            attrs.append(f'cx="{element.get("cx", 0)}"')
            attrs.append(f'cy="{element.get("cy", 0)}"')
            attrs.append(f'r="{element.get("r", 50)}"')
            attrs.append(f'fill="{fill}"')
            return f'<circle {" ".join(attrs)} />'

        elif element_type == "line":
            attrs.append(f'x1="{element.get("x1", 0)}"')
            attrs.append(f'y1="{element.get("y1", 0)}"')
            attrs.append(f'x2="{element.get("x2", 100)}"')
            attrs.append(f'y2="{element.get("y2", 100)}"')
            return f'<line {" ".join(attrs)} />'

        elif element_type == "text":
            text = element.get("text", "")
            font_size = element.get("font_size", 12)
            attrs.append(f'x="{element.get("x", 0)}"')
            attrs.append(f'y="{element.get("y", 0)}"')
            attrs.append(f'font-size="{font_size}"')
            attrs.append(f'fill="{fill}"')
            return f'<text {" ".join(attrs)}>{text}</text>'

        return ""
