/**
 * Ensures BACKEND_URL uses HTTPS to prevent Mixed Content errors
 * Railway public domains should always use HTTPS
 */
export function ensureHttpsBackendUrl(backendUrl: string | undefined): string {
  if (!backendUrl) {
    throw new Error('BACKEND_URL is not set');
  }

  // If URL starts with http://, replace with https://
  if (backendUrl.startsWith('http://')) {
    return backendUrl.replace('http://', 'https://');
  }

  // If URL doesn't have a protocol, assume https://
  if (!backendUrl.startsWith('http://') && !backendUrl.startsWith('https://')) {
    return `https://${backendUrl}`;
  }

  return backendUrl;
}

