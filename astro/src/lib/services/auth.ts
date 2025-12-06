import type { User } from '../../types';

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

const API_URL = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const authService = {
  async verifyMagicLink(token: string): Promise<TokenResponse> {
    const response = await fetch(`${API_URL}/auth/verify?token=${token}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to verify magic link');
    }

    return response.json();
  },

  setSession(tokens: TokenResponse) {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);
      localStorage.setItem('user', JSON.stringify(tokens.user));
      // Set cookie for Astro middleware (optional, but good for SSR)
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
  }
};
