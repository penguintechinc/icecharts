/**
 * Page Object Model — Admin Users page (/admin/users)
 *
 * Admin-only user management surface.  Lists all users, supports role
 * assignment, user activation/deactivation, and deletion.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export type UserRole = 'admin' | 'maintainer' | 'viewer';

export class AdminPage {
  readonly url = '/admin/users';

  // Locators
  readonly userList: Locator;
  readonly pageHeading: Locator;
  readonly inviteUserButton: Locator;
  readonly searchInput: Locator;
  readonly roleFilter: Locator;
  readonly loadingSpinner: Locator;
  readonly emptyState: Locator;

  constructor(private readonly page: Page) {
    this.pageHeading = page.getByRole('heading', { name: /users?|user management/i });

    this.userList = page.getByTestId('admin-users-list').or(
      page.locator('[data-testid="users-list"]').or(
        page.locator('table tbody, .users-list, [class*="UsersList"]')
      )
    );

    this.inviteUserButton = page.getByTestId('invite-user').or(
      page.getByRole('button', { name: /invite|add user/i })
    );

    this.searchInput = page.getByTestId('users-search').or(
      page.getByRole('searchbox').or(
        page.getByPlaceholder(/search users?/i)
      )
    );

    this.roleFilter = page.getByTestId('role-filter').or(
      page.getByRole('combobox', { name: /role/i })
    );

    this.loadingSpinner = page.locator('[data-testid="loading"], .loading-spinner, [class*="Spinner"]');

    this.emptyState = page.getByTestId('users-empty').or(
      page.getByText(/no users? found/i)
    );
  }

  /**
   * Navigate to the Admin Users page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/admin\/users/, { timeout: 10_000 });
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});
  }

  /**
   * Click a user row to navigate to their detail/edit page.
   */
  async clickUser(idOrEmail: string): Promise<void> {
    const userRow = this.userList.getByTestId(`user-${idOrEmail}`).or(
      this.userList.getByText(idOrEmail, { exact: false }).first()
    );
    await userRow.click();
  }

  /**
   * Change the role for a specific user.
   *
   * Finds the role dropdown within the row identified by `userId` (a data-testid
   * suffix, email, or display name) and selects the given role.
   */
  async changeRole(userId: string, role: UserRole): Promise<void> {
    // Locate the row for this user
    const userRow = this.userList.getByTestId(`user-${userId}`).or(
      this.userList.locator(`tr:has-text("${userId}")`)
    );

    // Find the role select/dropdown within the row
    const roleSelect = userRow.getByRole('combobox').or(
      userRow.getByTestId('role-select')
    );

    await roleSelect.selectOption(role);

    // Some UIs require a separate "Save" or "Apply" button within the row
    const saveRowButton = userRow.getByRole('button', { name: /save|apply/i });
    const hasSaveButton = await saveRowButton.isVisible().catch(() => false);
    if (hasSaveButton) {
      await saveRowButton.click();
    }
  }

  /**
   * Filter users by role using the role filter dropdown.
   */
  async filterByRole(role: UserRole | 'all'): Promise<void> {
    await this.roleFilter.selectOption(role);
    await this.page.waitForTimeout(300);
  }

  /**
   * Type in the search box to filter the user list.
   */
  async search(term: string): Promise<void> {
    await this.searchInput.fill(term);
    await this.page.waitForTimeout(400);
  }

  /**
   * Assert that the Admin Users page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/admin\/users/);
    await expect(this.pageHeading.or(this.userList)).toBeVisible();
  }

  /**
   * Assert that a user with the given email is visible in the list.
   */
  async expectUserVisible(email: string): Promise<void> {
    await expect(this.userList.getByText(email)).toBeVisible();
  }
}
