import { useEffect, useState } from 'react';
import { authService } from '@/lib/services/auth';

export const VerifyView: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Trwa logowanie, proszę czekać.');

  useEffect(() => {
    async function verify() {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');

      if (!token) {
        setStatus('error');
        setMessage('Brak tokenu weryfikacyjnego.');
        return;
      }

      try {
        console.log('Verifying magic link with token:', token.substring(0, 10) + '...');
        const data = await authService.verifyMagicLink(token);
        console.log('Verification successful, setting session');
        authService.setSession(data);
        
        // Verify that token was saved before redirecting
        const savedToken = authService.getAccessToken();
        if (!savedToken) {
          throw new Error('Failed to save authentication token');
        }
        
        console.log('Token saved successfully, redirecting to dashboard');
        setStatus('success');
        setMessage('Zalogowano pomyślnie! Przekierowywanie...');
        
        // Use replace instead of href to avoid back button issues
        // Small delay to ensure localStorage is fully written
        setTimeout(() => {
          window.location.replace('/dashboard');
        }, 100);
        
      } catch (error) {
        console.error('Verification error:', error);
        setStatus('error');
        
        let errorMessage = "Nieznany błąd";
        if (error instanceof Error) {
          errorMessage = error.message;
          // If it's a fetch error, try to get more details
          if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
            errorMessage = "Błąd połączenia z serwerem. Sprawdź połączenie internetowe.";
          }
        } else if (typeof error === 'object' && error !== null) {
          errorMessage = JSON.stringify(error);
        }
        
        setMessage("Błąd logowania: " + errorMessage);
      }
    }

    verify();
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="p-8 bg-white dark:bg-gray-800 rounded-lg shadow-md max-w-md w-full text-center">
        <h2 className="text-2xl font-bold mb-4 text-gray-800 dark:text-white">Weryfikacja...</h2>
        <p 
          className={`text-gray-600 dark:text-gray-300 ${
            status === 'error' ? 'text-red-600 dark:text-red-400' : ''
          }`}
        >
          {message}
        </p>
        {status === 'loading' && (
          <div className="mt-6 flex justify-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600"></div>
          </div>
        )}
      </div>
    </div>
  );
};

