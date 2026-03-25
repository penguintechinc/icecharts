/**
 * ExportDialog Component Tests
 *
 * Tests for format selection, quality slider, export trigger, and error handling.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// Mock useExport hook — defined before importing the component
const mockExportDrawing = vi.fn();
const mockUseExport = vi.fn(() => ({
  loading: false,
  error: null,
  success: false,
  exportDrawing: mockExportDrawing,
  exportProgress: null,
}));

vi.mock('@/client/hooks/useExport', () => ({
  useExport: () => mockUseExport(),
}));

// Mock api client used inside useExport internals (prevent module errors)
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import { ExportDialog } from '@/client/components/drawing/ExportDialog';

describe('ExportDialog Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockExportDrawing.mockResolvedValue(new Blob());
    mockUseExport.mockReturnValue({
      loading: false,
      error: null,
      success: false,
      exportDrawing: mockExportDrawing,
      exportProgress: null,
    });
  });

  it('does not render when isOpen is false', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={false} onClose={vi.fn()} />
    );
    expect(screen.queryByText('Export Drawing')).toBeNull();
  });

  it('renders Export Drawing title when open', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    expect(screen.getByText('Export Drawing')).toBeDefined();
  });

  it('renders format buttons: PNG, SVG, PDF, JSON, JPG', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    expect(screen.getByRole('button', { name: 'PNG' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'SVG' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'PDF' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'JSON' })).toBeDefined();
    expect(screen.getByRole('button', { name: 'JPG' })).toBeDefined();
  });

  it('shows PNG-specific options (width, height, quality) by default', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    // Labels in ExportDialog use <label> without htmlFor; use getByText
    expect(screen.getByText('Width')).toBeDefined();
    expect(screen.getByText('Height')).toBeDefined();
    // Quality label includes current value
    expect(screen.getByText(/Quality: \d+%/)).toBeDefined();
  });

  it('switches to PDF format and shows page size dropdown', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: 'PDF' }));
    expect(screen.getByText('Page Size')).toBeDefined();
  });

  it('switches to SVG format and hides PNG dimension options', () => {
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    fireEvent.click(screen.getByRole('button', { name: 'SVG' }));
    // PNG width/height inputs should be gone for SVG
    expect(screen.queryByText('Width')).toBeNull();
    // SVG shows include background checkbox label
    expect(screen.getByText('Include background')).toBeDefined();
  });

  it('calls exportDrawing with correct args when Download button is clicked', async () => {
    const onClose = vi.fn();
    render(
      <ExportDialog drawingId="drawing-42" isOpen={true} onClose={onClose} />
    );

    fireEvent.click(screen.getByRole('button', { name: 'Download' }));

    await waitFor(() => {
      expect(mockExportDrawing).toHaveBeenCalledWith(
        'drawing-42',
        expect.objectContaining({ format: 'png' })
      );
    });
  });

  it('calls onClose when Cancel button is clicked', () => {
    const onClose = vi.fn();
    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={onClose} />
    );
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('displays error message when hook reports an error', () => {
    mockUseExport.mockReturnValue({
      loading: false,
      error: 'Export failed due to network error',
      success: false,
      exportDrawing: mockExportDrawing,
      exportProgress: null,
    });

    render(
      <ExportDialog drawingId="drawing-1" isOpen={true} onClose={vi.fn()} />
    );
    expect(screen.getByText('Export failed due to network error')).toBeDefined();
  });
});
