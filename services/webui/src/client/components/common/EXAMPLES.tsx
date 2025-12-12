/**
 * Component Usage Examples
 *
 * This file contains practical examples of how to use each component
 * in the IceCharts common component library.
 */

import { useState } from 'react';
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Toggle,
  Card,
  Modal,
  Dropdown,
  Avatar,
  Badge,
  Spinner,
  Alert,
  Tooltip,
  DrawingCard,
  DrawingGrid,
  GroupCard,
} from './index';

// ============================================================================
// Form Components Examples
// ============================================================================

export function ButtonExamples() {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Button Examples</h2>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">Primary Buttons</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" size="sm">
            Small
          </Button>
          <Button variant="primary" size="md">
            Medium
          </Button>
          <Button variant="primary" size="lg">
            Large
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">Secondary Buttons</h3>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Delete</Button>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">With Icons</h3>
        <div className="flex flex-wrap gap-2">
          <Button icon="➕" iconPosition="left">
            Add New
          </Button>
          <Button icon="🔗" iconPosition="right" variant="ghost">
            Share
          </Button>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">Loading State</h3>
        <Button isLoading>Save Changes</Button>
      </div>
    </div>
  );
}

export function FormExamples() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    description: '',
    category: '',
    subscribe: false,
    notifications: true,
  });

  return (
    <Card title="Contact Form" className="max-w-md">
      <div className="space-y-4">
        <Input
          label="Full Name"
          placeholder="John Doe"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          required
        />

        <Input
          label="Email"
          type="email"
          placeholder="john@example.com"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
        />

        <Select
          label="Category"
          options={[
            { value: 'support', label: 'Support Request' },
            { value: 'feedback', label: 'Feedback' },
            { value: 'other', label: 'Other' },
          ]}
          value={formData.category}
          onChange={(e) => setFormData({ ...formData, category: e.target.value })}
          placeholder="Select a category"
        />

        <Textarea
          label="Message"
          placeholder="Your message here..."
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={4}
        />

        <Checkbox
          label="Subscribe to updates"
          checked={formData.subscribe}
          onChange={(e) => setFormData({ ...formData, subscribe: e.target.checked })}
        />

        <Toggle
          label="Enable notifications"
          checked={formData.notifications}
          onChange={(checked) => setFormData({ ...formData, notifications: checked })}
        />

        <div className="flex gap-2">
          <Button variant="primary">Submit</Button>
          <Button variant="secondary">Cancel</Button>
        </div>
      </div>
    </Card>
  );
}

// ============================================================================
// Layout Components Examples
// ============================================================================

export function ModalExample() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open Modal</Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Action"
        size="md"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={() => setIsOpen(false)}>
              Delete
            </Button>
          </>
        }
      >
        <p className="text-slate-300">
          Are you sure you want to delete this item? This action cannot be undone.
        </p>
      </Modal>
    </>
  );
}

export function DropdownExample() {
  return (
    <Dropdown
      trigger={<Button variant="ghost">Actions</Button>}
      items={[
        { id: 'edit', label: 'Edit', icon: '✏️', onClick: () => console.log('edit') },
        { id: 'duplicate', label: 'Duplicate', icon: '📋', onClick: () => console.log('duplicate') },
        { id: 'divider', label: '', divider: true, onClick: () => {} },
        { id: 'delete', label: 'Delete', icon: '🗑️', danger: true, onClick: () => console.log('delete') },
      ]}
    />
  );
}

// ============================================================================
// Display Components Examples
// ============================================================================

export function AvatarExamples() {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Avatar Examples</h2>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">With Image</h3>
        <div className="flex gap-4">
          <Avatar
            src="https://ui-avatars.com/api/?name=John+Doe"
            alt="John Doe"
            size="sm"
          />
          <Avatar
            src="https://ui-avatars.com/api/?name=Jane+Smith"
            alt="Jane Smith"
            size="md"
          />
          <Avatar
            src="https://ui-avatars.com/api/?name=Bob+Johnson"
            alt="Bob Johnson"
            size="lg"
          />
          <Avatar
            src="https://ui-avatars.com/api/?name=Alice+Brown"
            alt="Alice Brown"
            size="xl"
          />
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">With Initials</h3>
        <div className="flex gap-4">
          <Avatar initials="JD" size="sm" />
          <Avatar initials="JS" size="md" />
          <Avatar initials="BJ" size="lg" />
          <Avatar initials="AB" size="xl" />
        </div>
      </div>
    </div>
  );
}

export function BadgeExamples() {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Badge Examples</h2>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">Status Badges</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="success">Active</Badge>
          <Badge variant="warning">Pending</Badge>
          <Badge variant="error">Failed</Badge>
          <Badge variant="info">Information</Badge>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">Role Badges</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="admin">Administrator</Badge>
          <Badge variant="maintainer">Maintainer</Badge>
          <Badge variant="viewer">Viewer</Badge>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-slate-300">With Icons</h3>
        <div className="flex flex-wrap gap-2">
          <Badge variant="success" icon="✅">
            Completed
          </Badge>
          <Badge variant="error" icon="❌">
            Error
          </Badge>
        </div>
      </div>
    </div>
  );
}

export function AlertExamples() {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Alert Examples</h2>

      <Alert message="This is a success message" variant="success" />
      <Alert message="This is a warning message" variant="warning" />
      <Alert message="This is an error message" variant="error" />
      <Alert message="This is an info message" variant="info" />
    </div>
  );
}

export function SpinnerExamples() {
  return (
    <div className="space-y-8 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Spinner Examples</h2>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-300">Sizes</h3>
        <div className="flex gap-8">
          <Spinner size="sm" />
          <Spinner size="md" />
          <Spinner size="lg" />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-300">Colors</h3>
        <div className="flex gap-8">
          <Spinner color="gold" />
          <Spinner color="slate" />
          <Spinner color="white" />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-slate-300">With Text</h3>
        <Spinner size="md" text="Loading your data..." />
      </div>
    </div>
  );
}

export function TooltipExamples() {
  return (
    <div className="space-y-4 p-4">
      <h2 className="text-xl font-bold text-ice-gold-400">Tooltip Examples</h2>

      <div className="flex flex-wrap gap-12">
        <Tooltip content="This is a top tooltip" position="top">
          <Button>Top</Button>
        </Tooltip>

        <Tooltip content="This is a bottom tooltip" position="bottom">
          <Button>Bottom</Button>
        </Tooltip>

        <Tooltip content="This is a left tooltip" position="left">
          <Button>Left</Button>
        </Tooltip>

        <Tooltip content="This is a right tooltip" position="right">
          <Button>Right</Button>
        </Tooltip>
      </div>
    </div>
  );
}

// ============================================================================
// Feature-Specific Components Examples
// ============================================================================

export function DrawingCardExample() {
  return (
    <div className="max-w-sm">
      <DrawingCard
        id="1"
        title="Q4 Financial Report"
        lastModified={new Date(Date.now() - 3600000)}
        ownerName="John Doe"
        ownerInitials="JD"
        thumbnail="https://ui-avatars.com/api/?name=Chart&background=fbbf24&color=000"
        onEdit={() => console.log('edit')}
        onDuplicate={() => console.log('duplicate')}
        onDelete={() => console.log('delete')}
        onShare={() => console.log('share')}
      />
    </div>
  );
}

export function DrawingGridExample() {
  const drawings = [
    {
      id: '1',
      title: 'Q4 Financial Report',
      lastModified: new Date(Date.now() - 3600000),
      ownerName: 'John Doe',
      ownerInitials: 'JD',
    },
    {
      id: '2',
      title: 'Marketing Dashboard',
      lastModified: new Date(Date.now() - 86400000),
      ownerName: 'Jane Smith',
      ownerInitials: 'JS',
    },
    {
      id: '3',
      title: 'Sales Metrics',
      lastModified: new Date(Date.now() - 604800000),
      ownerName: 'Bob Johnson',
      ownerInitials: 'BJ',
    },
  ];

  return (
    <DrawingGrid
      drawings={drawings}
      columns={3}
      onEdit={() => {}}
      onDelete={() => {}}
    />
  );
}

export function GroupCardExample() {
  return (
    <div className="max-w-md">
      <GroupCard
        id="1"
        name="Design Team"
        description="Core design and UX team members"
        memberCount={8}
        members={[
          { name: 'Alice Brown', initials: 'AB' },
          { name: 'Charlie Davis', initials: 'CD' },
          { name: 'Emma Wilson', initials: 'EW' },
        ]}
        createdDate={new Date('2024-01-15')}
        onEdit={() => console.log('edit')}
        onDelete={() => console.log('delete')}
        onViewMembers={() => console.log('view members')}
      />
    </div>
  );
}

// ============================================================================
// Complete Page Example
// ============================================================================

export function ComponentShowcase() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-ice-gold-400 mb-12">
          IceCharts Component Library
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <section>
            <h2 className="text-2xl font-bold text-ice-gold-400 mb-4">Forms</h2>
            <div className="space-y-6">
              <ButtonExamples />
              <FormExamples />
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-ice-gold-400 mb-4">Modals</h2>
            <Card>
              <ModalExample />
              <DropdownExample />
            </Card>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-ice-gold-400 mb-4">Display</h2>
            <div className="space-y-6">
              <AvatarExamples />
              <BadgeExamples />
              <AlertExamples />
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-ice-gold-400 mb-4">Feedback</h2>
            <div className="space-y-6">
              <SpinnerExamples />
              <TooltipExamples />
            </div>
          </section>

          <section className="lg:col-span-2">
            <h2 className="text-2xl font-bold text-ice-gold-400 mb-4">Features</h2>
            <div className="space-y-6">
              <DrawingCardExample />
              <DrawingGridExample />
              <GroupCardExample />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
