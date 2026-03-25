/**
 * Page Object Model — IceRuns (/iceruns)
 *
 * Serverless function management page.  Lists functions, allows creation,
 * editing, testing, and viewing executions / schedules.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class IceRunsPage {
  readonly url = '/iceruns';

  // Locators
  readonly runsList: Locator;
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly pageHeading: Locator;
  readonly emptyState: Locator;
  readonly loadingSpinner: Locator;

  constructor(private readonly page: Page) {
    this.pageHeading = page.getByRole('heading', { name: /iceruns?|function/i });

    this.runsList = page.getByTestId('iceruns-list').or(
      page.locator('[data-testid="runs-list"]').or(
        page.locator('.iceruns-list, [class*="RunsList"]')
      )
    );

    this.createButton = page.getByTestId('create-icerun').or(
      page.getByRole('button', { name: /new function|create (function|icerun)|new icerun/i }).or(
        page.getByRole('link', { name: /new function|create (function|icerun)|new icerun/i })
      )
    );

    this.searchInput = page.getByTestId('iceruns-search').or(
      page.getByRole('searchbox').or(
        page.getByPlaceholder(/search (functions?|runs?|iceruns?)/i)
      )
    );

    this.emptyState = page.getByTestId('iceruns-empty').or(
      page.getByText(/no (functions?|runs?|iceruns?)/i)
    );

    this.loadingSpinner = page.locator('[data-testid="loading"], .loading-spinner, [class*="Spinner"]');
  }

  /**
   * Navigate to the IceRuns list page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/iceruns/, { timeout: 10_000 });
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});
  }

  /**
   * Click the "Create" button and wait for the creation form to load.
   */
  async createNew(): Promise<void> {
    await this.createButton.click();
    await expect(this.page).toHaveURL(/\/iceruns\/(create|new|[^/]+\/edit)/, { timeout: 10_000 });
  }

  /**
   * Click an IceRun entry by ID or display name.
   */
  async clickRun(idOrName: string): Promise<void> {
    const runRow = this.runsList.getByTestId(`icerun-${idOrName}`).or(
      this.runsList.getByText(idOrName, { exact: false }).first()
    );
    await runRow.click();
    await expect(this.page).toHaveURL(/\/iceruns\/[^/]+/, { timeout: 10_000 });
  }

  /**
   * Type into the search input and wait for results to refresh.
   */
  async search(term: string): Promise<void> {
    await this.searchInput.fill(term);
    await this.page.waitForTimeout(400);
  }

  /**
   * Assert that the IceRuns page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/iceruns/);
    await expect(this.pageHeading.or(this.createButton)).toBeVisible();
  }
}
