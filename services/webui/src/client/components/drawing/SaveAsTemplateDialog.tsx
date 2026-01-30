import React from 'react';
import { FormModalBuilder } from '@penguin/react_libs';
import type { FormField } from '@penguin/react_libs';
import apiClient from '../../lib/api';

interface SaveAsTemplateDialogProps {
  drawingId: string;
  drawingName: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const SaveAsTemplateDialog: React.FC<SaveAsTemplateDialogProps> = ({
  drawingId,
  drawingName,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const fields: FormField[] = [
    {
      name: 'name',
      type: 'text',
      label: 'Template Name',
      placeholder: 'Enter template name',
      required: true,
      defaultValue: `${drawingName} Template`,
    },
    {
      name: 'description',
      type: 'textarea',
      label: 'Description',
      placeholder: 'Enter template description (optional)',
      rows: 3,
    },
    {
      name: 'category',
      type: 'text',
      label: 'Category',
      placeholder: 'e.g., custom, diagrams, etc.',
      defaultValue: 'custom',
    },
    {
      name: 'is_public',
      type: 'checkbox',
      label: 'Make template public (visible to other users)',
      defaultValue: false,
    },
  ];

  const handleSubmit = async (data: Record<string, unknown>) => {
    await apiClient.post('/v1/templates', {
      name: (data.name as string).trim(),
      description: ((data.description as string) || '').trim(),
      category: data.category,
      drawing_id: drawingId,
      is_public: data.is_public,
    });

    onSuccess?.();
  };

  return (
    <FormModalBuilder
      title="Save as Template"
      isOpen={isOpen}
      onClose={onClose}
      fields={fields}
      onSubmit={handleSubmit}
      submitButtonText="Save Template"
    />
  );
};
