import type { User, UserProfile, ApiResponse } from '../../types';
import { apiFetch } from '../api-client';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export const authService = {
  async verifyMagicLink(token: string): Promise<TokenResponse> {
    // Always use relative URL - nginx proxies /api/* to backend in production
    // In development, Vite dev server can proxy /api/* to backend
    const apiPath = `/api/auth/verify?token=${token}`;
    
    try {
      const response = await fetch(apiPath, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: Failed to verify magic link`;
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch {
          // If response is not JSON, use status text
          errorMessage = response.statusText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      return response.json();
    } catch (error) {
      // Re-throw if it's already an Error with a message
      if (error instanceof Error) {
        throw error;
      }
      // Handle network errors (fetch failures)
      throw new Error('Błąd połączenia z serwerem. Sprawdź połączenie internetowe.');
    }
  },

  async refreshToken(): Promise<TokenResponse> {
    if (typeof window === 'undefined') {
      throw new Error('Cannot refresh token on server side');
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    // Always use relative URL - nginx proxies /api/* to backend in production
    // In development, Vite dev server can proxy /api/* to backend
    const refreshPath = `/api/auth/refresh`;
    
    const response = await fetch(refreshPath, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      const error = await response.json();
      // If refresh fails, clear session
      this.clearSession();
      throw new Error(error.detail || 'Failed to refresh token');
    }

    const tokens = await response.json();
    this.setSession(tokens);
    return tokens;
  },

  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  },

  setSession(tokens: TokenResponse) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(tokens.user));
      // Set cookie for Astro middleware (optional, but good for SSR)
      // Access token expires in 15 minutes, cookie max-age should match
      document.cookie = `access_token=${tokens.access_token}; path=/; max-age=900; SameSite=Strict`;
    }
  },

  clearSession() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }
  },

  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },

  /**
   * Pobiera profil użytkownika wraz ze statystykami użycia
   * @returns Profil użytkownika z informacjami o limicie paragonów
   */
  async getUserProfile(): Promise<UserProfile> {
    try {
      const response = await apiFetch('/api/users/me');

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Brak autoryzacji');
        }
        throw new Error(`API error: ${response.status}`);
      }

      const data: ApiResponse<UserProfile> | UserProfile = await response.json();

      // Handle both wrapped ApiResponse and direct response for flexibility
      if ('data' in data && 'success' in data) {
        if (!data.success) {
          throw new Error(data.message || 'Failed to fetch user profile');
        }
        return data.data;
      }

      return data as UserProfile;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  },
};
