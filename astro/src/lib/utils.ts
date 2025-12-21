import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Get base URL without port (fixes Railway issue where port 8080 appears in URLs)
 */
export function getBaseUrl(): string {
  if (typeof window !== 'undefined') {
    // Use stored base URL from layout script if available
    const storedBase = (window as any).__BASE_URL__;
    if (storedBase) {
      return storedBase;
    }
    // Fallback: remove port if it's 8080 or 80
    const origin = window.location.origin;
    if (origin.includes(':8080') || origin.includes(':80')) {
      return origin.split(':').slice(0, 2).join(':');
    }
    return origin;
  }
  // Server-side: use environment variable
  return import.meta.env.PUBLIC_SITE_URL || '';
}
