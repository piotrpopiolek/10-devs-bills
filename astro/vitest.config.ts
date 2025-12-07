import { defineConfig } from 'vitest/config';
import react from '@astrojs/react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    // Enable globals (expect, describe, it, etc.)
    globals: true,
    
    // Test environment
    environment: 'jsdom',
    
    // Setup files
    setupFiles: ['./src/test/setup.ts'],
    
    // Glob patterns for test files
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', '.astro', 'e2e'],
    
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/dist/',
        '**/.astro/',
        '**/*.astro',
      ],
    },
    
    // Global test timeout
    testTimeout: 10000,
    
    // Watch mode configuration
    watch: true,
    
    // Threads for parallel execution
    threads: true,
    
    // Type checking
    typecheck: {
      tsconfig: './tsconfig.json',
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

