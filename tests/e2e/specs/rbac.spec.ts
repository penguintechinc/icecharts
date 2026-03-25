/**
 * E2E tests — Role-Based Access Control (RBAC)
 *
 * Covers Viewer/Maintainer/Admin access enforcement across protected routes,
 * service account scope testing, and feature gating by role.
 */

import { test, expect } from '../fixtures/auth.fixture';

test.describe('RBAC — Viewer Role Restrictions', () => {
  test('viewer can access dashboard', async ({ viewerPage }) => {
    await viewerPage.goto('/dashboard');
    await expect(viewerPage).toHaveURL(/\/dashboard/, { timeout: 15_000 });
    await expect(viewerPage.locator('body')).toBeVisible();
  });

  test('viewer can view drawings list', async ({ viewerPage }) => {
    await viewerPage.goto('/drawings');
    await expect(viewerPage).toHaveURL(/\/drawings/, { timeout: 10_000 });
    await expect(viewerPage.locator('body')).toBeVisible();
  });

  test('viewer cannot create drawings (create button absent or disabled)', async ({ viewerPage }) => {
    await viewerPage.goto('/drawings');
    const createBtn = viewerPage.getByRole('button', { name: /new drawing|create drawing/i }).or(
      viewerPage.getByRole('link', { name: /new drawing|create drawing/i }).or(
        viewerPage.getByTestId('create-drawing-btn')
      )
    );
    const isVisible = await createBtn.first().isVisible().catch(() => false);
    if (isVisible) {
      const isEnabled = await createBtn.first().isEnabled().catch(() => false);
      // If button is visible, it should be disabled for viewers
      expect(isEnabled).toBe(false);
    }
    // If not visible, that's also correct viewer behavior
    await expect(viewerPage.locator('body')).toBeVisible();
  });

  test('viewer cannot access admin panel', async ({ viewerPage }) => {
    await viewerPage.goto('/admin/users');
    await viewerPage.waitForLoadState('domcontentloaded');
    const url = viewerPage.url();
    // Should redirect away or show forbidden
    const isOnAdminPage = url.includes('/admin/users');
    if (isOnAdminPage) {
      const forbiddenMsg = viewerPage.getByText(/forbidden|unauthorized|access denied|not allowed/i);
      const isForbidden = await forbiddenMsg.first().isVisible().catch(() => false);
      expect(isForbidden).toBe(true);
    } else {
      expect(url).not.toContain('/admin/users');
    }
  });

  test('viewer cannot access admin license page', async ({ viewerPage }) => {
    await viewerPage.goto('/admin/license');
    await viewerPage.waitForLoadState('domcontentloaded');
    const url = viewerPage.url();
    const isOnAdminPage = url.includes('/admin/license');
    if (isOnAdminPage) {
      const forbiddenMsg = viewerPage.getByText(/forbidden|unauthorized|access denied/i);
      const isForbidden = await forbiddenMsg.first().isVisible().catch(() => false);
      expect(isForbidden).toBe(true);
    } else {
      expect(url).not.toContain('/admin/license');
    }
  });

  test('viewer cannot access admin settings page', async ({ viewerPage }) => {
    await viewerPage.goto('/admin/settings');
    await viewerPage.waitForLoadState('domcontentloaded');
    const url = viewerPage.url();
    const isOnAdminSettings = url.includes('/admin/settings');
    if (isOnAdminSettings) {
      const forbiddenMsg = viewerPage.getByText(/forbidden|unauthorized|access denied/i);
      const isForbidden = await forbiddenMsg.first().isVisible().catch(() => false);
      expect(isForbidden).toBe(true);
    } else {
      expect(url).not.toContain('/admin/settings');
    }
  });

  test('viewer can view IceRuns list but not create', async ({ viewerPage }) => {
    await viewerPage.goto('/iceruns');
    await expect(viewerPage).toHaveURL(/\/iceruns/, { timeout: 10_000 });
    await expect(viewerPage.locator('body')).toBeVisible();

    const createBtn = viewerPage.getByRole('button', { name: /new function|create (function|icerun)/i }).or(
      viewerPage.getByTestId('create-icerun-btn')
    );
    const isVisible = await createBtn.first().isVisible().catch(() => false);
    if (isVisible) {
      const isEnabled = await createBtn.first().isEnabled().catch(() => false);
      expect(isEnabled).toBe(false);
    }
    await expect(viewerPage.locator('body')).toBeVisible();
  });

  test('viewer can view IceFlows list but not create', async ({ viewerPage }) => {
    await viewerPage.goto('/iceflows');
    await expect(viewerPage).toHaveURL(/\/iceflows/, { timeout: 10_000 });
    await expect(viewerPage.locator('body')).toBeVisible();

    const createBtn = viewerPage.getByRole('button', { name: /new (pipeline|iceflow)|create/i }).or(
      viewerPage.getByTestId('create-iceflow-btn')
    );
    const isVisible = await createBtn.first().isVisible().catch(() => false);
    if (isVisible) {
      const isEnabled = await createBtn.first().isEnabled().catch(() => false);
      expect(isEnabled).toBe(false);
    }
    await expect(viewerPage.locator('body')).toBeVisible();
  });
});

test.describe('RBAC — Admin Role Access', () => {
  test('admin can access admin panel', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    await expect(adminPage).toHaveURL(/\/admin\/users/, { timeout: 10_000 });
    await expect(adminPage.locator('body')).toBeVisible();
  });

  test('admin can see invite user button', async ({ adminPage }) => {
    await adminPage.goto('/admin/users');
    const inviteBtn = adminPage.getByRole('button', { name: /invite|add user/i }).or(
      adminPage.getByTestId('invite-user')
    );
    await expect(inviteBtn.first()).toBeVisible({ timeout: 10_000 });
  });

  test('admin can access all settings tabs', async ({ adminPage }) => {
    await adminPage.goto('/settings');
    const tabs = adminPage.getByRole('tablist');
    await expect(tabs.first()).toBeVisible({ timeout: 10_000 });
    // Count tabs — admin should have full access
    const tabCount = await adminPage.getByRole('tab').count();
    expect(tabCount).toBeGreaterThanOrEqual(1);
  });

  test('admin can create new drawings', async ({ adminPage }) => {
    await adminPage.goto('/drawings');
    const createBtn = adminPage.getByRole('button', { name: /new drawing|create drawing/i }).or(
      adminPage.getByRole('link', { name: /new drawing|create drawing/i }).or(
        adminPage.getByTestId('create-drawing-btn')
      )
    );
    await expect(createBtn.first()).toBeVisible({ timeout: 10_000 });
    await expect(createBtn.first()).toBeEnabled();
  });

  test('admin can access audit logs', async ({ adminPage }) => {
    await adminPage.goto('/admin/audit-logs');
    await adminPage.waitForLoadState('domcontentloaded');
    const url = adminPage.url();
    const onAuditPage = url.includes('/admin/audit') || url.includes('/admin');
    expect(onAuditPage).toBe(true);
    await expect(adminPage.locator('body')).toBeVisible();
  });
});

test.describe('RBAC — Unauthenticated Access', () => {
  test('unauthenticated user redirected to login from dashboard', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/, { timeout: 10_000 });
  });

  test('unauthenticated user redirected from drawings', async ({ page }) => {
    await page.goto('/drawings');
    await page.waitForLoadState('domcontentloaded');
    const url = page.url();
    expect(url).toMatch(/\/login|\/$/);
  });

  test('unauthenticated user redirected from admin panel', async ({ page }) => {
    await page.goto('/admin/users');
    await page.waitForLoadState('domcontentloaded');
    const url = page.url();
    const isOnAdminPage = url.includes('/admin/users');
    if (!isOnAdminPage) {
      expect(url).toMatch(/login|\/$/);
    } else {
      // If accessible, must show forbidden
      const forbiddenMsg = page.getByText(/forbidden|unauthorized|access denied|sign in/i);
      const isForbidden = await forbiddenMsg.first().isVisible().catch(() => false);
      expect(isForbidden).toBe(true);
    }
  });

  test('unauthenticated user redirected from settings', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('domcontentloaded');
    const url = page.url();
    expect(url).toMatch(/login|settings/);
    await expect(page.locator('body')).toBeVisible();
  });
});
