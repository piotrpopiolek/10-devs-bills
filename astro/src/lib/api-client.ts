import { authService } from './services/auth';

const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api/v1';

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
  // Get access token
  const accessToken = authService.getAccessToken();

  // Prepare headers
  const headers = new Headers(options.headers);
  
  // Add Authorization header if we have a token
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
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

