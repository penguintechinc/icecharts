# Component API Reference

Complete API documentation for all IceCharts common components.

## Table of Contents

- [Form Components](#form-components)
- [Layout Components](#layout-components)
- [Display Components](#display-components)
- [Feature Components](#feature-components)

---

## Form Components

### Button

Primary call-to-action component with multiple variants and sizes.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'danger' \| 'ghost'` | `'primary'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `isLoading` | `boolean` | `false` | Show loading state |
| `icon` | `React.ReactNode` | - | Icon to display |
| `iconPosition` | `'left' \| 'right'` | `'left'` | Icon placement |
| `disabled` | `boolean` | `false` | Disable button |
| `onClick` | `(e: React.MouseEvent) => void` | - | Click handler |
| `className` | `string` | `''` | Additional CSS classes |
| `children` | `React.ReactNode` | - | Button text (required) |

#### Example

```tsx
<Button
  variant="primary"
  size="md"
  icon="➕"
  onClick={() => console.log('clicked')}
>
  Add Item
</Button>
```

---

### Input

Text input field with validation support.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Field label |
| `error` | `string` | - | Error message |
| `helperText` | `string` | - | Helper text below input |
| `required` | `boolean` | `false` | Show required indicator |
| `type` | `string` | `'text'` | Input type (text, email, password, etc.) |
| `value` | `string` | - | Input value |
| `onChange` | `(e: React.ChangeEvent<HTMLInputElement>) => void` | - | Change handler |
| `placeholder` | `string` | - | Placeholder text |
| `disabled` | `boolean` | `false` | Disable input |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Input
  label="Email Address"
  type="email"
  placeholder="you@example.com"
  error={errors.email}
  onChange={(e) => handleChange('email', e.target.value)}
  required
/>
```

---

### Textarea

Multi-line text input field.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Field label |
| `error` | `string` | - | Error message |
| `helperText` | `string` | - | Helper text |
| `required` | `boolean` | `false` | Show required indicator |
| `rows` | `number` | - | Number of visible rows |
| `value` | `string` | - | Textarea value |
| `onChange` | `(e: React.ChangeEvent<HTMLTextAreaElement>) => void` | - | Change handler |
| `placeholder` | `string` | - | Placeholder text |
| `disabled` | `boolean` | `false` | Disable textarea |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Textarea
  label="Message"
  rows={5}
  placeholder="Enter your message..."
  value={message}
  onChange={(e) => setMessage(e.target.value)}
/>
```

---

### Select

Dropdown select field.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Field label |
| `error` | `string` | - | Error message |
| `helperText` | `string` | - | Helper text |
| `required` | `boolean` | `false` | Show required indicator |
| `options` | `Array<{value: string \| number; label: string}>` | - | Select options (required) |
| `placeholder` | `string` | - | Placeholder option text |
| `value` | `string \| number` | - | Selected value |
| `onChange` | `(e: React.ChangeEvent<HTMLSelectElement>) => void` | - | Change handler |
| `disabled` | `boolean` | `false` | Disable select |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Select
  label="Category"
  options={[
    { value: 'personal', label: 'Personal' },
    { value: 'business', label: 'Business' },
    { value: 'other', label: 'Other' },
  ]}
  placeholder="Select a category"
  onChange={(e) => setCategory(e.target.value)}
/>
```

---

### Checkbox

Checkbox input with optional label.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Checkbox label |
| `error` | `string` | - | Error message |
| `checked` | `boolean` | `false` | Checked state |
| `onChange` | `(e: React.ChangeEvent<HTMLInputElement>) => void` | - | Change handler |
| `disabled` | `boolean` | `false` | Disable checkbox |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Checkbox
  label="I agree to the terms"
  checked={agreed}
  onChange={(e) => setAgreed(e.target.checked)}
/>
```

---

### Toggle

Toggle switch control.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `label` | `string` | - | Toggle label |
| `checked` | `boolean` | - | Checked state (controlled) |
| `onChange` | `(checked: boolean) => void` | - | Change handler |
| `defaultChecked` | `boolean` | `false` | Initial state (uncontrolled) |
| `disabled` | `boolean` | `false` | Disable toggle |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Toggle
  label="Enable notifications"
  checked={notificationsEnabled}
  onChange={(checked) => setNotificationsEnabled(checked)}
/>
```

---

## Layout Components

### Card

Container component for grouping content.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | `string` | - | Card title |
| `subtitle` | `string` | - | Card subtitle |
| `actions` | `React.ReactNode` | - | Action buttons/controls |
| `variant` | `'default' \| 'elevated'` | `'default'` | Style variant |
| `padding` | `'sm' \| 'md' \| 'lg'` | `'md'` | Inner padding |
| `className` | `string` | `''` | Additional CSS classes |
| `children` | `React.ReactNode` | - | Card content (required) |

#### Example

```tsx
<Card
  title="Settings"
  subtitle="Manage your preferences"
  variant="elevated"
  actions={<Button size="sm">Reset</Button>}
>
  {/* Card content */}
</Card>
```

---

### Modal

Dialog modal component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `isOpen` | `boolean` | - | Modal visibility (required) |
| `onClose` | `() => void` | - | Close callback (required) |
| `title` | `string` | - | Modal title |
| `footer` | `React.ReactNode` | - | Footer content (buttons) |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Modal size |
| `closeButton` | `boolean` | `true` | Show close button |
| `className` | `string` | `''` | Additional CSS classes |
| `children` | `React.ReactNode` | - | Modal content (required) |

#### Features

- Click backdrop to close
- Press Escape to close
- Focus trap for accessibility
- Prevents body scroll

#### Example

```tsx
<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Confirm Delete"
  size="md"
  footer={
    <>
      <Button variant="secondary" onClick={() => setIsOpen(false)}>
        Cancel
      </Button>
      <Button variant="danger" onClick={handleDelete}>
        Delete
      </Button>
    </>
  }
>
  <p>Are you sure?</p>
</Modal>
```

---

### Dropdown

Context menu or dropdown component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `trigger` | `React.ReactNode` | - | Trigger element (required) |
| `items` | `DropdownItem[]` | - | Menu items (required) |
| `align` | `'left' \| 'right'` | `'left'` | Menu alignment |

#### DropdownItem Type

```typescript
interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  divider?: boolean;
  danger?: boolean;
}
```

#### Example

```tsx
<Dropdown
  trigger={<Button variant="ghost">Menu</Button>}
  items={[
    { id: 'edit', label: 'Edit', onClick: handleEdit },
    { id: 'divider', label: '', divider: true, onClick: () => {} },
    { id: 'delete', label: 'Delete', danger: true, onClick: handleDelete },
  ]}
  align="right"
/>
```

---

## Display Components

### Avatar

User avatar with image or initials fallback.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `src` | `string` | - | Image URL |
| `alt` | `string` | `'Avatar'` | Image alt text |
| `initials` | `string` | `'?'` | Fallback initials |
| `size` | `'sm' \| 'md' \| 'lg' \| 'xl'` | `'md'` | Avatar size |
| `onClick` | `() => void` | - | Click handler |
| `className` | `string` | `''` | Additional CSS classes |

#### Sizes

- `sm`: 32px
- `md`: 40px
- `lg`: 48px
- `xl`: 64px

#### Example

```tsx
<Avatar
  src="https://example.com/avatar.jpg"
  alt="John Doe"
  initials="JD"
  size="lg"
/>
```

---

### Badge

Status badge component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'default' \| 'success' \| 'warning' \| 'error' \| 'info' \| 'admin' \| 'maintainer' \| 'viewer'` | `'default'` | Badge style |
| `size` | `'sm' \| 'md'` | `'sm'` | Badge size |
| `icon` | `React.ReactNode` | - | Badge icon |
| `className` | `string` | `''` | Additional CSS classes |
| `children` | `React.ReactNode` | - | Badge text (required) |

#### Example

```tsx
<Badge variant="success" icon="✅">
  Active
</Badge>

<Badge variant="admin">
  Administrator
</Badge>
```

---

### Spinner

Loading spinner component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Spinner size |
| `color` | `'gold' \| 'slate' \| 'white'` | `'gold'` | Spinner color |
| `text` | `string` | - | Loading text |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Spinner
  size="lg"
  color="gold"
  text="Loading data..."
/>
```

---

### Alert

Alert notification component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `message` | `string` | - | Alert message (required) |
| `variant` | `'success' \| 'warning' \| 'error' \| 'info'` | `'info'` | Alert type |
| `dismissible` | `boolean` | `true` | Show close button |
| `icon` | `React.ReactNode` | - | Custom icon |
| `onDismiss` | `() => void` | - | Dismiss callback |
| `autoCloseDuration` | `number` | - | Auto-close delay (ms) |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<Alert
  message="Settings saved successfully"
  variant="success"
  autoCloseDuration={3000}
/>
```

---

### Tooltip

Hover tooltip component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `content` | `string` | - | Tooltip text (required) |
| `position` | `'top' \| 'bottom' \| 'left' \| 'right'` | `'top'` | Tooltip position |
| `delay` | `number` | `200` | Show delay (ms) |
| `children` | `React.ReactNode` | - | Trigger element (required) |

#### Example

```tsx
<Tooltip content="Click to edit" position="right">
  <button>Edit</button>
</Tooltip>
```

---

## Feature Components

### DrawingCard

Drawing thumbnail card component.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | `string` | - | Card ID (required) |
| `title` | `string` | - | Drawing title (required) |
| `thumbnail` | `string` | - | Thumbnail image URL |
| `lastModified` | `Date` | - | Last modified date (required) |
| `ownerName` | `string` | - | Owner name (required) |
| `ownerInitials` | `string` | - | Owner initials (required) |
| `ownerAvatar` | `string` | - | Owner avatar URL |
| `onEdit` | `(id: string) => void` | - | Edit callback |
| `onDuplicate` | `(id: string) => void` | - | Duplicate callback |
| `onDelete` | `(id: string) => void` | - | Delete callback |
| `onShare` | `(id: string) => void` | - | Share callback |
| `className` | `string` | `''` | Additional CSS classes |

#### Example

```tsx
<DrawingCard
  id="drawing-1"
  title="Q4 Report"
  thumbnail="/images/report.png"
  lastModified={new Date()}
  ownerName="Jane Smith"
  ownerInitials="JS"
  onEdit={(id) => navigate(`/edit/${id}`)}
  onDelete={(id) => handleDelete(id)}
/>
```

---

### DrawingGrid

Grid layout for drawing cards.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `drawings` | `Drawing[]` | - | Array of drawings (required) |
| `onEdit` | `(id: string) => void` | - | Edit callback |
| `onDuplicate` | `(id: string) => void` | - | Duplicate callback |
| `onDelete` | `(id: string) => void` | - | Delete callback |
| `onShare` | `(id: string) => void` | - | Share callback |
| `isLoading` | `boolean` | `false` | Show loading skeleton |
| `emptyMessage` | `string` | `'No drawings yet...'` | Empty state message |
| `columns` | `2 \| 3 \| 4 \| 5` | `3` | Grid columns |

#### Drawing Type

```typescript
interface Drawing {
  id: string;
  title: string;
  thumbnail?: string;
  lastModified: Date;
  ownerName: string;
  ownerInitials: string;
  ownerAvatar?: string;
}
```

#### Example

```tsx
<DrawingGrid
  drawings={drawings}
  columns={4}
  isLoading={isLoading}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

---

### GroupCard

Group information card.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `id` | `string` | - | Group ID (required) |
| `name` | `string` | - | Group name (required) |
| `description` | `string` | - | Group description |
| `memberCount` | `number` | - | Total members (required) |
| `members` | `GroupMember[]` | `[]` | Member list (up to 3) |
| `createdDate` | `Date` | - | Creation date (required) |
| `onEdit` | `(id: string) => void` | - | Edit callback |
| `onDelete` | `(id: string) => void` | - | Delete callback |
| `onViewMembers` | `(id: string) => void` | - | View members callback |
| `className` | `string` | `''` | Additional CSS classes |

#### GroupMember Type

```typescript
interface GroupMember {
  name: string;
  initials: string;
  avatar?: string;
}
```

#### Example

```tsx
<GroupCard
  id="team-1"
  name="Design Team"
  description="Core design team"
  memberCount={8}
  members={[
    { name: 'Alice', initials: 'A' },
    { name: 'Bob', initials: 'B' },
  ]}
  createdDate={new Date('2024-01-15')}
  onEdit={handleEdit}
/>
```

---

## Common Props

### All Components

| Prop | Type | Description |
|------|------|-------------|
| `className` | `string` | Additional Tailwind CSS classes |
| `key` | `string \| number` | React key (when in lists) |

### Form Components (Button, Input, Textarea, Select, Checkbox)

| Prop | Type | Description |
|------|------|-------------|
| `disabled` | `boolean` | Disable the component |
| `id` | `string` | Element ID for labels |

### Container Components (Card, Modal, Dropdown)

| Prop | Type | Description |
|------|------|-------------|
| `children` | `React.ReactNode` | Component content |

---

## Type Exports

All component types are exported from the index:

```typescript
import type { Drawing } from '@/client/components/common';
```

---

## Callback Patterns

### Form Submission

```tsx
const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
  // Handle submission
};
```

### Button Click

```tsx
const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
  // Handle click
};
```

### Input Change

```tsx
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};
```

---

## Accessibility Notes

- All inputs have associated labels
- Buttons have proper aria-labels
- Modals have dialog role and focus management
- Color is never the only indicator
- All interactive elements are keyboard accessible

---

## Performance Considerations

- Components use React.memo where appropriate
- Event handlers are optimized to prevent unnecessary re-renders
- Modal and Dropdown use portal-like behavior for proper stacking
- Avatar and images are lazy-loaded when possible

---

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari 12+, Chrome Android

---

## Styling Notes

All components use:
- Tailwind CSS for styling
- Custom `ice-gold-*` color palette
- Dark theme by default
- Responsive design with mobile-first approach
