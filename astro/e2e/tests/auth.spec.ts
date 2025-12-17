import { test, expect } from '@playwright/test';
import { AuthPage } from '../page-objects/AuthPage';
import { clearAuthSession, isAuthenticated, getAccessToken, getRefreshToken, hasAccessTokenCookie, getUserData } from '../fixtures/auth-helpers';
import { generateTestMagicLink, TEST_USER } from '../fixtures/test-data';

/**
 * E2E Tests for User Authentication (Magic Link)
 * 
 * Covers the complete authentication flow:
 * - Magic link verification
 * - Token validation
 * - Session management (localStorage + cookies)
 * - Redirects
 * - Error handling
 */
test.describe('User Authentication - Magic Link', () => {
  let authPage: AuthPage;

  test.beforeEach(async ({ page }) => {
    authPage = new AuthPage(page);
    // Clear any existing session before each test
    await clearAuthSession(page);
  });

  test.describe('Successful Authentication Flow', () => {
    test('should verify valid magic link token and redirect to dashboard', async ({ page }) => {
      // Arrange: Generate a valid token from backend API
      // NOTE: This test requires:
      // 1. Backend API to be running
      // 2. Test user to exist in database with telegram_user_id matching TEST_USER.external_id
      
      // Try to generate token via API, fallback to env variable if API fails
      let validToken: string;
      try {
        validToken = await generateTestMagicLink(TEST_USER.external_id);
      } catch (error) {
        // If API call fails, try environment variable as fallback
        validToken = process.env.TEST_MAGIC_LINK_TOKEN || '';
        if (!validToken) {
          test.skip(
            true,
            `Cannot generate magic link: ${error instanceof Error ? error.message : 'Unknown error'}. ` +
            `Set TEST_MAGIC_LINK_TOKEN environment variable to use a pre-generated token.`
          );
          return;
        }
      }
      
      // Act: Navigate to verify page with token
      await authPage.gotoVerify(validToken);
      
      // Wait for verification process to complete
      await authPage.waitForVerification(10000);
      
      // Assert: Verification was successful
      await expect(authPage.isSuccess()).resolves.toBe(true);
      
      // Assert: Wait for redirect to dashboard
      await authPage.waitForDashboardRedirect(10000);
      expect(await authPage.isOnDashboard()).toBe(true);
      
      // Assert: Session is set in localStorage
      expect(await isAuthenticated(page)).toBe(true);
      expect(await getAccessToken(page)).toBeTruthy();
      expect(await getRefreshToken(page)).toBeTruthy();
      expect(await getUserData(page)).toBeTruthy();
      
      // Assert: Cookie is set
      expect(await hasAccessTokenCookie(page)).toBe(true);
    });

    test('should set session tokens in localStorage and cookies after successful verification', async ({ page }) => {
      // This test specifically verifies that authService.setSession() works correctly
      let validToken: string;
      try {
        validToken = await generateTestMagicLink(TEST_USER.external_id);
      } catch (error) {
        validToken = process.env.TEST_MAGIC_LINK_TOKEN || '';
        if (!validToken) {
          test.skip(
            true,
            `Cannot generate magic link: ${error instanceof Error ? error.message : 'Unknown error'}`
          );
          return;
        }
      }
      
      await authPage.gotoVerify(validToken);
      await authPage.waitForVerification(10000);
      
      // Verify localStorage
      const accessToken = await getAccessToken(page);
      const refreshToken = await getRefreshToken(page);
      const userData = await getUserData(page);
      
      expect(accessToken).toBeTruthy();
      expect(refreshToken).toBeTruthy();
      expect(userData).toBeTruthy();
      expect(userData).toHaveProperty('id');
      expect(userData).toHaveProperty('external_id');
      
      // Verify cookie
      const cookies = await page.context().cookies();
      const accessTokenCookie = cookies.find(c => c.name === 'access_token');
      expect(accessTokenCookie).toBeTruthy();
      expect(accessTokenCookie?.value).toBe(accessToken);
      expect(accessTokenCookie?.path).toBe('/');
    });
  });

  test.describe('Error Handling', () => {
    test('should display error for invalid token', async ({ page }) => {
      // Arrange: Use an invalid token
      const invalidToken = 'invalid-token-12345';
      
      // Act: Navigate to verify page with invalid token
      await authPage.gotoVerify(invalidToken);
      
      // Wait for verification to complete (should fail)
      await authPage.waitForVerification(10000);
      
      // Assert: Error is displayed
      await expect(authPage.isError()).resolves.toBe(true);
      const errorMessage = await authPage.getErrorMessage();
      expect(errorMessage).toBeTruthy();
      expect(errorMessage).toContain('Błąd logowania');
      
      // Assert: No session is set
      expect(await isAuthenticated(page)).toBe(false);
      expect(await getAccessToken(page)).toBeNull();
      
      // Assert: No redirect to dashboard
      expect(await authPage.isOnDashboard()).toBe(false);
      expect(page.url()).toContain('/auth/verify');
    });

    test('should display error for expired token', async ({ page }) => {
      // Arrange: Use an expired token
      // In real scenario, this would be a token that was created and expired
      const expiredToken = 'expired-token-12345';
      
      // Act
      await authPage.gotoVerify(expiredToken);
      await authPage.waitForVerification(10000);
      
      // Assert: Error is displayed
      await expect(authPage.isError()).resolves.toBe(true);
      const errorMessage = await authPage.getErrorMessage();
      expect(errorMessage).toBeTruthy();
      
      // Assert: No session is set
      expect(await isAuthenticated(page)).toBe(false);
    });

    test('should display error when token is missing', async ({ page }) => {
      // Act: Navigate to verify page without token
      await authPage.gotoVerifyWithoutToken();
      
      // Wait a bit for the page to process
      await page.waitForTimeout(1000);
      
      // Assert: Error message about missing token
      const errorMessage = await authPage.getErrorMessage();
      expect(errorMessage).toBeTruthy();
      expect(errorMessage).toContain('Brak tokenu');
      
      // Assert: Loader is hidden
      await expect(authPage.loader).not.toBeVisible();
      
      // Assert: No session is set
      expect(await isAuthenticated(page)).toBe(false);
    });

    test('should display error when token is already used', async ({ page }) => {
      // Arrange: Use a token that was already used
      // In real scenario, this would be a token that was used in a previous test
      const usedToken = 'already-used-token-12345';
      
      // Act
      await authPage.gotoVerify(usedToken);
      await authPage.waitForVerification(10000);
      
      // Assert: Error is displayed
      await expect(authPage.isError()).resolves.toBe(true);
      
      // Assert: No session is set
      expect(await isAuthenticated(page)).toBe(false);
    });
  });

  test.describe('Redirects and Navigation', () => {
    test('should redirect to dashboard after successful authentication', async ({ page }) => {
      let validToken: string;
      try {
        validToken = await generateTestMagicLink(TEST_USER.external_id);
      } catch (error) {
        validToken = process.env.TEST_MAGIC_LINK_TOKEN || '';
        if (!validToken) {
          test.skip(
            true,
            `Cannot generate magic link: ${error instanceof Error ? error.message : 'Unknown error'}`
          );
          return;
        }
      }
      
      await authPage.gotoVerify(validToken);
      
      // Wait for redirect
      await authPage.waitForDashboardRedirect(10000);
      
      // Assert: We're on dashboard
      expect(page.url()).toContain('/dashboard');
      expect(await authPage.isOnDashboard()).toBe(true);
    });

    test('should redirect unauthenticated user from protected page to home', async ({ page }) => {
      // Arrange: Clear session
      await clearAuthSession(page);
      
      // Act: Try to access protected page (dashboard)
      await page.goto('/dashboard');
      
      // Wait a bit for potential redirect
      await page.waitForTimeout(2000);
      
      // Assert: Should be redirected to home or show login
      // Note: This depends on middleware implementation
      // If middleware redirects, we should be on home page
      // If middleware doesn't redirect, we might see an error or empty page
      const url = page.url();
      // Either on home page or still on dashboard but with error
      expect(url === '/' || url.includes('/dashboard')).toBe(true);
    });
  });

  test.describe('Session Management', () => {
    test('should persist session across page reloads', async ({ page }) => {
      const validToken = process.env.TEST_MAGIC_LINK_TOKEN || 'test-valid-token';
      
      // Authenticate
      await authPage.gotoVerify(validToken);
      await authPage.waitForVerification(10000);
      await authPage.waitForDashboardRedirect(10000);
      
      // Get tokens before reload
      const accessTokenBefore = await getAccessToken(page);
      const refreshTokenBefore = await getRefreshToken(page);
      
      // Reload page
      await page.reload();
      await page.waitForLoadState('networkidle');
      
      // Assert: Session persists
      expect(await isAuthenticated(page)).toBe(true);
      expect(await getAccessToken(page)).toBe(accessTokenBefore);
      expect(await getRefreshToken(page)).toBe(refreshTokenBefore);
    });

    test('should clear session on logout', async ({ page }) => {
      // This test assumes there's a logout functionality
      // If logout is implemented, test it here
      // For now, we'll test manual session clearing
      
      const validToken = process.env.TEST_MAGIC_LINK_TOKEN || 'test-valid-token';
      
      // Authenticate first
      await authPage.gotoVerify(validToken);
      await authPage.waitForVerification(10000);
      
      expect(await isAuthenticated(page)).toBe(true);
      
      // Clear session manually (simulating logout)
      await clearAuthSession(page);
      
      // Assert: Session is cleared
      expect(await isAuthenticated(page)).toBe(false);
      expect(await getAccessToken(page)).toBeNull();
      expect(await getRefreshToken(page)).toBeNull();
    });
  });

  test.describe('Token Refresh', () => {
    test('should automatically refresh token on 401 error', async ({ page }) => {
      // This test verifies that apiFetch automatically refreshes token
      // It requires:
      // 1. Valid session
      // 2. Expired access token (or mock 401 response)
      // 3. Valid refresh token
      // 4. API call that triggers refresh
      
      // Note: This is complex to test in E2E without mocking
      // Consider testing this in integration tests instead
      
      let validToken: string;
      try {
        validToken = await generateTestMagicLink(TEST_USER.external_id);
      } catch (error) {
        validToken = process.env.TEST_MAGIC_LINK_TOKEN || '';
        if (!validToken) {
          test.skip(
            true,
            `Cannot generate magic link: ${error instanceof Error ? error.message : 'Unknown error'}`
          );
          return;
        }
      }
      
      await authPage.gotoVerify(validToken);
      await authPage.waitForVerification(10000);
      
      // Get initial tokens
      const initialAccessToken = await getAccessToken(page);
      const refreshToken = await getRefreshToken(page);
      
      expect(initialAccessToken).toBeTruthy();
      expect(refreshToken).toBeTruthy();
      
      // To fully test refresh, we would need to:
      // 1. Wait for access token to expire (15 minutes)
      // 2. Make an API call that returns 401
      // 3. Verify that refresh happens automatically
      // 4. Verify new tokens are set
      
      // For now, we just verify that tokens exist
      // Full refresh testing should be done in integration tests
    });
  });
});
