// Hook for managing drawing exports

import { useState, useCallback, useEffect, useRef } from 'react';
import apiClient from '../../lib/api';

interface ExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'json' | 'jpg';
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

interface ProgressState {
  percentage: number;
  status: 'processing' | 'completed' | 'failed';
}

export const useExport = () => {
  const [state, setState] = useState<ExportState>({
    loading: false,
    error: null,
    success: false,
  });
  const [exportProgress, setExportProgress] = useState<ProgressState | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const buildQueryParams = (_drawingId: string, options: ExportOptions): URLSearchParams => {
    const params = new URLSearchParams();
    params.append('format', options.format);

    if (options.format === 'png' || options.format === 'jpg') {
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

    return params;
  };

  const downloadFile = (blob: Blob, drawingId: string, format: string) => {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `drawing_${drawingId}.${format}`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  };

  const pollJobStatus = useCallback(
    async (jobId: string, drawingId: string) => {
      try {
        const response = await apiClient.get(`/v1/exports/${jobId}/status`);
        const { status, percentage } = response.data;

        setExportProgress({
          percentage: percentage || 0,
          status: status === 'completed' ? 'completed' : 'processing',
        });

        if (status === 'completed') {
          // Download the completed export
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }

          // Fetch and download the file
          try {
            const fileResponse = await apiClient.get(`/v1/exports/${jobId}/download`, {
              responseType: 'blob',
            });
            downloadFile(fileResponse.data, drawingId, 'png'); // Format will be determined by backend
            setState({ loading: false, error: null, success: true });
          } catch (downloadError) {
            const errorMessage =
              downloadError instanceof Error
                ? downloadError.message
                : 'Failed to download export';
            setState({ loading: false, error: errorMessage, success: false });
            setExportProgress({ percentage: 0, status: 'failed' });
          }
        } else if (status === 'failed') {
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          setState({
            loading: false,
            error: 'Export job failed',
            success: false,
          });
          setExportProgress({ percentage: 0, status: 'failed' });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to check export status';
        setState({ loading: false, error: errorMessage, success: false });
        setExportProgress({ percentage: 0, status: 'failed' });
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    },
    []
  );

  const exportDrawing = useCallback(
    async (drawingId: string, options: ExportOptions) => {
      setState({ loading: true, error: null, success: false });
      setExportProgress(null);

      try {
        const params = buildQueryParams(drawingId, options);

        // Call API
        const response = await apiClient.get(
          `/v1/drawings/${drawingId}/export/${options.format}?${params.toString()}`,
          { responseType: 'blob', validateStatus: (status) => status === 200 || status === 202 }
        );

        // Check if this is an async job (202 response)
        if (response.status === 202) {
          const jobData = response.data;

          // For 202 responses, the response body should contain jobId
          // Note: We need to parse the JSON response instead of blob
          let jobId: string;

          try {
            const text = await new Promise<string>((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = () => resolve(reader.result as string);
              reader.onerror = reject;
              reader.readAsText(jobData);
            });
            const parsedData = JSON.parse(text);
            jobId = parsedData.job_id;
          } catch {
            throw new Error('Invalid job response format');
          }

          setExportProgress({
            percentage: 0,
            status: 'processing',
          });

          // Start polling for job status
          pollingIntervalRef.current = setInterval(() => {
            pollJobStatus(jobId, drawingId);
          }, 2000); // Poll every 2 seconds

          return { jobId };
        } else {
          // Synchronous export (200 response)
          const blob = new Blob([response.data], {
            type: response.headers['content-type'] || 'application/octet-stream',
          });

          downloadFile(blob, drawingId, options.format);
          setState({ loading: false, error: null, success: true });
          return blob;
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to export drawing';
        setState({ loading: false, error: errorMessage, success: false });
        throw error;
      }
    },
    [pollJobStatus]
  );

  return {
    ...state,
    exportProgress,
    exportDrawing,
  };
};
