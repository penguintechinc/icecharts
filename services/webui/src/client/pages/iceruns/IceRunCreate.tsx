/**
 * IceRunCreate - Create new IceRun function
 *
 * Multi-step wizard:
 * - Step 1: Basic info (name, description, tags)
 * - Step 2: Runtime selection with logo icons
 * - Step 3: Package upload (drag-and-drop or file picker)
 * - Step 4: Configuration (entrypoint, handler, env vars)
 * - Step 5: Resource limits (memory, CPU, timeout sliders)
 * - Step 6: Webhook settings (optional)
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RuntimeSelector } from './components/RuntimeSelector';
import { PackageUpload } from './components/PackageUpload';

export const IceRunCreate: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    tags: [] as string[],
    runtime: '',
    entrypoint: '',
    handler: '',
    memory_limit_mb: 128,
    timeout_seconds: 60,
    cpu_limit: 0.5,
    env_vars: {} as Record<string, string>,
    webhook_enabled: false,
  });

  const handleNext = () => {
    setCurrentStep((prev) => Math.min(prev + 1, 6));
  };

  const handleBack = () => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    // TODO: Submit to API
    navigate('/iceruns');
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <h1 className="text-3xl font-bold text-white mb-6">Create New Function</h1>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-8">
          {[1, 2, 3, 4, 5, 6].map((step) => (
            <div key={step} className="flex items-center">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step <= currentStep ? 'bg-purple-600 text-white' : 'bg-ice-navy-700 text-ice-navy-400'
                }`}
              >
                {step}
              </div>
              {step < 6 && (
                <div className={`w-16 h-1 ${step < currentStep ? 'bg-purple-600' : 'bg-ice-navy-700'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Step Content */}
        <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
          {currentStep === 1 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white mb-4">Basic Information</h2>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Function Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="my-function"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  rows={3}
                  placeholder="Describe what this function does..."
                />
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div>
              <h2 className="text-xl font-semibold text-white mb-4">Select Runtime</h2>
              <RuntimeSelector
                value={formData.runtime}
                onChange={(runtime) => setFormData({ ...formData, runtime })}
              />
            </div>
          )}

          {currentStep === 3 && (
            <div>
              <h2 className="text-xl font-semibold text-white mb-4">Upload Package</h2>
              <PackageUpload onUpload={(data) => console.log('Uploaded:', data)} />
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white mb-4">Configuration</h2>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Entrypoint</label>
                <input
                  type="text"
                  value={formData.entrypoint}
                  onChange={(e) => setFormData({ ...formData, entrypoint: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="main.py"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Handler</label>
                <input
                  type="text"
                  value={formData.handler}
                  onChange={(e) => setFormData({ ...formData, handler: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="handler"
                />
              </div>
            </div>
          )}

          {currentStep === 5 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-white mb-4">Resource Limits</h2>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">
                  Memory: {formData.memory_limit_mb} MB
                </label>
                <input
                  type="range"
                  min="128"
                  max="4096"
                  step="128"
                  value={formData.memory_limit_mb}
                  onChange={(e) => setFormData({ ...formData, memory_limit_mb: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">
                  Timeout: {formData.timeout_seconds} seconds
                </label>
                <input
                  type="range"
                  min="1"
                  max="900"
                  value={formData.timeout_seconds}
                  onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">
                  CPU: {formData.cpu_limit} cores
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="4.0"
                  step="0.1"
                  value={formData.cpu_limit}
                  onChange={(e) => setFormData({ ...formData, cpu_limit: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>
            </div>
          )}

          {currentStep === 6 && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-white mb-4">Webhook Settings (Optional)</h2>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.webhook_enabled}
                  onChange={(e) => setFormData({ ...formData, webhook_enabled: e.target.checked })}
                  className="form-checkbox h-5 w-5 text-purple-600"
                />
                <span className="text-white">Enable webhook trigger</span>
              </label>
            </div>
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className="px-6 py-2 bg-ice-navy-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>
          <div className="space-x-4">
            <button
              onClick={() => navigate('/iceruns')}
              className="px-6 py-2 bg-ice-navy-700 text-white rounded-lg"
            >
              Cancel
            </button>
            {currentStep < 6 ? (
              <button
                onClick={handleNext}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
              >
                Create Function
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default IceRunCreate;
