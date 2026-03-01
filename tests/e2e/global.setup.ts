/**
 * Global setup for Playwright E2E tests.
 *
 * Authenticates as admin and viewer users via the API and saves browser storage
 * state so individual tests can reuse authenticated sessions without re-logging in.
 *
 * Storage state files are saved to .auth/ (git-ignored).
 */

import { test as setup, expect, request } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const API_URL = process.env.API_URL || 'http://localhost:5000';

const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL || 'admin@icecharts.local';
const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD || 'AdminPass123!';

const VIEWER_EMAIL = process.env.TEST_VIEWER_EMAIL || 'viewer@icecharts.local';
const VIEWER_PASSWORD = process.env.TEST_VIEWER_PASSWORD || 'ViewerPass123!';

const AUTH_DIR = path.join(__dirname, '.auth');
const ADMIN_AUTH_FILE = path.join(AUTH_DIR, 'admin.json');
const VIEWER_AUTH_FILE = path.join(AUTH_DIR, 'viewer.json');

/**
 * Authenticate against the API and return JWT access_token.
 */
async function getApiToken(email: string, password: string): Promise<string> {
  const apiContext = await request.newContext({ baseURL: API_URL });
  const response = await apiContext.post('/api/v1/auth/login', {
    data: { email, password },
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(
      `Login failed for ${email}: HTTP ${response.status()} — ${body}`
    );
  }

  const body = await response.json();
  await apiContext.dispose();
  return body.access_token as string;
}

/**
 * Build a Playwright storageState object that injects a JWT token into
 * localStorage so the React app's authStore picks it up on load.
 */
function buildStorageState(token: string, origins: string[]) {
  return {
    cookies: [],
    origins: origins.map((origin) => ({
      origin,
      localStorage: [
        { name: 'access_token', value: token },
        { name: 'icecharts_auth_token', value: token },
      ],
    })),
  };
}

setup('authenticate as admin', async ({ page }) => {
  // Ensure .auth directory exists
  if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
  }

  // Obtain API token
  const token = await getApiToken(ADMIN_EMAIL, ADMIN_PASSWORD);

  // Navigate to login page, inject token into localStorage, then verify we land
  // on the dashboard — this ensures cookies and session storage are also set.
  await page.goto(`${BASE_URL}/login`);

  await page.evaluate(
    ({ accessToken }) => {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('icecharts_auth_token', accessToken);
    },
    { accessToken: token }
  );

  // Reload to trigger the app's auth initialisation
  await page.goto(`${BASE_URL}/dashboard`);

  // Wait for a recognisable authenticated element
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });

  // Save storageState (cookies + localStorage)
  await page.context().storageState({ path: ADMIN_AUTH_FILE });
  console.log(`Admin auth state saved to ${ADMIN_AUTH_FILE}`);
});

setup('authenticate as viewer', async ({ page }) => {
  if (!fs.existsSync(AUTH_DIR)) {
    fs.mkdirSync(AUTH_DIR, { recursive: true });
  }

  let token: string;

  try {
    token = await getApiToken(VIEWER_EMAIL, VIEWER_PASSWORD);
  } catch {
    // Viewer account may not exist in all environments — create a minimal
    // storageState with no token so viewer tests can handle missing auth
    // gracefully rather than crashing the whole suite.
    console.warn(
      `Viewer login failed; creating empty auth state at ${VIEWER_AUTH_FILE}`
    );
    const emptyState = { cookies: [], origins: [] };
    fs.writeFileSync(VIEWER_AUTH_FILE, JSON.stringify(emptyState, null, 2));
    return;
  }

  await page.goto(`${BASE_URL}/login`);

  await page.evaluate(
    ({ accessToken }) => {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('icecharts_auth_token', accessToken);
    },
    { accessToken: token }
  );

  await page.goto(`${BASE_URL}/dashboard`);
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 15_000 });

  await page.context().storageState({ path: VIEWER_AUTH_FILE });
  console.log(`Viewer auth state saved to ${VIEWER_AUTH_FILE}`);
});
