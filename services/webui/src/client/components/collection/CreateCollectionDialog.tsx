import { FormModalBuilder } from '@penguin/react_libs';
import type { FormField } from '@penguin/react_libs';
import apiClient from '../../lib/api';

interface CreateCollectionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (collectionId: string) => void;
}

const fields: FormField[] = [
  {
    name: 'name',
    type: 'text',
    label: 'Collection Name',
    placeholder: 'e.g., Q1 Architecture Diagrams',
    required: true,
    helpText: 'Give your collection a descriptive name',
  },
  {
    name: 'description',
    type: 'textarea',
    label: 'Description (Optional)',
    placeholder: 'Add a description for this collection...',
    rows: 3,
  },
  {
    name: 'share_mode',
    type: 'select',
    label: 'Share Mode',
    required: true,
    defaultValue: 'private',
    options: [
      { value: 'private', label: 'Private - Only you can access' },
      { value: 'link_only', label: 'Link Only - Anyone with link can view' },
      { value: 'registered_users', label: 'Registered Users - All users can view' },
    ],
    helpText: 'Control who can access this collection',
  },
];

export default function CreateCollectionDialog({
  isOpen,
  onClose,
  onSuccess,
}: CreateCollectionDialogProps) {
  const handleSubmit = async (data: Record<string, unknown>) => {
    const response = await apiClient.post('/collections', {
      name: (data.name as string).trim(),
      description: ((data.description as string) || '').trim(),
      share_mode: data.share_mode,
    });

    const { id } = response.data;
    onSuccess?.(id);
  };

  return (
    <FormModalBuilder
      title="Create New Collection"
      isOpen={isOpen}
      onClose={onClose}
      fields={fields}
      onSubmit={handleSubmit}
      submitButtonText="Create Collection"
    />
  );
}
