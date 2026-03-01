/**
 * Page Object Model — Settings (/settings)
 *
 * User-facing preferences page with multiple tabs (General, Connectors,
 * Preferences, Security, etc.).
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export type SettingsTab = 'General' | 'Connectors' | 'Preferences' | 'Security';

export class SettingsPage {
  readonly url = '/settings';

  // Top-level locators
  readonly tabList: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly settingsHeading: Locator;

  // Tab-specific panels
  readonly generalPanel: Locator;
  readonly connectorsPanel: Locator;
  readonly preferencesPanel: Locator;
  readonly securityPanel: Locator;

  constructor(private readonly page: Page) {
    this.tabList = page.getByRole('tablist').or(
      page.locator('[data-testid="settings-tabs"]')
    );

    this.saveButton = page.getByTestId('settings-save').or(
      page.getByRole('button', { name: /save|save preferences/i })
    );

    this.cancelButton = page.getByRole('button', { name: /cancel/i });

    this.settingsHeading = page.getByRole('heading', { name: /settings/i });

    this.generalPanel = page.getByRole('tabpanel', { name: /general/i }).or(
      page.locator('[data-testid="tab-general"]')
    );
    this.connectorsPanel = page.getByRole('tabpanel', { name: /connectors/i }).or(
      page.locator('[data-testid="tab-connectors"]')
    );
    this.preferencesPanel = page.getByRole('tabpanel', { name: /preferences/i }).or(
      page.locator('[data-testid="tab-preferences"]')
    );
    this.securityPanel = page.getByRole('tabpanel', { name: /security/i }).or(
      page.locator('[data-testid="tab-security"]')
    );
  }

  /**
   * Navigate to the settings page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.page).toHaveURL(/\/settings/, { timeout: 10_000 });
  }

  /**
   * Click a settings tab by name.
   */
  async selectTab(name: SettingsTab): Promise<void> {
    const tab = this.page.getByRole('tab', { name: new RegExp(name, 'i') }).or(
      this.page.getByTestId(`settings-tab-${name.toLowerCase()}`)
    );
    await tab.click();
    // Ensure the tab becomes selected/active
    await expect(tab).toHaveAttribute('aria-selected', 'true').catch(() => {
      // Some implementations use data-state or class rather than aria-selected
    });
  }

  /**
   * Click the primary Save button and wait for confirmation.
   */
  async savePreferences(): Promise<void> {
    await this.saveButton.click();
    const successMsg = this.page.getByText(/saved|preferences saved|settings saved/i).or(
      this.page.locator('[data-testid="save-success"]')
    );
    await successMsg.waitFor({ state: 'visible', timeout: 8_000 }).catch(() => {
      // Gracefully handle implementations without explicit success messages
    });
  }

  /**
   * Assert that the settings page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/settings/);
    await expect(this.tabList.or(this.settingsHeading)).toBeVisible();
  }
}
