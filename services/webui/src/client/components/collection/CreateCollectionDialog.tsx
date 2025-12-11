import React, { useState } from 'react';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Textarea from '../common/Textarea';
import Select from '../common/Select';
import Button from '../common/Button';
import apiClient from '../../lib/api';

interface CreateCollectionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (collectionId: string) => void;
}

type ShareMode = 'private' | 'link_only' | 'registered_users';

interface CollectionFormData {
  name: string;
  description: string;
  share_mode: ShareMode;
}

interface ValidationErrors {
  name?: string;
  description?: string;
  share_mode?: string;
}

export default function CreateCollectionDialog({
  isOpen,
  onClose,
  onSuccess,
}: CreateCollectionDialogProps) {
  const [formData, setFormData] = useState<CollectionFormData>({
    name: '',
    description: '',
    share_mode: 'private',
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const validateForm = (): boolean => {
    const newErrors: ValidationErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Collection name is required';
    } else if (formData.name.trim().length > 255) {
      newErrors.name = 'Collection name must be 255 characters or less';
    }

    if (formData.description.trim().length > 1000) {
      newErrors.description = 'Description must be 1000 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (
    field: keyof CollectionFormData,
    value: string
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleCreate = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setApiError(null);

    try {
      const response = await apiClient.post('/collections', {
        name: formData.name.trim(),
        description: formData.description.trim(),
        share_mode: formData.share_mode,
      });

      const { id } = response.data;

      if (onSuccess) {
        onSuccess(id);
      }

      // Reset form and close
      setFormData({
        name: '',
        description: '',
        share_mode: 'private',
      });
      onClose();
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to create collection';
      setApiError(errorMessage);
      console.error('Create collection error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      share_mode: 'private',
    });
    setErrors({});
    setApiError(null);
    onClose();
  };

  const shareModeOptions = [
    {
      value: 'private',
      label: 'Private - Only you can access',
    },
    {
      value: 'link_only',
      label: 'Link Only - Anyone with link can view',
    },
    {
      value: 'registered_users',
      label: 'Registered Users - All users can view',
    },
  ];

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New Collection"
      size="md"
      footer={
        <>
          <Button
            variant="ghost"
            size="md"
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleCreate}
            disabled={loading || !formData.name.trim()}
            isLoading={loading}
          >
            Create Collection
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {apiError}
          </div>
        )}

        {/* Name Input */}
        <Input
          label="Collection Name"
          placeholder="e.g., Q1 Architecture Diagrams"
          value={formData.name}
          onChange={(e) => handleInputChange('name', e.target.value)}
          error={errors.name}
          required
          maxLength={255}
          disabled={loading}
        />

        {/* Description Input */}
        <Textarea
          label="Description (Optional)"
          placeholder="Add a description for this collection..."
          value={formData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          error={errors.description}
          helperText={`${formData.description.length}/1000`}
          maxLength={1000}
          disabled={loading}
          rows={3}
        />

        {/* Share Mode Selector */}
        <Select
          label="Share Mode"
          options={shareModeOptions}
          value={formData.share_mode}
          onChange={(e) => handleInputChange('share_mode', e.target.value)}
          error={errors.share_mode}
          disabled={loading}
          required
        />

        {/* Help text for share modes */}
        <p className="text-xs text-slate-400 mt-2">
          {formData.share_mode === 'private' &&
            'Only you can access this collection.'}
          {formData.share_mode === 'link_only' &&
            'Anyone with the share link can view this collection.'}
          {formData.share_mode === 'registered_users' &&
            'All registered users in the system can view this collection.'}
        </p>
      </div>
    </Modal>
  );
}
