# IceCharts Common UI Components

Comprehensive dark-themed UI component library for IceCharts with gold accents and enterprise-grade features.

## Color Scheme

- **Primary**: Gold/Amber (`ice-gold-400`, `#fbbf24`)
- **Background**: Slate (`slate-900`, `#0f172a`)
- **Surface**: Slate (`slate-800`, `#1e293b`)
- **Border**: Slate (`slate-700`, `#334155`)
- **Text**: Light Slate (`slate-100`, `#f1f5f9`)
- **Muted**: Slate (`slate-400`, `#94a3b8`)

## Form Components

### Button
Button component with multiple variants and sizes.

**Props:**
- `variant`: 'primary' | 'secondary' | 'danger' | 'ghost' (default: 'primary')
- `size`: 'sm' | 'md' | 'lg' (default: 'md')
- `isLoading`: boolean (default: false)
- `icon`: React.ReactNode
- `iconPosition`: 'left' | 'right' (default: 'left')
- `children`: React.ReactNode (required)

**Example:**
```tsx
import { Button } from '@/client/components/common';

<Button variant="primary" size="md" isLoading={false}>
  Click me
</Button>

<Button variant="ghost" icon="🔗" iconPosition="right">
  Share
</Button>
```

### Input
Text input with label, error state, and helper text.

**Props:**
- `label`: string
- `error`: string
- `helperText`: string
- `required`: boolean
- Plus all standard HTML input attributes

**Example:**
```tsx
<Input
  label="Email"
  type="email"
  placeholder="your@email.com"
  error={errors.email}
  required
/>
```

### Textarea
Multi-line text input with same styling as Input.

**Props:** Same as Input

### Select
Dropdown select with label and error states.

**Props:**
- `label`: string
- `error`: string
- `helperText`: string
- `options`: Array<{ value: string | number; label: string }> (required)
- `placeholder`: string
- Plus standard HTML select attributes

**Example:**
```tsx
<Select
  label="Category"
  options={[
    { value: 'personal', label: 'Personal' },
    { value: 'business', label: 'Business' },
  ]}
  placeholder="Select a category"
/>
```

### Checkbox
Checkbox with label and error state.

**Props:**
- `label`: string
- `error`: string
- Plus standard HTML input attributes

### Toggle
Toggle switch component.

**Props:**
- `label`: string
- `checked`: boolean
- `onChange`: (checked: boolean) => void
- `defaultChecked`: boolean

## Layout Components

### Card
Container component with optional title, subtitle, and actions.

**Props:**
- `title`: string
- `subtitle`: string
- `actions`: React.ReactNode
- `variant`: 'default' | 'elevated' (default: 'default')
- `padding`: 'sm' | 'md' | 'lg' (default: 'md')
- `children`: React.ReactNode (required)

**Example:**
```tsx
<Card title="Settings" subtitle="Manage your preferences">
  <p>Settings content</p>
</Card>
```

### Modal
Dialog modal with header, body, and footer.

**Props:**
- `isOpen`: boolean (required)
- `onClose`: () => void (required)
- `title`: string
- `children`: React.ReactNode (required)
- `footer`: React.ReactNode
- `size`: 'sm' | 'md' | 'lg' (default: 'md')
- `closeButton`: boolean (default: true)

**Features:**
- Escape key to close
- Focus trap
- Backdrop click to close
- Prevents body scroll when open

### Dropdown
Context menu or dropdown for user interactions.

**Props:**
- `trigger`: React.ReactNode (required)
- `items`: Array<DropdownItem> (required)
- `align`: 'left' | 'right' (default: 'left')

**DropdownItem:**
```tsx
interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  divider?: boolean;
  danger?: boolean;
}
```

**Example:**
```tsx
<Dropdown
  trigger={<button>Actions</button>}
  items={[
    { id: 'edit', label: 'Edit', onClick: handleEdit },
    { id: 'divider', label: '', divider: true, onClick: () => {} },
    { id: 'delete', label: 'Delete', danger: true, onClick: handleDelete },
  ]}
/>
```

## Display Components

### Avatar
User avatar with image or fallback initials.

**Props:**
- `src`: string
- `alt`: string
- `initials`: string
- `size`: 'sm' | 'md' | 'lg' | 'xl' (default: 'md')
- `onClick`: () => void

**Example:**
```tsx
<Avatar src="/avatar.jpg" alt="John" initials="JD" size="lg" />
<Avatar initials="JD" size="md" />
```

### Badge
Status badges with multiple variants.

**Props:**
- `variant`: 'default' | 'success' | 'warning' | 'error' | 'info' | 'admin' | 'maintainer' | 'viewer' (default: 'default')
- `size`: 'sm' | 'md' (default: 'sm')
- `icon`: React.ReactNode
- `children`: React.ReactNode (required)

**Example:**
```tsx
<Badge variant="success">Active</Badge>
<Badge variant="admin">Administrator</Badge>
```

### Spinner
Loading spinner with optional text.

**Props:**
- `size`: 'sm' | 'md' | 'lg' (default: 'md')
- `color`: 'gold' | 'slate' | 'white' (default: 'gold')
- `text`: string

**Example:**
```tsx
<Spinner size="lg" text="Loading..." color="gold" />
```

### Alert
Alert/notification banner with auto-dismiss option.

**Props:**
- `message`: string (required)
- `variant`: 'success' | 'warning' | 'error' | 'info' (default: 'info')
- `dismissible`: boolean (default: true)
- `icon`: React.ReactNode
- `onDismiss`: () => void
- `autoCloseDuration`: number (milliseconds)

**Example:**
```tsx
<Alert
  message="Changes saved successfully"
  variant="success"
  autoCloseDuration={3000}
/>
```

### Tooltip
Hover tooltip component.

**Props:**
- `content`: string (required)
- `children`: React.ReactNode (required)
- `position`: 'top' | 'bottom' | 'left' | 'right' (default: 'top')
- `delay`: number milliseconds (default: 200)

**Example:**
```tsx
<Tooltip content="Click to edit" position="right">
  <button>Edit</button>
</Tooltip>
```

## Feature-Specific Components

### DrawingCard
Card component for displaying drawing thumbnails with metadata and actions.

**Props:**
- `id`: string (required)
- `title`: string (required)
- `thumbnail`: string (image URL)
- `lastModified`: Date (required)
- `ownerName`: string (required)
- `ownerInitials`: string (required)
- `ownerAvatar`: string (image URL)
- `onEdit`: (id: string) => void
- `onDuplicate`: (id: string) => void
- `onDelete`: (id: string) => void
- `onShare`: (id: string) => void

**Features:**
- Responsive thumbnail
- Time-relative modified date
- Owner avatar and name
- Dropdown actions menu
- Hover effects

### DrawingGrid
Grid layout component for displaying multiple drawings.

**Props:**
- `drawings`: Drawing[] (required)
- `onEdit`: (id: string) => void
- `onDuplicate`: (id: string) => void
- `onDelete`: (id: string) => void
- `onShare`: (id: string) => void
- `isLoading`: boolean (default: false)
- `emptyMessage`: string
- `columns`: 2 | 3 | 4 | 5 (default: 3)

**Features:**
- Responsive grid layout
- Loading skeleton animation
- Empty state message
- Configurable column count

**Example:**
```tsx
<DrawingGrid
  drawings={drawings}
  columns={4}
  onEdit={handleEdit}
  onDelete={handleDelete}
  isLoading={isLoading}
/>
```

### GroupCard
Card component for displaying group information.

**Props:**
- `id`: string (required)
- `name`: string (required)
- `description`: string
- `memberCount`: number (required)
- `members`: GroupMember[] (up to 3 displayed)
- `createdDate`: Date (required)
- `onEdit`: (id: string) => void
- `onDelete`: (id: string) => void
- `onViewMembers`: (id: string) => void

**Features:**
- Group name and description
- Member avatars with stacked display
- Member count badge
- Creation date
- Action dropdown menu

## Usage Examples

### Complete Form Example
```tsx
import { useState } from 'react';
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Toggle,
  Modal,
  Alert,
} from '@/client/components/common';

function SettingsForm() {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    category: '',
    notifications: true,
  });

  const handleSubmit = () => {
    setIsOpen(false);
    // Handle form submission
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Edit Settings</Button>

      <Modal isOpen={isOpen} onClose={() => setIsOpen(false)} title="Settings">
        <Alert message="Changes will be saved immediately" variant="info" />

        <div className="space-y-4 mt-4">
          <Input
            label="Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />

          <Input
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          />

          <Select
            label="Category"
            options={[
              { value: 'personal', label: 'Personal' },
              { value: 'business', label: 'Business' },
            ]}
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value })}
          />

          <Toggle
            label="Enable Notifications"
            checked={formData.notifications}
            onChange={(checked) =>
              setFormData({ ...formData, notifications: checked })
            }
          />
        </div>

        <div className="flex gap-2 justify-end mt-6">
          <Button variant="secondary" onClick={() => setIsOpen(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            Save
          </Button>
        </div>
      </Modal>
    </>
  );
}
```

### Drawing Gallery Example
```tsx
import { DrawingGrid, Button } from '@/client/components/common';

function DrawingGallery() {
  const [drawings, setDrawings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDrawings().then((data) => {
      setDrawings(data);
      setIsLoading(false);
    });
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-ice-gold-400">My Drawings</h1>
        <Button variant="primary">Create New</Button>
      </div>

      <DrawingGrid
        drawings={drawings}
        isLoading={isLoading}
        columns={4}
        onEdit={(id) => navigate(`/drawings/${id}/edit`)}
        onDelete={(id) => handleDelete(id)}
      />
    </div>
  );
}
```

## Styling

All components use Tailwind CSS with custom color extensions:
- `ice-gold-{50-900}`: Primary gold/amber colors
- `ice-blue-{50-900}`: Optional blue accent colors
- `ice-navy-{50-900}`: Optional navy accent colors
- Standard Slate colors for backgrounds and borders

## Accessibility

All components include:
- Semantic HTML
- ARIA labels and roles where appropriate
- Keyboard navigation support
- Focus management (especially for modals)
- Color contrast compliance (WCAG AA)

## Icons

Components support custom icons (React nodes, Unicode, or SVG). Recommended icon libraries:
- Heroicons
- Feather Icons
- Custom SVG components

## Theme Customization

Colors are defined in `colors.ts` and can be easily modified:
```tsx
import { colors, getRoleColor, getStatusColor } from './colors';

const adminColor = getRoleColor('admin');
const successColor = getStatusColor('success');
```

## Component Status

| Component | Status | Features |
|-----------|--------|----------|
| Button | ✅ Complete | All variants, sizes, loading state |
| Input | ✅ Complete | Labels, errors, helpers |
| Textarea | ✅ Complete | Same as Input |
| Select | ✅ Complete | Options, placeholder |
| Checkbox | ✅ Complete | Labels, errors |
| Toggle | ✅ Complete | Controlled & uncontrolled |
| Card | ✅ Complete | Variants, padding options |
| Modal | ✅ Complete | Focus trap, backdrop click, escape |
| Dropdown | ✅ Complete | Multiple items, dividers, danger |
| Avatar | ✅ Complete | Image + fallback, sizes |
| Badge | ✅ Complete | Multiple variants |
| Spinner | ✅ Complete | Sizes, colors |
| Alert | ✅ Complete | Variants, auto-close, dismissible |
| Tooltip | ✅ Complete | Position options, delay |
| DrawingCard | ✅ Complete | Full metadata display |
| DrawingGrid | ✅ Complete | Responsive, loading state |
| GroupCard | ✅ Complete | Member avatars, actions |
