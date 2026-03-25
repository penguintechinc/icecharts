/**
 * Elder Import Dialog Component
 *
 * Modal dialog for connecting to Elder instance, browsing entities,
 * selecting them, and importing into IceCharts drawing.
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useElderImport } from '../../hooks/useElderImport';

interface ElderImportDialogProps {
  drawingId: string;
  isOpen: boolean;
  onClose: () => void;
  onImport: (nodes: unknown[], connectors: unknown[]) => void;
}

type DialogStep = 'connect' | 'browse' | 'select' | 'preview' | 'importing' | 'success';

const ElderImportDialog: React.FC<ElderImportDialogProps> = ({
  drawingId,
  isOpen,
  onClose,
  onImport,
}) => {
  // State management
  const [step, setStep] = useState<DialogStep>('connect');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [orgId, setOrgId] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [includeDependencies, setIncludeDependencies] = useState(true);

  // Elder import hook
  const {
    isLoading,
    error,
    entities,
    selectedEntities,
    validateConnection,
    fetchEntities,
    toggleEntitySelection,
    toggleSelectAll,
    importEntities,
    reset,
  } = useElderImport();

  // Reset dialog state when opening
  useEffect(() => {
    if (isOpen && step === 'connect') {
      reset();
    }
  }, [isOpen, reset]);

  // Handle connection
  const handleConnect = useCallback(async () => {
    if (!baseUrl.trim() || !apiKey.trim() || !orgId.trim()) {
      alert('Please fill in all connection details');
      return;
    }

    const isValid = await validateConnection(
      baseUrl,
      apiKey
    );

    if (isValid) {
      setStep('browse');
      // Fetch initial entities
      await fetchEntities(baseUrl, apiKey, parseInt(orgId, 10), entityTypeFilter);
    }
  }, [baseUrl, apiKey, orgId, entityTypeFilter, validateConnection, fetchEntities]);

  // Handle entity type filter change
  const handleFilterChange = useCallback(async () => {
    if (!baseUrl || !apiKey || !orgId) return;
    await fetchEntities(
      baseUrl,
      apiKey,
      parseInt(orgId, 10),
      entityTypeFilter
    );
  }, [baseUrl, apiKey, orgId, entityTypeFilter, fetchEntities]);

  // Handle import
  const handleImport = useCallback(async () => {
    if (selectedEntities.size === 0) {
      alert('Please select at least one entity');
      return;
    }

    setStep('importing');
    const result = await importEntities(
      drawingId,
      includeDependencies,
      1600,
      900
    );

    if (result) {
      setStep('success');
      // Auto-close after 2 seconds
      setTimeout(() => {
        onImport(result.nodes, result.connectors);
        onClose();
      }, 2000);
    } else {
      setStep('select');
    }
  }, [selectedEntities, drawingId, includeDependencies, importEntities, onImport, onClose]);

  // Entity type options
  const entityTypes = [
    { value: '', label: 'All Types' },
    { value: 'compute', label: 'Compute' },
    { value: 'vpc', label: 'VPC' },
    { value: 'subnet', label: 'Subnet' },
    { value: 'datacenter', label: 'Datacenter' },
    { value: 'network', label: 'Network Device' },
    { value: 'user', label: 'User' },
    { value: 'security_issue', label: 'Security Issue' },
  ];

  if (!isOpen) return null;

  return (
    <div className="elder-import-dialog-overlay">
      <div className="elder-import-dialog">
        <div className="elder-dialog-header">
          <h2>Import from Elder</h2>
          <button
            className="elder-dialog-close"
            onClick={onClose}
            disabled={isLoading}
          >
            ×
          </button>
        </div>

        <div className="elder-dialog-content">
          {/* Connection Step */}
          {step === 'connect' && (
            <div className="elder-step">
              <h3>Connect to Elder Instance</h3>
              <form onSubmit={(e) => { e.preventDefault(); handleConnect(); }}>
                <div className="elder-form-group">
                  <label htmlFor="elder-base-url">Elder Base URL</label>
                  <input
                    id="elder-base-url"
                    type="url"
                    placeholder="https://elder.example.com"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    disabled={isLoading}
                    className="elder-input"
                  />
                </div>

                <div className="elder-form-group">
                  <label htmlFor="elder-api-key">API Key</label>
                  <input
                    id="elder-api-key"
                    type="password"
                    placeholder="Enter your Elder API key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    disabled={isLoading}
                    className="elder-input"
                  />
                </div>

                <div className="elder-form-group">
                  <label htmlFor="elder-org-id">Organization ID</label>
                  <input
                    id="elder-org-id"
                    type="number"
                    placeholder="Organization ID"
                    value={orgId}
                    onChange={(e) => setOrgId(e.target.value)}
                    disabled={isLoading}
                    className="elder-input"
                  />
                </div>

                {error && (
                  <div className="elder-error-message">{error}</div>
                )}

                <button
                  type="submit"
                  className="elder-button elder-button-primary"
                  disabled={isLoading}
                >
                  {isLoading ? 'Connecting...' : 'Connect'}
                </button>
              </form>
            </div>
          )}

          {/* Browse/Select Step */}
          {(step === 'browse' || step === 'select') && (
            <div className="elder-step">
              <h3>Select Entities to Import</h3>

              <div className="elder-filter-group">
                <label htmlFor="entity-type-filter">Filter by Type</label>
                <div className="elder-filter-row">
                  <select
                    id="entity-type-filter"
                    value={entityTypeFilter}
                    onChange={(e) => setEntityTypeFilter(e.target.value)}
                    className="elder-select"
                    disabled={isLoading}
                  >
                    {entityTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleFilterChange}
                    className="elder-button elder-button-secondary"
                    disabled={isLoading}
                  >
                    Apply Filter
                  </button>
                </div>
              </div>

              <div className="elder-entity-list-header">
                <div className="elder-select-all">
                  <input
                    type="checkbox"
                    id="select-all-checkbox"
                    checked={selectedEntities.size === entities.length && entities.length > 0}
                    onChange={toggleSelectAll}
                    disabled={isLoading || entities.length === 0}
                  />
                  <label htmlFor="select-all-checkbox">
                    Select All ({selectedEntities.size}/{entities.length})
                  </label>
                </div>
              </div>

              <div className="elder-entity-list">
                {isLoading ? (
                  <div className="elder-loading">Loading entities...</div>
                ) : entities.length === 0 ? (
                  <div className="elder-empty">No entities found</div>
                ) : (
                  entities.map((entity) => (
                    <div
                      key={entity.id}
                      className={`elder-entity-item ${selectedEntities.has(entity.id) ? 'selected' : ''}`}
                    >
                      <input
                        type="checkbox"
                        id={`entity-${entity.id}`}
                        checked={selectedEntities.has(entity.id)}
                        onChange={() => toggleEntitySelection(entity.id)}
                      />
                      <label htmlFor={`entity-${entity.id}`} className="elder-entity-label">
                        <div className="elder-entity-name">{entity.name}</div>
                        <div className="elder-entity-type">{entity.entity_type}</div>
                        {entity.description && (
                          <div className="elder-entity-description">{entity.description}</div>
                        )}
                      </label>
                    </div>
                  ))
                )}
              </div>

              {error && (
                <div className="elder-error-message">{error}</div>
              )}

              <div className="elder-checkbox-group">
                <input
                  type="checkbox"
                  id="include-dependencies"
                  checked={includeDependencies}
                  onChange={(e) => setIncludeDependencies(e.target.checked)}
                />
                <label htmlFor="include-dependencies">
                  Include relationships/dependencies
                </label>
              </div>

              <div className="elder-dialog-actions">
                <button
                  onClick={() => setStep('connect')}
                  className="elder-button elder-button-secondary"
                  disabled={isLoading}
                >
                  Back
                </button>
                <button
                  onClick={handleImport}
                  className="elder-button elder-button-primary"
                  disabled={isLoading || selectedEntities.size === 0}
                >
                  {isLoading ? 'Importing...' : `Import (${selectedEntities.size})`}
                </button>
              </div>
            </div>
          )}

          {/* Importing Step */}
          {step === 'importing' && (
            <div className="elder-step">
              <div className="elder-loading-container">
                <div className="elder-spinner"></div>
                <p>Importing entities and relationships...</p>
              </div>
            </div>
          )}

          {/* Success Step */}
          {step === 'success' && (
            <div className="elder-step">
              <div className="elder-success-container">
                <div className="elder-success-icon">✓</div>
                <p className="elder-success-title">Import Successful!</p>
                <p className="elder-success-message">
                  {selectedEntities.size} entities and relationships have been imported
                </p>
                <p className="elder-success-note">Closing dialog...</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .elder-import-dialog-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .elder-import-dialog {
          background: white;
          border-radius: 8px;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          width: 90%;
          max-width: 600px;
          max-height: 80vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .elder-dialog-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 20px;
          border-bottom: 1px solid #e5e7eb;
        }

        .elder-dialog-header h2 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
        }

        .elder-dialog-close {
          background: none;
          border: none;
          font-size: 28px;
          cursor: pointer;
          color: #6b7280;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .elder-dialog-close:hover {
          color: #1f2937;
        }

        .elder-dialog-close:disabled {
          cursor: not-allowed;
          opacity: 0.5;
        }

        .elder-dialog-content {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
        }

        .elder-step {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .elder-step h3 {
          margin: 0 0 12px 0;
          font-size: 16px;
          font-weight: 600;
          color: #1f2937;
        }

        .elder-form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .elder-form-group label {
          font-size: 13px;
          font-weight: 600;
          color: #374151;
        }

        .elder-input,
        .elder-select {
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
          font-family: inherit;
        }

        .elder-input:focus,
        .elder-select:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .elder-input:disabled,
        .elder-select:disabled {
          background-color: #f3f4f6;
          cursor: not-allowed;
          color: #9ca3af;
        }

        .elder-filter-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .elder-filter-row {
          display: flex;
          gap: 8px;
          align-items: flex-end;
        }

        .elder-filter-row .elder-select {
          flex: 1;
        }

        .elder-entity-list-header {
          padding: 8px;
          background-color: #f9fafb;
          border-radius: 6px;
        }

        .elder-select-all {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .elder-select-all input[type="checkbox"] {
          cursor: pointer;
          width: 18px;
          height: 18px;
        }

        .elder-select-all label {
          margin: 0;
          cursor: pointer;
          font-weight: 600;
          color: #374151;
          font-size: 13px;
        }

        .elder-entity-list {
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          max-height: 300px;
          overflow-y: auto;
          background-color: #fafbfc;
        }

        .elder-entity-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px;
          border-bottom: 1px solid #e5e7eb;
          cursor: pointer;
          transition: background-color 0.15s;
        }

        .elder-entity-item:last-child {
          border-bottom: none;
        }

        .elder-entity-item:hover {
          background-color: #f3f4f6;
        }

        .elder-entity-item.selected {
          background-color: #dbeafe;
        }

        .elder-entity-item input[type="checkbox"] {
          width: 18px;
          height: 18px;
          margin-top: 2px;
          flex-shrink: 0;
          cursor: pointer;
        }

        .elder-entity-label {
          flex: 1;
          cursor: pointer;
          margin: 0;
        }

        .elder-entity-name {
          font-weight: 600;
          color: #1f2937;
          font-size: 13px;
        }

        .elder-entity-type {
          font-size: 12px;
          color: #6b7280;
          margin-top: 2px;
        }

        .elder-entity-description {
          font-size: 12px;
          color: #9ca3af;
          margin-top: 4px;
          font-style: italic;
        }

        .elder-loading,
        .elder-empty {
          padding: 40px;
          text-align: center;
          color: #6b7280;
          font-size: 14px;
        }

        .elder-checkbox-group {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 12px;
        }

        .elder-checkbox-group input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }

        .elder-checkbox-group label {
          margin: 0;
          cursor: pointer;
          font-size: 13px;
          color: #374151;
        }

        .elder-error-message {
          padding: 12px;
          background-color: #fee2e2;
          color: #991b1b;
          border-radius: 6px;
          font-size: 13px;
          border-left: 3px solid #dc2626;
        }

        .elder-loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          padding: 60px 20px;
        }

        .elder-spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #e5e7eb;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .elder-loading-container p {
          color: #6b7280;
          font-size: 14px;
          margin: 0;
        }

        .elder-dialog-actions {
          display: flex;
          gap: 8px;
          justify-content: flex-end;
          margin-top: 16px;
          padding-top: 12px;
          border-top: 1px solid #e5e7eb;
        }

        .elder-button {
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 600;
          border: none;
          cursor: pointer;
          transition: all 0.2s;
        }

        .elder-button-primary {
          background-color: #3b82f6;
          color: white;
        }

        .elder-button-primary:hover:not(:disabled) {
          background-color: #2563eb;
        }

        .elder-button-secondary {
          background-color: #e5e7eb;
          color: #1f2937;
        }

        .elder-button-secondary:hover:not(:disabled) {
          background-color: #d1d5db;
        }

        .elder-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .elder-success-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 16px;
          padding: 40px 20px;
        }

        .elder-success-icon {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background-color: #d1fae5;
          color: #059669;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 32px;
          font-weight: bold;
        }

        .elder-success-title {
          font-size: 18px;
          font-weight: 600;
          color: #059669;
          margin: 0;
        }

        .elder-success-message {
          font-size: 14px;
          color: #374151;
          margin: 0;
          text-align: center;
        }

        .elder-success-note {
          font-size: 12px;
          color: #9ca3af;
          margin: 0;
          font-style: italic;
        }
      `}</style>
    </div>
  );
};

export default ElderImportDialog;
