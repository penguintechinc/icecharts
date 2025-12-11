/**
 * Test file for IconSearch component and useIconSearch hook
 *
 * Run tests with: npm test -- IconSearch.test
 */

import { renderHook, act } from '@testing-library/react';
import { useIconSearch } from './useIconSearch';
import type { IconDefinition } from '../types';

describe('useIconSearch hook', () => {
  const mockIcons: IconDefinition[] = [
    {
      id: 'aws',
      label: 'AWS',
      source: 'aws',
      color: '#FF9900',
      tags: ['cloud', 'provider', 'amazon'],
    },
    {
      id: 'azure',
      label: 'Azure',
      source: 'azure',
      color: '#0078D4',
      tags: ['cloud', 'provider', 'microsoft'],
    },
    {
      id: 'database',
      label: 'Database',
      source: 'internal',
      color: '#6B7280',
      tags: ['storage', 'data'],
    },
    {
      id: 'postgres',
      label: 'PostgreSQL',
      source: 'internal',
      color: '#336791',
      tags: ['database', 'sql', 'relational'],
    },
    {
      id: 'redis',
      label: 'Redis',
      source: 'internal',
      color: '#DC382D',
      tags: ['database', 'cache', 'nosql'],
    },
  ];

  test('should initialize with empty results', () => {
    const { result } = renderHook(() => useIconSearch());

    expect(result.current.results).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  test('should search for icons with exact label match', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('AWS', mockIcons);
    });

    // Wait for async search
    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results.length).toBeGreaterThan(0);
    expect(result.current.results[0].id).toBe('aws');
  });

  test('should search for icons with partial match', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('data', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    const ids = result.current.results.map(r => r.id);
    expect(ids).toContain('database');
    expect(ids).toContain('postgres');
  });

  test('should search by tags', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('cloud', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    const ids = result.current.results.map(r => r.id);
    expect(ids).toContain('aws');
    expect(ids).toContain('azure');
  });

  test('should rank results by relevance', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('database', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    // 'database' should rank higher than others since it's an exact label match
    expect(result.current.results[0].id).toBe('database');
  });

  test('should return empty results for no matches', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('nonexistent', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results).toEqual([]);
  });

  test('should clear results', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('AWS', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results.length).toBeGreaterThan(0);

    act(() => {
      result.current.clear();
    });

    expect(result.current.results).toEqual([]);
  });

  test('should respect maxResults option', async () => {
    const { result } = renderHook(() => useIconSearch({ maxResults: 2 }));

    act(() => {
      result.current.search('db', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results.length).toBeLessThanOrEqual(2);
  });

  test('should perform fuzzy matching', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('db', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    // 'db' should fuzzy match 'database'
    const ids = result.current.results.map(r => r.id);
    expect(ids.length).toBeGreaterThan(0);
  });

  test('should be case insensitive', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('awS', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results.length).toBeGreaterThan(0);
    expect(result.current.results[0].id).toBe('aws');
  });

  test('should handle empty query', () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('', mockIcons);
    });

    expect(result.current.results).toEqual([]);
  });

  test('should handle whitespace-only query', () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('   ', mockIcons);
    });

    expect(result.current.results).toEqual([]);
  });

  test('should include score in results', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('AWS', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(result.current.results[0]).toHaveProperty('score');
    expect(typeof result.current.results[0].score).toBe('number');
    expect(result.current.results[0].score).toBeGreaterThan(0);
  });

  test('should maintain icon metadata in results', async () => {
    const { result } = renderHook(() => useIconSearch());

    act(() => {
      result.current.search('AWS', mockIcons);
    });

    await new Promise(resolve => setTimeout(resolve, 100));

    const awsIcon = result.current.results[0];
    expect(awsIcon.id).toBe('aws');
    expect(awsIcon.label).toBe('AWS');
    expect(awsIcon.source).toBe('aws');
    expect(awsIcon.color).toBe('#FF9900');
    expect(awsIcon.tags).toBeDefined();
  });
});

describe('IconSearch component integration', () => {
  /**
   * Component integration tests would go here
   * These would require:
   * - React Testing Library setup
   * - DOM queries for input, dropdown, results
   * - User interaction simulation (typing, keyboard navigation)
   * - Accessibility testing
   *
   * Example:
   *
   * test('should render search input with placeholder', () => {
   *   render(
   *     <IconSearch
   *       onSelect={jest.fn()}
   *       allIcons={mockIcons}
   *       placeholder="Search icons..."
   *       iconMap={mockIconMap}
   *     />
   *   );
   *
   *   const input = screen.getByPlaceholderText('Search icons...');
   *   expect(input).toBeInTheDocument();
   * });
   *
   * test('should show results when typing', async () => {
   *   const user = userEvent.setup();
   *
   *   render(
   *     <IconSearch
   *       onSelect={jest.fn()}
   *       allIcons={mockIcons}
   *       iconMap={mockIconMap}
   *     />
   *   );
   *
   *   const input = screen.getByRole('textbox');
   *   await user.type(input, 'aws');
   *
   *   await waitFor(() => {
   *     expect(screen.getByText('AWS')).toBeInTheDocument();
   *   });
   * });
   *
   * test('should call onSelect when icon is clicked', async () => {
   *   const onSelect = jest.fn();
   *   const user = userEvent.setup();
   *
   *   render(
   *     <IconSearch
   *       onSelect={onSelect}
   *       allIcons={mockIcons}
   *       iconMap={mockIconMap}
   *     />
   *   );
   *
   *   const input = screen.getByRole('textbox');
   *   await user.type(input, 'aws');
   *
   *   const awsOption = await screen.findByText('AWS');
   *   await user.click(awsOption);
   *
   *   expect(onSelect).toHaveBeenCalledWith(mockIcons[0]);
   * });
   *
   * test('should navigate with arrow keys', async () => {
   *   const user = userEvent.setup();
   *   const onSelect = jest.fn();
   *
   *   render(
   *     <IconSearch
   *       onSelect={onSelect}
   *       allIcons={mockIcons}
   *       iconMap={mockIconMap}
   *     />
   *   );
   *
   *   const input = screen.getByRole('textbox');
   *   await user.type(input, 'database');
   *   await user.keyboard('{ArrowDown}');
   *   await user.keyboard('{Enter}');
   *
   *   // Should select the first result
   *   expect(onSelect).toHaveBeenCalled();
   * });
   */

  test.skip('Component integration tests would go here', () => {
    // Integration tests would be implemented with React Testing Library
    // See comments above for example test patterns
  });
});
