import { authService } from './services/auth';

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

/**
 * Wrapper for fetch that automatically handles:
 * - Adding Authorization header with access token
 * - Refreshing token on 401 errors
 * - Retrying request after token refresh
 * - Preventing multiple simultaneous refresh attempts
 */
export async function apiFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  // Ensure URL is relative (starts with /) to prevent Mixed Content errors
  // If URL is absolute (starts with http:// or https://), it means BACKEND_URL leaked to client
  // In production, all API calls should go through nginx proxy at /api/*
  if (url.startsWith('http://') || url.startsWith('https://')) {
    console.error(`[apiFetch] ERROR: Absolute URL detected: ${url}. This should be a relative path like /api/...`);
    // Extract path from absolute URL and use relative path instead
    try {
      const urlObj = new URL(url);
      url = urlObj.pathname + urlObj.search;
      console.log(`[apiFetch] Converted to relative path: ${url}`);
    } catch (e) {
      console.error(`[apiFetch] Failed to parse URL: ${url}`, e);
      throw new Error('Invalid API URL - must be relative path');
    }
  }
  
  // Ensure URL starts with /api/
  if (!url.startsWith('/api/')) {
    console.warn(`[apiFetch] URL does not start with /api/: ${url}`);
  }

  // Get access token - retry if not available (handles race conditions after login)
  let accessToken = authService.getAccessToken();
  
  // If no token, wait a bit and retry (handles case where token was just saved)
  if (!accessToken) {
    console.log(`[apiFetch] No token found, waiting 50ms and retrying for ${url}`);
    await new Promise(resolve => setTimeout(resolve, 50));
    accessToken = authService.getAccessToken();
  }

  // Prepare headers
  const headers = new Headers(options.headers);
  
  // Add Authorization header if we have a token
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
    console.log(`[apiFetch] Adding Authorization header for ${url}`);
  } else {
    console.warn(`[apiFetch] No access token available for ${url} after retry`);
  }

  // Make initial request
  let response = await fetch(url, {
    ...options,
    headers,
  });

  // If we got 401, handle authentication error
  if (response.status === 401) {
    const refreshToken = authService.getRefreshToken();
    
    // If we have a refresh token, try to refresh
    if (refreshToken) {
      // If already refreshing, wait for that to complete
      if (isRefreshing && refreshPromise) {
        await refreshPromise;
        // Retry with new token
        const newAccessToken = authService.getAccessToken();
        if (newAccessToken) {
          headers.set('Authorization', `Bearer ${newAccessToken}`);
          response = await fetch(url, {
            ...options,
            headers,
          });
        }
        return response;
      }

      // Start refresh process
      isRefreshing = true;
      refreshPromise = (async () => {
        try {
          // Refresh token
          await authService.refreshToken();
        } catch (refreshError) {
          // If refresh fails, clear session and redirect
          authService.clearSession();
          
          // If we're on client side, redirect to home page
          if (typeof window !== 'undefined') {
            window.location.href = '/';
          }
          
          throw new Error('Session expired. Please log in again.');
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
      })();

      try {
        await refreshPromise;
        
        // Get new access token
        const newAccessToken = authService.getAccessToken();
        
        if (newAccessToken) {
          // Update Authorization header with new token
          headers.set('Authorization', `Bearer ${newAccessToken}`);
          
          // Retry original request with new token
          response = await fetch(url, {
            ...options,
            headers,
          });
        }
      } catch (refreshError) {
        // Error already handled in refreshPromise
        throw refreshError;
      }
    } else {
      // No refresh token available - session expired, clear and redirect
      authService.clearSession();
      
      // If we're on client side, redirect to home page
      if (typeof window !== 'undefined') {
        window.location.href = '/';
      }
    }
  }

  return response;
}

