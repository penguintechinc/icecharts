# Component Library Cheat Sheet

Quick reference for the IceCharts common component library.

## Import Patterns

```tsx
// Single import
import { Button } from '@/client/components/common';

// Multiple imports
import { Button, Input, Card, Modal } from '@/client/components/common';

// Namespace import
import * as UI from '@/client/components/common';
// Usage: <UI.Button>Click</UI.Button>
```

## Form Components Quickstart

### Button
```tsx
<Button variant="primary" size="md" icon="➕">Click</Button>
<Button variant="secondary" disabled>Disabled</Button>
<Button variant="danger" isLoading>Deleting...</Button>
<Button variant="ghost">Ghost</Button>
```

### Input
```tsx
<Input label="Email" type="email" required />
<Input label="Name" error="Required" />
<Input label="Phone" helperText="Format: (555) 555-5555" />
```

### Select
```tsx
<Select
  label="Category"
  options={[
    { value: 'a', label: 'Option A' },
    { value: 'b', label: 'Option B' },
  ]}
  placeholder="Choose..."
/>
```

### Textarea
```tsx
<Textarea label="Message" rows={4} required />
<Textarea error="Too long" helperText="Max 500 chars" />
```

### Checkbox
```tsx
<Checkbox label="I agree" checked={agreed} onChange={handle} />
```

### Toggle
```tsx
<Toggle label="Dark Mode" checked={dark} onChange={setDark} />
```

## Layout Components Quickstart

### Card
```tsx
<Card title="Settings" subtitle="Manage preferences">
  Content here
</Card>

<Card variant="elevated" padding="lg">
  Elevated card
</Card>

<Card title="Actions" actions={<Button size="sm">Reset</Button>}>
  Content
</Card>
```

### Modal
```tsx
const [open, setOpen] = useState(false);

<Modal isOpen={open} onClose={() => setOpen(false)} title="Dialog">
  <p>Content</p>
</Modal>
```

### Dropdown
```tsx
<Dropdown
  trigger={<Button>Menu</Button>}
  items={[
    { id: '1', label: 'Edit', onClick: handleEdit },
    { id: 'div', label: '', divider: true, onClick: () => {} },
    { id: '2', label: 'Delete', danger: true, onClick: handleDelete },
  ]}
/>
```

## Display Components Quickstart

### Avatar
```tsx
<Avatar src="/avatar.jpg" initials="JD" size="md" />
<Avatar initials="AB" size="lg" />
```

### Badge
```tsx
<Badge variant="success">Active</Badge>
<Badge variant="admin">Admin</Badge>
<Badge variant="error" icon="❌">Error</Badge>
```

### Spinner
```tsx
<Spinner size="lg" text="Loading..." />
<Spinner color="white" />
```

### Alert
```tsx
<Alert message="Saved!" variant="success" />
<Alert message="Error!" variant="error" autoCloseDuration={3000} />
```

### Tooltip
```tsx
<Tooltip content="Click to edit" position="top">
  <button>Edit</button>
</Tooltip>
```

## Feature Components Quickstart

### DrawingCard
```tsx
<DrawingCard
  id="1"
  title="Report"
  lastModified={new Date()}
  ownerName="John"
  ownerInitials="J"
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

### DrawingGrid
```tsx
<DrawingGrid
  drawings={drawings}
  columns={3}
  isLoading={false}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>
```

### GroupCard
```tsx
<GroupCard
  id="1"
  name="Team"
  memberCount={5}
  members={[{name: 'Alice', initials: 'A'}]}
  createdDate={new Date()}
  onEdit={handleEdit}
/>
```

## Common Patterns

### Form with Validation
```tsx
const [data, setData] = useState({ email: '' });
const [errors, setErrors] = useState<Record<string, string>>({});

const validate = () => {
  const newErrors: Record<string, string> = {};
  if (!data.email) newErrors.email = 'Required';
  return newErrors;
};

const handleSubmit = () => {
  const errs = validate();
  if (Object.keys(errs).length) {
    setErrors(errs);
    return;
  }
  // Submit
};

return (
  <>
    <Input
      label="Email"
      value={data.email}
      onChange={(e) => setData({ ...data, email: e.target.value })}
      error={errors.email}
    />
    <Button onClick={handleSubmit}>Submit</Button>
  </>
);
```

### Modal Dialog
```tsx
const [open, setOpen] = useState(false);

<>
  <Button onClick={() => setOpen(true)}>Open</Button>
  <Modal
    isOpen={open}
    onClose={() => setOpen(false)}
    title="Confirm"
    footer={
      <>
        <Button variant="secondary" onClick={() => setOpen(false)}>Cancel</Button>
        <Button variant="danger" onClick={() => { handleDelete(); setOpen(false); }}>Delete</Button>
      </>
    }
  >
    Are you sure?
  </Modal>
</>
```

### Loading State
```tsx
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  try {
    await api.submit(data);
  } finally {
    setLoading(false);
  }
};

<Button isLoading={loading} onClick={handleSubmit}>Save</Button>
```

### Conditional Rendering
```tsx
{isLoading ? (
  <Spinner size="lg" text="Loading..." />
) : items.length > 0 ? (
  <DrawingGrid drawings={items} />
) : (
  <Alert message="No items found" variant="info" />
)}
```

## Variant & Size Quick Reference

### Button Variants
- `primary` - Gold background (main action)
- `secondary` - Dark background (alternative)
- `danger` - Red background (destructive)
- `ghost` - Transparent (low emphasis)

### Button Sizes
- `sm` - Small (px-3 py-1.5 text-sm)
- `md` - Medium (px-4 py-2)
- `lg` - Large (px-6 py-3 text-lg)

### Avatar Sizes
- `sm` - 32px
- `md` - 40px (default)
- `lg` - 48px
- `xl` - 64px

### Card Variants
- `default` - Normal border
- `elevated` - With shadow

### Card Padding
- `sm` - p-3
- `md` - p-4 (default)
- `lg` - p-6

### Modal Sizes
- `sm` - max-w-sm
- `md` - max-w-md (default)
- `lg` - max-w-lg

### Spinner Sizes
- `sm` - 16px
- `md` - 32px (default)
- `lg` - 48px

### Spinner Colors
- `gold` - Ice-gold primary (default)
- `slate` - Slate gray
- `white` - White

### Badge Variants
- `default` - Gray
- `success` - Green
- `warning` - Amber
- `error` - Red
- `info` - Blue
- `admin` - Red (special)
- `maintainer` - Blue (special)
- `viewer` - Green (special)

### Alert Variants
- `success` - Green alert
- `warning` - Amber alert
- `error` - Red alert
- `info` - Blue alert (default)

## Color Palette

### Primary
- Ice-gold: `#fbbf24` (gold-400)

### Background
- Dark-900: `#0f172a` (page bg)
- Dark-800: `#1e293b` (surface)
- Dark-700: `#334155` (borders)

### Text
- Text-100: `#f1f5f9` (primary text)
- Text-400: `#94a3b8` (muted)

## Accessibility Tips

✅ Always include labels for form inputs
```tsx
<Input label="Email" type="email" />
```

✅ Use semantic HTML elements
```tsx
<Button>Click me</Button>  // Not <div onClick>
```

✅ Provide error messages
```tsx
<Input error="This field is required" />
```

✅ Test keyboard navigation
- Tab through form fields
- Enter to submit forms
- Escape to close modals
- Arrow keys for dropdowns

## Performance Tips

💡 Memoize expensive components
```tsx
const MemoCard = memo(DrawingCard);
```

💡 Lazy load modals
```tsx
const ConfirmModal = lazy(() => import('./ConfirmModal'));
```

💡 Minimize re-renders with useCallback
```tsx
const handleClick = useCallback(() => { }, []);
```

## Common Mistakes

❌ Forgetting onChange handler
```tsx
// Wrong
<Input value={text} />

// Right
<Input value={text} onChange={(e) => setText(e.target.value)} />
```

❌ Not providing onClose for Modal
```tsx
// Wrong
<Modal isOpen={open}>Content</Modal>

// Right
<Modal isOpen={open} onClose={() => setOpen(false)}>Content</Modal>
```

❌ Using div instead of Button
```tsx
// Wrong
<div onClick={handleClick}>Click me</div>

// Right
<Button onClick={handleClick}>Click me</Button>
```

❌ Forgetting label for input
```tsx
// Wrong
<Input placeholder="Email" />

// Right
<Input label="Email" placeholder="user@example.com" />
```

## Styling Examples

### Add custom classes
```tsx
<Button className="rounded-full">Pill Button</Button>
<Card className="max-w-lg">Wide Card</Card>
```

### Responsive classes
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {items.map(item => <DrawingCard key={item.id} {...item} />)}
</div>
```

### Spacing utilities
```tsx
<div className="space-y-4">
  <Input label="Field 1" />
  <Input label="Field 2" />
  <Input label="Field 3" />
</div>
```

## TypeScript Support

### Type imports
```tsx
import type { Drawing } from '@/client/components/common';

interface MyProps {
  drawing: Drawing;
}
```

### Component props
```tsx
import type { ButtonHTMLAttributes } from 'react';

interface CustomButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  custom?: boolean;
}
```

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Button not styled | Check Tailwind CSS setup |
| Modal won't close | Ensure `onClose` callback |
| Input not responding | Check `onChange` handler |
| Dropdown empty | Verify `items` prop structure |
| Dark theme not applied | Check `darkMode: 'class'` in Tailwind config |

## Resources

- 📖 [Full README](./README.md) - Complete documentation
- 🎨 [API Reference](./API_REFERENCE.md) - Detailed props
- 💻 [Examples](./EXAMPLES.tsx) - Usage examples
- 🧪 [Testing Guide](./TESTING.md) - Testing patterns
- 📦 [Installation](./INSTALLATION.md) - Setup instructions

## Quick Links

- **Form Components**: Input, Textarea, Select, Checkbox, Toggle
- **Layout Components**: Card, Modal, Dropdown
- **Display Components**: Avatar, Badge, Spinner, Alert, Tooltip
- **Feature Components**: DrawingCard, DrawingGrid, GroupCard
