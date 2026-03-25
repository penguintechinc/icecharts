/**
 * PackageUpload - Drag-and-drop package upload component
 */

import React, { useCallback, useState } from 'react';

interface PackageUploadProps {
  onUpload: (data: { file: File; size: number; hash: string }) => void;
}

export const PackageUpload: React.FC<PackageUploadProps> = ({ onUpload }) => {
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      onUpload({
        file: droppedFile,
        size: droppedFile.size,
        hash: 'temp-hash', // TODO: Calculate SHA256
      });
    }
  }, [onUpload]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      onUpload({
        file: selectedFile,
        size: selectedFile.size,
        hash: 'temp-hash',
      });
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
        dragging
          ? 'border-purple-500 bg-purple-500/10'
          : 'border-ice-navy-600 hover:border-ice-navy-500'
      }`}
    >
      {file ? (
        <div>
          <p className="text-white font-medium mb-2">{file.name}</p>
          <p className="text-ice-navy-400 text-sm">
            {(file.size / 1024).toFixed(2)} KB
          </p>
          <button
            onClick={() => setFile(null)}
            className="mt-4 text-red-400 hover:text-red-300"
          >
            Remove
          </button>
        </div>
      ) : (
        <div>
          <svg
            className="mx-auto h-12 w-12 text-ice-navy-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="mt-4 text-white">
            Drag and drop your package here, or{' '}
            <label className="text-purple-400 hover:text-purple-300 cursor-pointer">
              browse
              <input
                type="file"
                className="hidden"
                accept=".zip,.tar.gz,.py,.js,.go,.rb,.sh,.ps1,.rs"
                onChange={handleFileSelect}
              />
            </label>
          </p>
          <p className="mt-2 text-sm text-ice-navy-400">
            Supports: .zip, .tar.gz, .py, .js, .go, .rb, .sh, .ps1, .rs
          </p>
        </div>
      )}
    </div>
  );
};
