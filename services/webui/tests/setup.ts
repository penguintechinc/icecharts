/**
 * Vitest setup file for WebUI tests
 */

import { expect, afterEach, vi } from 'vitest';

/**
 * Mock global fetch API
 */
global.fetch = vi.fn();

/**
 * Mock localStorage
 */
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

/**
 * Mock sessionStorage
 */
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
});

/**
 * Reset mocks after each test
 */
afterEach(() => {
  vi.clearAllMocks();
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
});

/**
 * Custom matchers for common assertions
 */
expect.extend({
  toHaveLocalStorageValue(received: string, key: string, value: string) {
    const actualValue = localStorage.getItem(key);
    const pass = actualValue === value;

    return {
      pass,
      message: () =>
        `expected localStorage[${key}] to be ${value}, but got ${actualValue}`,
    };
  },
});

/**
 * Mock window.matchMedia
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
