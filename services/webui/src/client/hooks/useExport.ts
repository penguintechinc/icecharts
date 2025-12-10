"""Hook for managing drawing exports."""

import { useState, useCallback } from 'react';
import apiClient from '../../lib/api';

interface ExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'json';
  width?: number;
  height?: number;
  quality?: number;
  pageSize?: string;
  includeBackground?: boolean;
}

interface ExportState {
  loading: boolean;
  error: string | null;
  success: boolean;
}

export const useExport = () => {
  const [state, setState] = useState<ExportState>({
    loading: false,
    error: null,
    success: false,
  });

  const exportDrawing = useCallback(
    async (drawingId: string, options: ExportOptions) => {
      setState({ loading: true, error: null, success: false });

      try {
        // Build query parameters
        const params = new URLSearchParams();
        params.append('format', options.format);

        if (options.format === 'png') {
          if (options.width) params.append('width', options.width.toString());
          if (options.height) params.append('height', options.height.toString());
          if (options.quality) params.append('quality', options.quality.toString());
          if (options.includeBackground !== undefined) {
            params.append('include_background', options.includeBackground ? 'true' : 'false');
          }
        }

        if (options.format === 'pdf') {
          if (options.pageSize) params.append('page_size', options.pageSize);
          if (options.includeBackground !== undefined) {
            params.append('include_background', options.includeBackground ? 'true' : 'false');
          }
        }

        // Call API
        const response = await apiClient.get(
          `/v1/drawings/${drawingId}/export/${options.format}`,
          { responseType: 'blob' }
        );

        // Create blob and download
        const blob = new Blob([response.data], {
          type: response.headers['content-type'] || 'application/octet-stream',
        });

        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;

        // Set filename
        const ext = options.format;
        link.download = `drawing_${drawingId}.${ext}`;

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        setState({ loading: false, error: null, success: true });
        return blob;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to export drawing';
        setState({ loading: false, error: errorMessage, success: false });
        throw error;
      }
    },
    []
  );

  return {
    ...state,
    exportDrawing,
  };
};
