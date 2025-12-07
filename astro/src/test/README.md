# Frontend Tests

Testy jednostkowe (Vitest) i E2E (Playwright) dla frontendu Bills.

## Instalacja

```bash
# Zainstaluj zależności
npm install
```

## Testy jednostkowe (Vitest)

### Uruchamianie

```bash
# Wszystkie testy
npm run test

# Tryb watch
npm run test:watch

# UI mode
npm run test:ui

# Z pokryciem kodu
npm run test:coverage
```

### Struktura

```
src/
├── test/
│   ├── setup.ts          # Konfiguracja globalna
│   ├── vitest.d.ts       # Definicje typów
│   └── example.test.tsx  # Przykładowe testy
└── components/
    └── **/*.test.tsx     # Testy komponentów
```

### Przykłady

#### Test komponentu React

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('should render correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

#### Mockowanie z vi

```typescript
import { vi } from 'vitest';

// Mock funkcji
const mockFn = vi.fn();
mockFn('test');
expect(mockFn).toHaveBeenCalledWith('test');

// Spy na istniejącej funkcji
const spy = vi.spyOn(obj, 'method');
obj.method();
expect(spy).toHaveBeenCalled();
```

## Testy E2E (Playwright)

### Uruchamianie

```bash
# Wszystkie testy E2E
npm run test:e2e

# UI mode
npm run test:e2e:ui

# Debug mode
npm run test:e2e:debug
```

### Struktura

```
e2e/
├── example.spec.ts       # Przykładowe testy
└── pages/                # Page Object Model
    └── ...
```

### Przykłady

#### Podstawowy test

```typescript
import { test, expect } from '@playwright/test';

test('should load homepage', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Bills/i);
});
```

#### Page Object Model

```typescript
// e2e/pages/HomePage.ts
export class HomePage {
  constructor(private page: Page) {}
  
  async goto() {
    await this.page.goto('/');
  }
  
  async getTitle() {
    return this.page.locator('h1');
  }
}

// e2e/homepage.spec.ts
test('homepage', async ({ page }) => {
  const homePage = new HomePage(page);
  await homePage.goto();
  await expect(homePage.getTitle()).toBeVisible();
});
```

## Konfiguracja

- `vitest.config.ts`: Konfiguracja Vitest
- `playwright.config.ts`: Konfiguracja Playwright
- `src/test/setup.ts`: Globalne ustawienia testów

