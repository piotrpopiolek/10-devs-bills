// @ts-check
import { defineConfig } from 'astro/config';

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
// Using static output for production (nginx serves static files)
// API routes are handled by nginx proxy to backend
export default defineConfig({
  output: 'static',
  // Base path - empty for root domain, Railway handles routing
  base: '/',
  // Site URL - Railway will set this via environment variable
  // For production, this should be your Railway domain without port
  // Only set site if PUBLIC_SITE_URL is provided (Astro requires valid URL or undefined)
  ...(process.env.PUBLIC_SITE_URL && { site: process.env.PUBLIC_SITE_URL }),
  integrations: [react()],

  vite: {
    plugins: [tailwindcss()]
  }
});