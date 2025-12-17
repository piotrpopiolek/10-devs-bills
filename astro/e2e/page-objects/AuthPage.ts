import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Authentication pages
 * Covers magic link verification and authentication flow
 */
export class AuthPage {
  readonly page: Page;
  
  // Locators for verify page
  readonly statusMessage: Locator;
  readonly loader: Locator;
  readonly heading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.statusMessage = page.locator('#status-message');
    this.loader = page.locator('#loader');
    this.heading = page.locator('h2');
  }

  /**
   * Navigate to verify page with token
   */
  async gotoVerify(token: string): Promise<void> {
    await this.page.goto(`/auth/verify?token=${token}`);
  }

  /**
   * Navigate to verify page without token
   */
  async gotoVerifyWithoutToken(): Promise<void> {
    await this.page.goto('/auth/verify');
  }

  /**
   * Wait for verification to complete (success or error)
   */
  async waitForVerification(timeout: number = 5000): Promise<void> {
    // Wait for page to load first
    await this.page.waitForLoadState('networkidle', { timeout });
    
    // Wait for loader to disappear or status message to change
    try {
      await Promise.race([
        this.loader.waitFor({ state: 'hidden', timeout }),
        this.statusMessage.waitFor({ state: 'visible', timeout }),
      ]);
    } catch {
      // If loader doesn't exist or is already hidden, just wait for status message
      await this.statusMessage.waitFor({ state: 'visible', timeout });
    }
    
    // Give a bit more time for any async operations
    await this.page.waitForTimeout(1000);
  }

  /**
   * Check if verification was successful
   */
  async isSuccess(): Promise<boolean> {
    try {
      const message = await this.statusMessage.textContent();
      return message?.includes('Zalogowano pomyślnie') ?? false;
    } catch {
      return false;
    }
  }

  /**
   * Check if verification failed
   */
  async isError(): Promise<boolean> {
    try {
      const message = await this.statusMessage.textContent();
      if (!message) return false;
      return message.includes('Błąd logowania') || message.includes('Brak tokenu');
    } catch {
      return false;
    }
  }

  /**
   * Get error message text
   */
  async getErrorMessage(): Promise<string | null> {
    return await this.statusMessage.textContent();
  }

  /**
   * Wait for redirect to dashboard
   */
  async waitForDashboardRedirect(timeout: number = 5000): Promise<void> {
    await this.page.waitForURL('**/dashboard', { timeout });
  }

  /**
   * Check if user is redirected to dashboard
   */
  async isOnDashboard(): Promise<boolean> {
    return this.page.url().includes('/dashboard');
  }
}
