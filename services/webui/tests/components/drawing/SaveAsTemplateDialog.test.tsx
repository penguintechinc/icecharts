/**
 * SaveAsTemplateDialog Component Tests
 *
 * Tests for form fields, submission, and success callback.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

// Mock api client
vi.mock('@/client/lib/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock FormModalBuilder from @penguintechinc/react-libs
// It renders a form with the provided fields
vi.mock('@penguintechinc/react-libs', () => ({
  FormModalBuilder: ({
    title,
    isOpen,
    onClose,
    fields,
    onSubmit,
    submitButtonText,
  }: {
    title: string;
    isOpen: boolean;
    onClose: () => void;
    fields: Array<{ name: string; label: string; type: string }>;
    onSubmit: (data: Record<string, unknown>) => Promise<void>;
    submitButtonText?: string;
  }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="form-modal">
        <h2>{title}</h2>
        {fields.map((f) => (
          <label key={f.name}>
            {f.label}
            <input name={f.name} data-testid={`field-${f.name}`} />
          </label>
        ))}
        <button data-testid="submit-btn" onClick={() => onSubmit({ name: 'Test Template', description: '', category: 'custom', is_public: false })}>
          {submitButtonText || 'Submit'}
        </button>
        <button data-testid="close-btn" onClick={onClose}>
          Cancel
        </button>
      </div>
    );
  },
}));

import { SaveAsTemplateDialog } from '@/client/components/drawing/SaveAsTemplateDialog';
import apiClient from '@/client/lib/api';

describe('SaveAsTemplateDialog Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  });

  it('does not render when isOpen is false', () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={false}
        onClose={vi.fn()}
      />
    );
    expect(screen.queryByTestId('form-modal')).toBeNull();
  });

  it('renders Save as Template title when open', () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('Save as Template')).toBeDefined();
  });

  it('renders Template Name field', () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('Template Name')).toBeDefined();
  });

  it('renders Description field', () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByText('Description')).toBeDefined();
  });

  it('renders Save Template submit button text', () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
      />
    );
    expect(screen.getByTestId('submit-btn').textContent).toBe('Save Template');
  });

  it('calls apiClient.post on form submission', async () => {
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-99"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    const submitBtn = screen.getByTestId('submit-btn');
    submitBtn.click();

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/v1/templates',
        expect.objectContaining({ drawing_id: 'drawing-99' })
      );
    });
  });

  it('calls onSuccess callback after successful submission', async () => {
    const onSuccess = vi.fn();
    render(
      <SaveAsTemplateDialog
        drawingId="drawing-1"
        drawingName="My Drawing"
        isOpen={true}
        onClose={vi.fn()}
        onSuccess={onSuccess}
      />
    );

    const submitBtn = screen.getByTestId('submit-btn');
    submitBtn.click();

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });
});
