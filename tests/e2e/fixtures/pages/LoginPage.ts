/**
 * Page Object Model — Login page (/login)
 *
 * Covers the email/password form, Google OAuth button, and error states.
 */

import type { Page, Locator } from '@playwright/test';
import { expect } from '@playwright/test';

export class LoginPage {
  readonly url = '/login';

  // Locators
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly googleOAuthButton: Locator;
  readonly errorMessage: Locator;
  readonly registerLink: Locator;
  readonly forgotPasswordLink: Locator;

  constructor(private readonly page: Page) {
    this.emailInput = page.getByTestId('login-email').or(
      page.getByRole('textbox', { name: /email/i })
    );
    this.passwordInput = page.getByTestId('login-password').or(
      page.getByRole('textbox', { name: /password/i }).or(
        page.locator('input[type="password"]')
      )
    );
    this.submitButton = page.getByTestId('login-submit').or(
      page.getByRole('button', { name: /sign in|log in|login/i })
    );
    this.googleOAuthButton = page.getByTestId('login-google').or(
      page.getByRole('button', { name: /google/i })
    );
    this.errorMessage = page.getByTestId('login-error').or(
      page.locator('[role="alert"]').or(
        page.locator('.error-message, .text-red-500, .text-red-400')
      )
    );
    this.registerLink = page.getByRole('link', { name: /register|sign up/i });
    this.forgotPasswordLink = page.getByRole('link', { name: /forgot/i });
  }

  /**
   * Navigate to the login page.
   */
  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await expect(this.emailInput).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Fill in credentials and submit the login form.
   */
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  /**
   * Assert that an error message containing `text` is visible.
   */
  async expectErrorMessage(text: string | RegExp): Promise<void> {
    await expect(this.errorMessage).toBeVisible();
    await expect(this.errorMessage).toContainText(text);
  }

  /**
   * Assert that the login page is currently displayed.
   */
  async expectVisible(): Promise<void> {
    await expect(this.page).toHaveURL(/\/login/);
    await expect(this.emailInput).toBeVisible();
  }
}
