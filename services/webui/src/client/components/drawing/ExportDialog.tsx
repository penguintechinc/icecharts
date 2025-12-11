import { useState, useEffect } from 'react';
import { useExport } from '../../hooks/useExport';

interface ExportDialogProps {
  drawingId: string;
  isOpen: boolean;
  onClose: () => void;
}

type ExportFormat = 'png' | 'svg' | 'pdf' | 'json' | 'jpg';

interface ExportConfig {
  format: ExportFormat;
  width: number;
  height: number;
  quality: number;
  pageSize: string;
  includeBackground: boolean;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  drawingId,
  isOpen,
  onClose,
}) => {
  const { loading, error, success, exportDrawing, exportProgress } = useExport();
  const [jobId, setJobId] = useState<string | null>(null);
  const [progressPercentage, setProgressPercentage] = useState<number>(0);

  const [config, setConfig] = useState<ExportConfig>({
    format: 'png',
    width: 800,
    height: 600,
    quality: 95,
    pageSize: 'A4',
    includeBackground: true,
  });

  // Reset state when dialog closes
  useEffect(() => {
    if (!isOpen) {
      setJobId(null);
      setProgressPercentage(0);
    }
  }, [isOpen]);

  const handleFormatChange = (format: ExportFormat) => {
    setConfig((prev) => ({ ...prev, format }));
  };

  const handleDimensionChange = (field: 'width' | 'height', value: number) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const handleQualityChange = (value: number) => {
    setConfig((prev) => ({ ...prev, quality: value }));
  };

  const handlePageSizeChange = (pageSize: string) => {
    setConfig((prev) => ({ ...prev, pageSize }));
  };

  const handleBackgroundToggle = () => {
    setConfig((prev) => ({ ...prev, includeBackground: !prev.includeBackground }));
  };

  const handleExport = async () => {
    try {
      const result = await exportDrawing(drawingId, {
        format: config.format,
        width: config.width,
        height: config.height,
        quality: config.quality,
        pageSize: config.pageSize,
        includeBackground: config.includeBackground,
      });

      // If result has jobId, track the async export
      if (result && typeof result === 'object' && 'jobId' in result) {
        setJobId(result.jobId as string);
      } else {
        // Synchronous export completed
        setTimeout(onClose, 500);
      }
    } catch (err) {
      // Error is handled by hook state
      console.error('Export failed:', err);
    }
  };

  // Track progress from exportProgress hook
  useEffect(() => {
    if (exportProgress) {
      setProgressPercentage(exportProgress.percentage || 0);

      // If export is complete, close dialog
      if (exportProgress.status === 'completed') {
        setTimeout(onClose, 1000);
      }
    }
  }, [exportProgress, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Export Drawing</h2>

        {/* Format Selection */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Format</h3>
          <div className="grid grid-cols-3 gap-2">
            {(['png', 'svg', 'pdf', 'json', 'jpg'] as ExportFormat[]).map((format) => (
              <button
                key={format}
                onClick={() => handleFormatChange(format)}
                className={`px-3 py-2 rounded border transition ${
                  config.format === format
                    ? 'bg-blue-500 text-white border-blue-600'
                    : 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200'
                }`}
              >
                {format.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* PNG-specific options */}
        {config.format === 'png' && (
          <div className="mb-6 space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Width</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={config.width}
                onChange={(e) => handleDimensionChange('width', parseInt(e.target.value))}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Height</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={config.height}
                onChange={(e) => handleDimensionChange('height', parseInt(e.target.value))}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Quality: {config.quality}%</label>
              <input
                type="range"
                min="1"
                max="100"
                value={config.quality}
                onChange={(e) => handleQualityChange(parseInt(e.target.value))}
                className="mt-1 w-full"
              />
            </div>
          </div>
        )}

        {/* JPG-specific options */}
        {config.format === 'jpg' && (
          <div className="mb-6 space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Width</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={config.width}
                onChange={(e) => handleDimensionChange('width', parseInt(e.target.value))}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Height</label>
              <input
                type="number"
                min="100"
                max="4000"
                value={config.height}
                onChange={(e) => handleDimensionChange('height', parseInt(e.target.value))}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700">Quality: {config.quality}%</label>
              <input
                type="range"
                min="1"
                max="100"
                value={config.quality}
                onChange={(e) => handleQualityChange(parseInt(e.target.value))}
                className="mt-1 w-full"
              />
            </div>
          </div>
        )}

        {/* PDF-specific options */}
        {config.format === 'pdf' && (
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-2">Page Size</label>
            <select
              value={config.pageSize}
              onChange={(e) => handlePageSizeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="A0">A0</option>
              <option value="A1">A1</option>
              <option value="A2">A2</option>
              <option value="A3">A3</option>
              <option value="A4">A4</option>
              <option value="A5">A5</option>
              <option value="A6">A6</option>
              <option value="Letter">Letter</option>
              <option value="Legal">Legal</option>
              <option value="Tabloid">Tabloid</option>
              <option value="Ledger">Ledger</option>
            </select>
          </div>
        )}

        {/* Background option (PNG/SVG only) */}
        {(config.format === 'png' || config.format === 'svg') && (
          <div className="mb-6 flex items-center group">
            <input
              type="checkbox"
              id="include-bg"
              checked={config.includeBackground}
              onChange={handleBackgroundToggle}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="include-bg" className="ml-2 text-sm text-gray-700 cursor-help relative">
              Include background
              <span className="invisible group-hover:visible absolute bottom-full left-0 mb-2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                Transparent background only available for PNG and SVG
              </span>
            </label>
          </div>
        )}

        {/* Error message */}
        {error && <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>}

        {/* Progress indicator for async exports */}
        {jobId && (
          <div className="mb-4 p-3 bg-blue-100 text-blue-700 rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Exporting...</span>
              <span className="text-sm">{progressPercentage}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Success message */}
        {success && !jobId && (
          <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">
            Export successful! Download started.
          </div>
        )}

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition disabled:opacity-50"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleExport}
            className="flex-1 px-4 py-2 text-white bg-blue-500 rounded hover:bg-blue-600 transition disabled:opacity-50 flex items-center justify-center gap-2"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="animate-spin">⏳</span>
                Exporting...
              </>
            ) : (
              'Download'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
