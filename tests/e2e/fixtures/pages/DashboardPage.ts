/**
 * Page Object Model — Dashboard (/dashboard)
 *
 * The main landing page after login.  Shows stats cards, recent drawings,
 * and quick-create actions.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class DashboardPage {
  readonly url = '/dashboard';

  // Locators
  readonly statsCards: Locator;
  readonly recentDrawingsList: Locator;
  readonly createDrawingButton: Locator;
  readonly drawingsNavLink: Locator;
  readonly collectionsNavLink: Locator;
  readonly iceFlowsNavLink: Locator;
  readonly iceRunsNavLink: Locator;
  readonly playbooksNavLink: Locator;
  readonly welcomeHeading: Locator;

  constructor(private readonly page: Page) {
    // Stats cards — typically a grid of metric cards
    this.statsCards = page.getByTestId('dashboard-stats').or(
      page.locator('[data-testid^="stat-card"]').or(
        page.locator('.stat-card, .stats-card, [class*="StatsCard"]')
      )
    );

    // Recent drawings list
    this.recentDrawingsList = page.getByTestId('recent-drawings').or(
      page.locator('[data-testid="drawings-list"]').or(
        page.locator('.recent-drawings, [class*="RecentDrawings"]')
      )
    );

    // Create drawing quick action
    this.createDrawingButton = page.getByTestId('create-drawing-btn').or(
      page.getByRole('button', { name: /new drawing|create drawing/i }).or(
        page.getByRole('link', { name: /new drawing|create drawing/i })
      )
    );

    // Navigation links (sidebar / topbar)
    this.drawingsNavLink = page.getByRole('link', { name: /^drawings$/i });
    this.collectionsNavLink = page.getByRole('link', { name: /^collections$/i });
    this.iceFlowsNavLink = page.getByRole('link', { name: /^iceflows?$/i });
    this.iceRunsNavLink = page.getByRole('link', { name: /^iceruns?$/i });
    this.playbooksNavLink = page.getByRole('link', { name: /^playbooks?$/i });

    this.welcomeHeading = page.getByRole('heading', { name: /dashboard|welcome/i });
  }

  /**
   * Navigate to the dashboard.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/dashboard/, { timeout: 15_000 });
  }

  /**
   * Return all visible stats card elements.
   */
  async getStatsCards(): Promise<Locator> {
    return this.statsCards;
  }

  /**
   * Click the "Create Drawing" button / link.
   */
  async clickCreateDrawing(): Promise<void> {
    await this.createDrawingButton.click();
  }

  /**
   * Navigate to the Drawings list page via the sidebar link.
   */
  async navigateToDrawings(): Promise<void> {
    await this.drawingsNavLink.click();
    await expect(this.page).toHaveURL(/\/drawings/, { timeout: 10_000 });
  }

  /**
   * Navigate to the Collections list page via the sidebar link.
   */
  async navigateToCollections(): Promise<void> {
    await this.collectionsNavLink.click();
    await expect(this.page).toHaveURL(/\/collections/, { timeout: 10_000 });
  }

  /**
   * Navigate to IceFlows via the sidebar link.
   */
  async navigateToIceFlows(): Promise<void> {
    await this.iceFlowsNavLink.click();
    await expect(this.page).toHaveURL(/\/iceflows/, { timeout: 10_000 });
  }

  /**
   * Assert that the dashboard is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }
}
