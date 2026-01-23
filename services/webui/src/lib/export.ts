// Client-side export helpers for IceCharts drawings

import html2canvas from 'html2canvas';

interface ExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'json';
  width?: number;
  height?: number;
  quality?: number;
  includeBackground?: boolean;
}

/**
 * Create a quick preview PNG from canvas element using html2canvas
 * Useful for client-side preview before server export
 */
export async function createCanvasPreview(
  canvasElement: HTMLElement,
  width: number = 800,
  height: number = 600,
  quality: number = 0.8
): Promise<Blob> {
  try {
    const canvas = await html2canvas(canvasElement, {
      width,
      height,
      scale: quality,
      backgroundColor: '#ffffff',
      useCORS: true,
      allowTaint: true,
    });

    return new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create preview blob'));
          }
        },
        'image/png',
        quality
      );
    });
  } catch (error) {
    throw new Error(`Failed to create canvas preview: ${error}`);
  }
}

/**
 * Convert canvas to data URL for preview display
 */
export async function canvasToDataUrl(
  canvasElement: HTMLElement,
  width: number = 800,
  height: number = 600
): Promise<string> {
  try {
    const canvas = await html2canvas(canvasElement, {
      width,
      height,
      backgroundColor: '#ffffff',
      useCORS: true,
    });

    return canvas.toDataURL('image/png');
  } catch (error) {
    throw new Error(`Failed to convert canvas to data URL: ${error}`);
  }
}

/**
 * Download a blob as file
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

/**
 * Download JSON data as file
 */
export function downloadJson(data: unknown, filename: string): void {
  const jsonString = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonString], { type: 'application/json' });
  downloadBlob(blob, filename);
}

/**
 * Download SVG as file
 */
export function downloadSvg(svgContent: string, filename: string): void {
  const blob = new Blob([svgContent], { type: 'image/svg+xml' });
  downloadBlob(blob, filename);
}

/**
 * Convert drawing data to SVG string (client-side, basic implementation)
 * Note: For production, use server-side export service for full features
 */
export function drawingToSvg(
  drawingData: Record<string, unknown>,
  width: number = 800,
  height: number = 600
): string {
  const viewbox = `0 0 ${width} ${height}`;

  const svgLines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewbox}" width="${width}" height="${height}">`,
  ];

  // Add background
  const bgColor = (drawingData.background_color as string) || 'rgb(255,255,255)';
  svgLines.push(`<rect width="${width}" height="${height}" fill="${bgColor}"/>`);

  // Add elements (simplified - adapt based on your drawing structure)
  const elements = (drawingData.elements as unknown[]) || [];
  for (const element of elements) {
    const svgElement = elementToSvgString(element);
    if (svgElement) {
      svgLines.push(svgElement);
    }
  }

  svgLines.push('</svg>');

  return svgLines.join('\n');
}

/**
 * Convert a single element to SVG string
 */
function elementToSvgString(element: unknown): string {
  if (typeof element !== 'object' || !element) return '';

  const el = element as Record<string, unknown>;
  const type = (el.type as string)?.toLowerCase();

  const attrs: string[] = [];

  // Common attributes
  if (el.id) attrs.push(`id="${el.id}"`);
  if (el.class) attrs.push(`class="${el.class}"`);

  const stroke = (el.color as string) || 'black';
  const strokeWidth = (el.stroke_width as number) || 1;
  const fill = (el.fill as string) || 'none';

  attrs.push(`stroke="${stroke}"`);
  attrs.push(`stroke-width="${strokeWidth}"`);

  if (type === 'rect') {
    attrs.push(`x="${el.x || 0}"`);
    attrs.push(`y="${el.y || 0}"`);
    attrs.push(`width="${el.width || 100}"`);
    attrs.push(`height="${el.height || 100}"`);
    attrs.push(`fill="${fill}"`);
    return `<rect ${attrs.join(' ')} />`;
  }

  if (type === 'circle') {
    attrs.push(`cx="${el.cx || 0}"`);
    attrs.push(`cy="${el.cy || 0}"`);
    attrs.push(`r="${el.r || 50}"`);
    attrs.push(`fill="${fill}"`);
    return `<circle ${attrs.join(' ')} />`;
  }

  if (type === 'line') {
    attrs.push(`x1="${el.x1 || 0}"`);
    attrs.push(`y1="${el.y1 || 0}"`);
    attrs.push(`x2="${el.x2 || 100}"`);
    attrs.push(`y2="${el.y2 || 100}"`);
    return `<line ${attrs.join(' ')} />`;
  }

  if (type === 'text') {
    const text = el.text as string;
    const fontSize = (el.font_size as number) || 12;
    attrs.push(`x="${el.x || 0}"`);
    attrs.push(`y="${el.y || 0}"`);
    attrs.push(`font-size="${fontSize}"`);
    attrs.push(`fill="${fill}"`);
    return `<text ${attrs.join(' ')}>${text}</text>`;
  }

  return '';
}

/**
 * Validate export options
 */
export function validateExportOptions(options: ExportOptions): { valid: boolean; error?: string } {
  if (!['png', 'svg', 'pdf', 'json'].includes(options.format)) {
    return { valid: false, error: 'Invalid export format' };
  }

  if (options.format === 'png') {
    if (options.width && (options.width < 100 || options.width > 4000)) {
      return { valid: false, error: 'Width must be between 100 and 4000 pixels' };
    }
    if (options.height && (options.height < 100 || options.height > 4000)) {
      return { valid: false, error: 'Height must be between 100 and 4000 pixels' };
    }
    if (options.quality && (options.quality < 1 || options.quality > 100)) {
      return { valid: false, error: 'Quality must be between 1 and 100' };
    }
  }

  return { valid: true };
}

/**
 * Get file extension for format
 */
export function getExtensionForFormat(format: string): string {
  const extensions: Record<string, string> = {
    png: 'png',
    svg: 'svg',
    pdf: 'pdf',
    json: 'json',
  };
  return extensions[format] || format;
}

/**
 * Get MIME type for format
 */
export function getMimeTypeForFormat(format: string): string {
  const mimeTypes: Record<string, string> = {
    png: 'image/png',
    svg: 'image/svg+xml',
    pdf: 'application/pdf',
    json: 'application/json',
  };
  return mimeTypes[format] || 'application/octet-stream';
}
