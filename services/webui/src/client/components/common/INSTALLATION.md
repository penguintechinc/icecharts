# Component Library Installation & Setup

Complete guide to installing and using the IceCharts common UI component library.

## File Structure

```
src/client/components/common/
├── Button.tsx                 # Button component with variants
├── Input.tsx                  # Text input with validation
├── Textarea.tsx               # Multi-line text input
├── Select.tsx                 # Dropdown select
├── Checkbox.tsx               # Checkbox control
├── Toggle.tsx                 # Toggle switch
├── Card.tsx                   # Card container
├── Modal.tsx                  # Dialog modal
├── Dropdown.tsx               # Context menu
├── Avatar.tsx                 # User avatar
├── Badge.tsx                  # Status badge
├── Spinner.tsx                # Loading spinner
├── Alert.tsx                  # Alert notification
├── Tooltip.tsx                # Hover tooltip
├── colors.ts                  # Color constants
├── index.ts                   # Barrel export
├── drawing/
│   ├── DrawingCard.tsx        # Drawing thumbnail card
│   └── DrawingGrid.tsx        # Grid of drawing cards
├── group/
│   └── GroupCard.tsx          # Group card
├── README.md                  # Component documentation
├── EXAMPLES.tsx               # Usage examples
├── TESTING.md                 # Testing guide
└── INSTALLATION.md            # This file
```

## Quick Start

### 1. Basic Imports

```tsx
// Import individual components
import { Button, Input, Card } from '@/client/components/common';

// Or use barrel import
import * as Common from '@/client/components/common';
```

### 2. Create a Simple Form

```tsx
import React, { useState } from 'react';
import { Button, Input, Card, Alert } from '@/client/components/common';

export function MyForm() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = () => {
    // Validate and submit
    setMessage('Form submitted!');
  };

  return (
    <Card title="Contact Us" className="max-w-md">
      <div className="space-y-4">
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        {message && (
          <Alert message={message} variant="success" autoCloseDuration={3000} />
        )}

        <Button variant="primary" onClick={handleSubmit}>
          Send
        </Button>
      </div>
    </Card>
  );
}
```

### 3. Use Feature-Specific Components

```tsx
import { DrawingGrid, GroupCard } from '@/client/components/common';

export function MyGallery() {
  const drawings = [
    {
      id: '1',
      title: 'My Drawing',
      lastModified: new Date(),
      ownerName: 'John',
      ownerInitials: 'J',
    },
  ];

  return (
    <DrawingGrid
      drawings={drawings}
      columns={3}
      onEdit={(id) => console.log('Edit', id)}
      onDelete={(id) => console.log('Delete', id)}
    />
  );
}
```

## Component Dependencies

All components use:
- **React 18.3+**: Core framework
- **Tailwind CSS 3.4+**: Styling
- **TypeScript 5.7+**: Type safety

### Tailwind Configuration Required

Ensure your `tailwind.config.js` includes:

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'ice-gold': {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
      },
    },
  },
  plugins: [],
};
```

### CSS Setup Required

Add to `src/client/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Ensure dark theme is applied */
html {
  color-scheme: dark;
}
```

## Component Imports by Category

### Form Components
```tsx
import {
  Button,
  Input,
  Textarea,
  Select,
  Checkbox,
  Toggle,
} from '@/client/components/common';
```

### Layout Components
```tsx
import {
  Card,
  Modal,
  Dropdown,
} from '@/client/components/common';
```

### Display Components
```tsx
import {
  Avatar,
  Badge,
  Spinner,
  Alert,
  Tooltip,
} from '@/client/components/common';
```

### Feature Components
```tsx
import {
  DrawingCard,
  DrawingGrid,
  GroupCard,
} from '@/client/components/common';
```

## Common Usage Patterns

### Form Validation Pattern

```tsx
import { useState } from 'react';
import { Button, Input, Alert } from '@/client/components/common';

export function ValidatedForm() {
  const [formData, setFormData] = useState({ email: '', name: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.name) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    return newErrors;
  };

  const handleSubmit = () => {
    const formErrors = validateForm();
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }

    // Submit form
    console.log('Submitting:', formData);
  };

  return (
    <div className="space-y-4">
      <Input
        label="Name"
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        error={errors.name}
        required
      />

      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        error={errors.email}
        required
      />

      <Button onClick={handleSubmit} variant="primary">
        Submit
      </Button>
    </div>
  );
}
```

### Modal with Actions Pattern

```tsx
import { useState } from 'react';
import { Button, Modal, Alert } from '@/client/components/common';

export function DeleteConfirmation() {
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState('');

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      // Call API to delete
      await new Promise(r => setTimeout(r, 1000));
      setMessage('Item deleted successfully');
      setIsOpen(false);
    } catch (error) {
      setMessage('Failed to delete item');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)} variant="danger">
        Delete Item
      </Button>

      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Confirm Deletion"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setIsOpen(false)}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDelete}
              isLoading={isDeleting}
            >
              Delete
            </Button>
          </>
        }
      >
        <p>Are you sure you want to delete this item? This action cannot be undone.</p>
        {message && <Alert message={message} variant="error" className="mt-4" />}
      </Modal>
    </>
  );
}
```

### Grid with Pagination Pattern

```tsx
import { useState, useEffect } from 'react';
import { DrawingGrid, Spinner, Button } from '@/client/components/common';

export function DrawingsWithPagination() {
  const [drawings, setDrawings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    setIsLoading(true);
    // Fetch drawings for page
    setTimeout(() => {
      setDrawings([
        {
          id: '1',
          title: `Drawing ${page}`,
          lastModified: new Date(),
          ownerName: 'John',
          ownerInitials: 'J',
        },
      ]);
      setIsLoading(false);
    }, 500);
  }, [page]);

  if (isLoading && page === 1) {
    return <Spinner size="lg" text="Loading drawings..." />;
  }

  return (
    <div>
      <DrawingGrid
        drawings={drawings}
        isLoading={isLoading}
        columns={3}
      />

      <div className="flex justify-between items-center mt-6 px-4">
        <Button
          variant="secondary"
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </Button>

        <span className="text-slate-400">Page {page}</span>

        <Button
          variant="secondary"
          onClick={() => setPage(p => p + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
```

## Customization

### Custom Color Scheme

Modify `colors.ts`:

```typescript
export const colors = {
  primary: {
    400: '#your-color-hex',
    500: '#your-color-hex',
    // ... other shades
  },
  // ... other color categories
};
```

Update components to use custom colors:

```tsx
<Button className="bg-your-primary hover:bg-your-primary-dark">
  Custom Button
</Button>
```

### Custom Styling

Override component styles with className prop:

```tsx
<Button className="rounded-full font-bold">
  Custom Button
</Button>
```

### Tailwind Theme Extension

Add to `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      // Your custom colors
      'custom-primary': '#...',
    },
    spacing: {
      // Custom spacing
    },
  },
}
```

## Performance Optimization

### Lazy Load Components

```tsx
import { lazy, Suspense } from 'react';
import { Spinner } from '@/client/components/common';

const DrawingGrid = lazy(() => import('./drawing/DrawingGrid'));

export function OptimizedGallery() {
  return (
    <Suspense fallback={<Spinner size="lg" text="Loading..." />}>
      <DrawingGrid drawings={[]} />
    </Suspense>
  );
}
```

### Memoize Components

```tsx
import { memo } from 'react';
import { Card } from '@/client/components/common';

const MemoizedCard = memo(Card);
```

## TypeScript Support

All components have full TypeScript support with exported types:

```tsx
import type { ButtonProps } from '@/client/components/common/Button';

interface MyComponentProps extends ButtonProps {
  customProp: string;
}
```

## Troubleshooting

### Components Not Rendering

**Issue**: Components appear unstyled or don't render.

**Solutions**:
1. Verify Tailwind CSS is installed: `npm ls tailwindcss`
2. Check `tailwind.config.js` includes component paths
3. Ensure CSS file imports `@tailwind` directives
4. Clear Tailwind cache: `rm -rf .next` (Next.js) or `npm run build`

### Color Not Working

**Issue**: Ice-gold colors not appearing.

**Solution**: Add to `tailwind.config.js`:
```javascript
colors: {
  'ice-gold': { /* colors */ }
}
```

### Modal Not Closing

**Issue**: Modal backdrop or close button not working.

**Solution**: Ensure `onClose` callback is properly defined:
```tsx
<Modal isOpen={isOpen} onClose={() => setIsOpen(false)}>
```

### Types Not Found

**Issue**: TypeScript errors about missing types.

**Solution**: Ensure `tsconfig.json` includes component paths:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## Best Practices

1. **Use Semantic Components**
   - Prefer Button over div with click handler
   - Use Input for text entry
   - Use Modal for dialogs

2. **Handle Errors Gracefully**
   - Display error messages using Alert or Input error prop
   - Use try-catch for async operations
   - Provide feedback for user actions

3. **Accessibility First**
   - Always include labels for form inputs
   - Use proper heading hierarchy
   - Test with keyboard navigation

4. **Responsive Design**
   - Use mobile-first approach
   - Test on multiple screen sizes
   - Consider touch targets (min 44px)

5. **Performance**
   - Memoize expensive components
   - Lazy load heavy components
   - Avoid unnecessary re-renders

## Migration from Old Components

If migrating from custom components:

```tsx
// Old
import OldButton from './OldButton';

// New
import { Button } from '@/client/components/common';

// Update className references
<OldButton className="btn-primary" />
// becomes
<Button variant="primary" />
```

## Contributing

To add new components:

1. Create component in appropriate directory
2. Add TypeScript types/interfaces
3. Document in README.md
4. Add examples to EXAMPLES.tsx
5. Add tests to TESTING.md
6. Update index.ts barrel export

## Support

For issues or questions:
- Check README.md for documentation
- Review EXAMPLES.tsx for usage patterns
- Check TESTING.md for test examples
- Review component source code for implementation details

## License

These components are part of IceCharts and follow the same license.
