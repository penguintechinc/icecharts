/**
 * Authentication fixtures for Playwright E2E tests.
 *
 * Provides extended test objects with pre-authenticated page contexts so
 * individual tests do not have to manage login flows manually.
 */

import { test as base, type Page, type BrowserContext } from '@playwright/test';
import * as path from 'path';

const ADMIN_STORAGE_STATE = path.join(__dirname, '../.auth/admin.json');
const VIEWER_STORAGE_STATE = path.join(__dirname, '../.auth/viewer.json');

const API_URL = process.env.API_URL || 'http://localhost:5000';

// ---------------------------------------------------------------------------
// Helper — programmatic login via the API
// ---------------------------------------------------------------------------

/**
 * Log into the app programmatically and store the JWT in localStorage.
 * Use this when you need to log in as an arbitrary user inside a test.
 */
export async function loginAsUser(
  page: Page,
  email: string,
  password: string,
  baseURL = process.env.BASE_URL || 'http://localhost:3000'
): Promise<string> {
  const response = await page.request.post(`${API_URL}/api/v1/auth/login`, {
    data: { email, password },
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok()) {
    throw new Error(
      `loginAsUser failed for ${email}: HTTP ${response.status()}`
    );
  }

  const { access_token } = await response.json();

  await page.goto(`${baseURL}/login`);
  await page.evaluate(
    ({ token }) => {
      localStorage.setItem('access_token', token);
      localStorage.setItem('icecharts_auth_token', token);
    },
    { token: access_token }
  );

  await page.goto(`${baseURL}/dashboard`);
  return access_token as string;
}

// ---------------------------------------------------------------------------
// Fixture type definitions
// ---------------------------------------------------------------------------

type AuthFixtures = {
  /** Page authenticated as the admin user. */
  adminPage: Page;
  /** Page authenticated as a viewer (read-only) user. */
  viewerPage: Page;
  /** Alias for adminPage — convenient for most tests that just need auth. */
  authenticatedPage: Page;
  /** The admin browser context (useful for multi-tab scenarios). */
  adminContext: BrowserContext;
  /** The viewer browser context. */
  viewerContext: BrowserContext;
};

// ---------------------------------------------------------------------------
// Extended test with auth fixtures
// ---------------------------------------------------------------------------

export const test = base.extend<AuthFixtures>({
  adminContext: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: ADMIN_STORAGE_STATE });
    await use(context);
    await context.close();
  },

  viewerContext: async ({ browser }, use) => {
    const context = await browser.newContext({ storageState: VIEWER_STORAGE_STATE });
    await use(context);
    await context.close();
  },

  adminPage: async ({ adminContext }, use) => {
    const page = await adminContext.newPage();
    await use(page);
    await page.close();
  },

  viewerPage: async ({ viewerContext }, use) => {
    const page = await viewerContext.newPage();
    await use(page);
    await page.close();
  },

  authenticatedPage: async ({ adminPage }, use) => {
    await use(adminPage);
  },
});

export { expect } from '@playwright/test';
