/**
 * Page Object Model — IceFlows (/iceflows)
 *
 * CI/CD pipeline management page.  Lists pipelines, allows creation, editing,
 * and viewing promotions.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class IceFlowsPage {
  readonly url = '/iceflows';

  // Locators
  readonly flowsList: Locator;
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly pageHeading: Locator;
  readonly emptyState: Locator;
  readonly myApprovalsLink: Locator;
  readonly loadingSpinner: Locator;

  constructor(private readonly page: Page) {
    this.pageHeading = page.getByRole('heading', { name: /iceflows?|pipeline/i });

    this.flowsList = page.getByTestId('iceflows-list').or(
      page.locator('[data-testid="flows-list"]').or(
        page.locator('.iceflows-list, [class*="FlowsList"]')
      )
    );

    this.createButton = page.getByTestId('create-iceflow').or(
      page.getByRole('button', { name: /new (pipeline|iceflow|flow)|create/i }).or(
        page.getByRole('link', { name: /new (pipeline|iceflow|flow)|create/i })
      )
    );

    this.searchInput = page.getByTestId('iceflows-search').or(
      page.getByRole('searchbox').or(
        page.getByPlaceholder(/search (flows?|pipelines?)/i)
      )
    );

    this.emptyState = page.getByTestId('iceflows-empty').or(
      page.getByText(/no (flows?|pipelines?)/i)
    );

    this.myApprovalsLink = page.getByRole('link', { name: /my approvals/i }).or(
      page.getByTestId('my-approvals-link')
    );

    this.loadingSpinner = page.locator('[data-testid="loading"], .loading-spinner, [class*="Spinner"]');
  }

  /**
   * Navigate to the IceFlows list page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/iceflows/, { timeout: 10_000 });
    // Wait for loading to complete
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {});
  }

  /**
   * Click the "Create new IceFlow" button and wait for the editor to load.
   */
  async createNew(): Promise<void> {
    await this.createButton.click();
    await expect(this.page).toHaveURL(/\/iceflows\/(create|new|[^/]+\/edit)/, { timeout: 10_000 });
  }

  /**
   * Click a flow in the list by its ID attribute or visible name.
   */
  async clickFlow(idOrName: string): Promise<void> {
    const flowRow = this.flowsList.getByTestId(`flow-${idOrName}`).or(
      this.flowsList.getByText(idOrName, { exact: false }).first()
    );
    await flowRow.click();
    await expect(this.page).toHaveURL(/\/iceflows\/[^/]+/, { timeout: 10_000 });
  }

  /**
   * Type into the search input and wait for results to refresh.
   */
  async search(term: string): Promise<void> {
    await this.searchInput.fill(term);
    // Brief wait for debounced search to fire
    await this.page.waitForTimeout(400);
  }

  /**
   * Navigate to the My Approvals sub-page.
   */
  async gotoMyApprovals(): Promise<void> {
    await this.myApprovalsLink.click();
    await expect(this.page).toHaveURL(/\/iceflows\/my-approvals/, { timeout: 10_000 });
  }

  /**
   * Assert that the IceFlows page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/iceflows/);
    await expect(this.pageHeading.or(this.createButton)).toBeVisible();
  }
}
