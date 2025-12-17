import { Page } from '@playwright/test';

/**
 * Helper functions for authentication in E2E tests
 */

/**
 * Set authentication session in browser
 * Simulates a logged-in user by setting tokens in localStorage and cookies
 */
export async function setAuthSession(
  page: Page,
  accessToken: string,
  refreshToken: string,
  user: { id: number; external_id: number; is_active: boolean; created_at: string }
): Promise<void> {
  await page.addInitScript(
    ({ accessToken, refreshToken, user }) => {
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('user', JSON.stringify(user));
      document.cookie = `access_token=${accessToken}; path=/; max-age=900; SameSite=Strict`;
    },
    { accessToken, refreshToken, user }
  );
}

/**
 * Clear authentication session
 * Handles cases where page might not be loaded yet (e.g., about:blank)
 */
export async function clearAuthSession(page: Page): Promise<void> {
  try {
    // Only clear if we're on a valid page (not about:blank)
    const url = page.url();
    if (url && url !== 'about:blank' && !url.startsWith('about:')) {
      await page.evaluate(() => {
        try {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        } catch (e) {
          // Ignore errors if localStorage is not accessible
        }
      });
    }
    // Also clear cookies via context (works even on about:blank)
    const context = page.context();
    const cookies = await context.cookies();
    const accessTokenCookie = cookies.find(c => c.name === 'access_token');
    if (accessTokenCookie) {
      await context.clearCookies();
    }
  } catch (error) {
    // Ignore errors - session might not exist yet
  }
}

/**
 * Check if user is authenticated (has access token)
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  return await page.evaluate(() => {
    return !!localStorage.getItem('access_token');
  });
}

/**
 * Get access token from localStorage
 */
export async function getAccessToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return localStorage.getItem('access_token');
  });
}

/**
 * Get refresh token from localStorage
 */
export async function getRefreshToken(page: Page): Promise<string | null> {
  return await page.evaluate(() => {
    return localStorage.getItem('refresh_token');
  });
}

/**
 * Get user data from localStorage
 */
export async function getUserData(page: Page): Promise<any | null> {
  return await page.evaluate(() => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  });
}

/**
 * Check if access_token cookie is set
 */
export async function hasAccessTokenCookie(page: Page): Promise<boolean> {
  const cookies = await page.context().cookies();
  return cookies.some(cookie => cookie.name === 'access_token' && cookie.value);
}
