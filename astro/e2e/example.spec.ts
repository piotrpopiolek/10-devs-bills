import { test, expect } from '@playwright/test';

/**
 * Example E2E test using Page Object Model pattern
 * This serves as a template for future tests
 */
test.describe('Example E2E Test', () => {
  test('should load the homepage', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to load
    await expect(page).toHaveTitle(/Bills/i);
    
    // Example: Check if a key element is visible
    // await expect(page.locator('h1')).toBeVisible();
  });
});

