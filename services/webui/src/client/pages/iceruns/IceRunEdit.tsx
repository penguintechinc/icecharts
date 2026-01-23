/**
 * IceRunEdit - Edit existing IceRun function
 * Reuses the same wizard structure as IceRunCreate
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { RuntimeSelector } from './components/RuntimeSelector';
// PackageUpload will be used when upload functionality is implemented
// import { PackageUpload } from './components/PackageUpload';

export const IceRunEdit: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [_currentStep, _setCurrentStep] = useState(1);
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

  useEffect(() => {
    // TODO: Fetch function data from API
    setLoading(false);
  }, [id]);

  const handleSave = async () => {
    // TODO: Update via API
    navigate(`/iceruns/${id}`);
  };

  if (loading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-6">Edit Function</h1>

        {/* Simplified single-page edit form */}
        <div className="bg-ice-navy-800 rounded-lg p-6 space-y-6">
          <div>
            <label className="block text-sm font-medium text-ice-navy-300 mb-2">Function Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ice-navy-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ice-navy-300 mb-2">Runtime</label>
            <RuntimeSelector
              value={formData.runtime}
              onChange={(runtime) => setFormData({ ...formData, runtime })}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ice-navy-300 mb-2">Entrypoint</label>
              <input
                type="text"
                value={formData.entrypoint}
                onChange={(e) => setFormData({ ...formData, entrypoint: e.target.value })}
                className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-ice-navy-300 mb-2">Handler</label>
              <input
                type="text"
                value={formData.handler}
                onChange={(e) => setFormData({ ...formData, handler: e.target.value })}
                className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-4 mt-6">
          <button
            onClick={() => navigate(`/iceruns/${id}`)}
            className="px-6 py-2 bg-ice-navy-700 text-white rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default IceRunEdit;
