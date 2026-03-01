/**
 * Page Object Model — Playbooks (/playbooks)
 *
 * IceStreams workflow/playbook management page.  Lists playbooks, supports
 * creation, editing, templates, and collections sub-pages.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class PlaybooksPage {
  readonly url = '/playbooks';

  // Locators
  readonly playbooksList: Locator;
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly pageHeading: Locator;
  readonly emptyState: Locator;
  readonly templatesLink: Locator;
  readonly collectionsLink: Locator;
  readonly loadingSpinner: Locator;

  constructor(private readonly page: Page) {
    this.pageHeading = page.getByRole('heading', { name: /playbooks?|workflow/i });

    this.playbooksList = page.getByTestId('playbooks-list').or(
      page.locator('[data-testid="playbooks-list"]').or(
        page.locator('.playbooks-list, [class*="PlaybooksList"]')
      )
    );

    this.createButton = page.getByTestId('create-playbook').or(
      page.getByRole('button', { name: /new playbook|create playbook/i }).or(
        page.getByRole('link', { name: /new playbook|create playbook/i })
      )
    );

    this.searchInput = page.getByTestId('playbooks-search').or(
      page.getByRole('searchbox').or(
        page.getByPlaceholder(/search playbooks?/i)
      )
    );

    this.emptyState = page.getByTestId('playbooks-empty').or(
      page.getByText(/no playbooks?/i)
    );

    this.templatesLink = page.getByRole('link', { name: /templates/i }).or(
      page.getByTestId('playbooks-templates-link')
    );

    this.collectionsLink = page.getByRole('link', { name: /collections/i }).or(
      page.getByTestId('playbooks-collections-link')
    );

    this.loadingSpinner = page.locator('[data-testid="loading"], .loading-spinner, [class*="Spinner"]');
  }

  /**
   * Navigate to the Playbooks list page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/playbooks/, { timeout: 10_000 });
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});
  }

  /**
   * Click the "Create new playbook" button.
   */
  async createNew(): Promise<void> {
    await this.createButton.click();
    await expect(this.page).toHaveURL(/\/playbooks\/(new|[^/]+\/edit)/, { timeout: 10_000 });
  }

  /**
   * Click a playbook entry by ID or visible name.
   */
  async clickPlaybook(idOrName: string): Promise<void> {
    const playbookRow = this.playbooksList.getByTestId(`playbook-${idOrName}`).or(
      this.playbooksList.getByText(idOrName, { exact: false }).first()
    );
    await playbookRow.click();
    await expect(this.page).toHaveURL(/\/playbooks\/[^/]+/, { timeout: 10_000 });
  }

  /**
   * Type into the search input and wait for results to refresh.
   */
  async search(term: string): Promise<void> {
    await this.searchInput.fill(term);
    await this.page.waitForTimeout(400);
  }

  /**
   * Navigate to Playbook Templates sub-page.
   */
  async gotoTemplates(): Promise<void> {
    await this.templatesLink.click();
    await expect(this.page).toHaveURL(/\/playbooks\/templates/, { timeout: 10_000 });
  }

  /**
   * Navigate to Playbook Collections sub-page.
   */
  async gotoCollections(): Promise<void> {
    await this.collectionsLink.click();
    await expect(this.page).toHaveURL(/\/collections\/playbooks|\/playbooks\/collections/, { timeout: 10_000 });
  }

  /**
   * Assert that the Playbooks page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/playbooks/);
    await expect(this.pageHeading.or(this.createButton)).toBeVisible();
  }
}
