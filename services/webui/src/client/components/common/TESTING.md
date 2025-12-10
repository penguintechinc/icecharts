# Component Testing Guide

This guide provides testing strategies and examples for the IceCharts common component library.

## Testing Setup

The components are built with React and TypeScript. Recommended testing libraries:

- **Jest**: Unit testing framework
- **React Testing Library**: Component testing utilities
- **Vitest**: Modern test runner (compatible with Vite)

### Installation

```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom jsdom
```

### Vitest Configuration

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

Create `src/test/setup.ts`:

```typescript
import '@testing-library/jest-dom';
```

## Test Examples

### Button Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from '../Button';

describe('Button Component', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('applies primary variant by default', () => {
    render(<Button>Primary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-ice-gold-400');
  });

  it('applies secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>);
    const button = screen.getByRole('button');
    expect(button).toHaveClass('bg-slate-700');
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalled();
  });

  it('disables button when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading spinner when isLoading is true', () => {
    render(<Button isLoading>Save</Button>);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('disables button when loading', () => {
    render(<Button isLoading>Save</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('px-3', 'py-1.5');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('px-6', 'py-3');
  });

  it('renders icon in correct position', () => {
    const { rerender } = render(
      <Button icon="➕" iconPosition="left">
        Add
      </Button>
    );

    let button = screen.getByRole('button');
    expect(button.textContent).toMatch(/➕.*Add/);

    rerender(
      <Button icon="➕" iconPosition="right">
        Add
      </Button>
    );

    button = screen.getByRole('button');
    expect(button.textContent).toMatch(/Add.*➕/);
  });
});
```

### Input Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Input from '../Input';

describe('Input Component', () => {
  it('renders with label', () => {
    render(<Input label="Email" />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(<Input label="Email" error="Invalid email" />);
    expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
  });

  it('displays helper text', () => {
    render(<Input label="Password" helperText="Min 8 characters" />);
    expect(screen.getByText(/min 8 characters/i)).toBeInTheDocument();
  });

  it('shows required indicator', () => {
    render(<Input label="Name" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('handles input changes', async () => {
    render(<Input placeholder="Type here" />);
    const input = screen.getByPlaceholderText(/type here/i);

    await userEvent.type(input, 'hello');
    expect(input).toHaveValue('hello');
  });

  it('applies error styling when error exists', () => {
    const { rerender } = render(<Input error="Error message" />);
    let input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-red-500');

    rerender(<Input />);
    input = screen.getByRole('textbox');
    expect(input).toHaveClass('border-slate-700');
  });
});
```

### Modal Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Modal from '../Modal';

describe('Modal Component', () => {
  it('does not render when isOpen is false', () => {
    render(
      <Modal isOpen={false} onClose={() => {}}>
        Content
      </Modal>
    );
    expect(screen.queryByText(/content/i)).not.toBeInTheDocument();
  });

  it('renders when isOpen is true', () => {
    render(
      <Modal isOpen={true} onClose={() => {}}>
        Content
      </Modal>
    );
    expect(screen.getByText(/content/i)).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(
      <Modal isOpen={true} onClose={() => {}} title="Test Modal">
        Content
      </Modal>
    );
    expect(screen.getByText(/test modal/i)).toBeInTheDocument();
  });

  it('calls onClose when backdrop is clicked', async () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={handleClose}>
        Content
      </Modal>
    );

    const backdrop = screen.getByRole('dialog').parentElement;
    await userEvent.click(backdrop as HTMLElement);
    expect(handleClose).toHaveBeenCalled();
  });

  it('calls onClose when close button is clicked', async () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={handleClose} closeButton>
        Content
      </Modal>
    );

    const closeButton = screen.getByLabelText(/close dialog/i);
    await userEvent.click(closeButton);
    expect(handleClose).toHaveBeenCalled();
  });

  it('calls onClose when Escape key is pressed', async () => {
    const handleClose = jest.fn();
    render(
      <Modal isOpen={true} onClose={handleClose}>
        Content
      </Modal>
    );

    await userEvent.keyboard('{Escape}');
    expect(handleClose).toHaveBeenCalled();
  });

  it('prevents body scroll when open', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={() => {}}>
        Content
      </Modal>
    );

    expect(document.body.style.overflow).toBe('hidden');

    rerender(
      <Modal isOpen={false} onClose={() => {}}>
        Content
      </Modal>
    );

    expect(document.body.style.overflow).toBe('unset');
  });

  it('applies correct size classes', () => {
    const { rerender } = render(
      <Modal isOpen={true} onClose={() => {}} size="sm">
        Content
      </Modal>
    );

    expect(screen.getByRole('dialog')).toHaveClass('max-w-sm');

    rerender(
      <Modal isOpen={true} onClose={() => {}} size="lg">
        Content
      </Modal>
    );

    expect(screen.getByRole('dialog')).toHaveClass('max-w-lg');
  });
});
```

### DrawingGrid Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import DrawingGrid from '../drawing/DrawingGrid';

describe('DrawingGrid Component', () => {
  const mockDrawings = [
    {
      id: '1',
      title: 'Drawing 1',
      lastModified: new Date(),
      ownerName: 'John',
      ownerInitials: 'J',
    },
    {
      id: '2',
      title: 'Drawing 2',
      lastModified: new Date(),
      ownerName: 'Jane',
      ownerInitials: 'JA',
    },
  ];

  it('renders empty state when no drawings', () => {
    render(
      <DrawingGrid
        drawings={[]}
        emptyMessage="No drawings found"
      />
    );
    expect(screen.getByText(/no drawings found/i)).toBeInTheDocument();
  });

  it('renders drawing cards', () => {
    render(<DrawingGrid drawings={mockDrawings} />);
    expect(screen.getByText(/drawing 1/i)).toBeInTheDocument();
    expect(screen.getByText(/drawing 2/i)).toBeInTheDocument();
  });

  it('shows loading skeleton', () => {
    render(
      <DrawingGrid
        drawings={[]}
        isLoading={true}
      />
    );
    expect(screen.getByRole('article')).toHaveClass('animate-pulse');
  });

  it('applies correct grid column classes', () => {
    const { container } = render(
      <DrawingGrid drawings={mockDrawings} columns={4} />
    );
    const grid = container.querySelector('.grid');
    expect(grid).toHaveClass('grid-cols-1', 'sm:grid-cols-2', 'lg:grid-cols-4');
  });

  it('calls onEdit callback', async () => {
    const handleEdit = jest.fn();
    render(
      <DrawingGrid drawings={mockDrawings} onEdit={handleEdit} />
    );
    // Mock clicking the edit action
  });
});
```

### Accessibility Tests

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import Button from '../Button';
import Input from '../Input';
import Modal from '../Modal';

expect.extend(toHaveNoViolations);

describe('Accessibility', () => {
  it('Button has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Input has no accessibility violations', async () => {
    const { container } = render(<Input label="Email" />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Modal has no accessibility violations', async () => {
    const { container } = render(
      <Modal isOpen={true} onClose={() => {}} title="Test">
        Content
      </Modal>
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('Button has proper ARIA attributes', () => {
    const { getByRole } = render(<Button>Submit</Button>);
    expect(getByRole('button')).toBeInTheDocument();
  });

  it('Input labels are associated', () => {
    const { getByLabelText } = render(<Input label="Email" />);
    expect(getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('Modal has dialog role', () => {
    const { getByRole } = render(
      <Modal isOpen={true} onClose={() => {}}>
        Content
      </Modal>
    );
    expect(getByRole('dialog')).toBeInTheDocument();
  });
});
```

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm run test -- Button.test.tsx

# Run with coverage
npm run test:coverage
```

## Test Coverage Goals

| Category | Target |
|----------|--------|
| Statements | 80%+ |
| Branches | 75%+ |
| Functions | 80%+ |
| Lines | 80%+ |

## Integration Testing

For testing component interactions with the application:

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SettingsPage from '@/client/pages/SettingsPage';

describe('Settings Page Integration', () => {
  it('allows user to update settings', async () => {
    render(<SettingsPage />);

    const input = screen.getByLabelText(/notification email/i);
    await userEvent.clear(input);
    await userEvent.type(input, 'new@example.com');

    const saveButton = screen.getByRole('button', { name: /save/i });
    await userEvent.click(saveButton);

    expect(screen.getByText(/settings saved/i)).toBeInTheDocument();
  });
});
```

## Snapshot Testing (Use Sparingly)

For complex components with consistent output:

```typescript
import { render } from '@testing-library/react';
import Card from '../Card';

describe('Card Snapshot', () => {
  it('renders correctly', () => {
    const { container } = render(
      <Card title="Test Card">
        Content
      </Card>
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
```

## Best Practices

1. **Test Behavior, Not Implementation**
   - Test what users see and interact with
   - Avoid testing internal state directly

2. **Use Semantic Queries**
   - Prefer `getByRole`, `getByLabelText`
   - Avoid `querySelector` or data-testid when possible

3. **Test User Interactions**
   - Use `userEvent` instead of `fireEvent`
   - Test actual user workflows

4. **Test Accessibility**
   - Use jest-axe for automated checks
   - Manual testing of keyboard navigation
   - Screen reader compatibility

5. **Mock External Dependencies**
   - Mock API calls
   - Mock routing
   - Mock context providers

6. **Keep Tests Focused**
   - One test per concept
   - Avoid testing multiple things in one test
   - Use descriptive test names

7. **Test Error States**
   - Invalid inputs
   - Error messages
   - Disabled states

8. **Performance Testing**
   - Test render performance
   - Test animation smoothness
   - Monitor bundle size

## Debugging Tests

```typescript
import { render, screen } from '@testing-library/react';

// Print the DOM
render(<Component />);
screen.debug();

// Print specific element
screen.debug(screen.getByRole('button'));

// Use screen.logTestingPlaygroundURL()
// Generates a URL for Test Playground
```

## CI/CD Integration

Add to GitHub Actions workflow:

```yaml
- name: Run Tests
  run: npm run test:ci

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage/coverage-final.json
```

## Resources

- [React Testing Library Docs](https://testing-library.com/react)
- [Vitest Documentation](https://vitest.dev)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [Accessibility Testing](https://www.w3.org/WAI/test-evaluate/)
