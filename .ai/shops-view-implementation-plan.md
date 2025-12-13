# Plan implementacji widoku Sklepów (Shops)

## 1. Przegląd

Widok "Sklepy" (`/shops`) służy do prezentacji listy miejsc, w których użytkownik dokonuje zakupów. Głównym celem jest umożliwienie użytkownikowi analizy częstotliwości zakupów w poszczególnych placówkach. Widok oferuje funkcjonalność przeglądania listy w formie tabelarycznej, wyszukiwania sklepów po nazwie oraz paginację wyników.

**Uwaga dotycząca danych:** Zgodnie z analizą typów (`ShopResponse` w `types.ts`), widok listy udostępnia obecnie liczbę paragonów (`bills_count`). Suma wydatków (`total_spent`) jest dostępna w typach szczegółowych, ale nie w widoku listy. Implementacja opiera się na dostępnych danych z możliwością łatwego rozszerzenia w przyszłości.

## 2. Routing widoku

- **Ścieżka:** `/shops`
- **Plik Astro:** `src/pages/shops.astro`
- **Dostęp:** Wymagana autoryzacja (chroniony przez middleware/layout).

## 3. Struktura komponentów

```text
src/pages/shops.astro (Layout Wrapper)
└── ShopsView (React Container - client:load)
    ├── ShopsToolbar (Search & Filters)
    │   └── Input (Shadcn)
    ├── ShopsTable (Data Display)
    │   ├── Table (Shadcn)
    │   └── Skeleton (Loading State)
    └── Pagination (Navigation)
```

## 4. Szczegóły komponentów

### `src/pages/shops.astro`

- **Opis:** Główny punkt wejścia. Odpowiada za renderowanie layoutu aplikacji i osadzenie aplikacji Reactowej.
- **Rola:** Layout, SEO, przekazanie wstępnych danych (opcjonalnie).
- **Elementy:** `Layout` (główny layout aplikacji), `ShopsView`.

### `src/components/shops/ShopsView.tsx`

- **Opis:** Główny kontener stanu (Smart Component).
- **Zadania:**
  - Zarządzanie stanem: `page`, `search`, `data`, `loading`.
  - Komunikacja z API (poprzez hook).
  - Przekazywanie danych do komponentów prezentacyjnych.
- **Typy:** Używa `ShopListResponse` i `ShopResponse`.

### `src/components/shops/ShopsToolbar.tsx`

- **Opis:** Pasek narzędziowy nad tabelą.
- **Elementy:** Input wyszukiwania.
- **Interakcje:**
  - `onSearch`: callback wywoływany po zmianie wartości w inpucie (z debounce).
- **Propsy:** `searchTerm: string`, `onSearchChange: (value: string) => void`.

### `src/components/shops/ShopsTable.tsx`

- **Opis:** Komponent prezentacyjny wyświetlający dane.
- **Kolumny tabeli:**
  1. **Nazwa sklepu** (`name`) - pogrubiona, główna informacja.
  2. **Adres** (`address`) - opcjonalnie, ukrywany na mobile jeśli długi.
  3. **Liczba paragonów** (`bills_count`) - wyrównana do prawej, badge lub tekst.
  4. **Akcje** (opcjonalnie) - np. link do szczegółów.
- **Stan ładowania:** Wyświetla `Skeleton` wierszy tabeli, gdy `isLoading === true`.
- **Stan pusty:** Wyświetla komunikat "Brak sklepów", gdy lista jest pusta.
- **Propsy:** `shops: ShopResponse[]`, `isLoading: boolean`.

## 5. Typy

Wykorzystujemy istniejące typy z `src/types.ts`. Nie ma potrzeby tworzenia nowych definicji DTO, ale warto zdefiniować propsy komponentów.

```typescript
// Import z src/types.ts
import type { ShopResponse, PaginationMeta } from '@/types';

// Lokalne interfejsy propsów
interface ShopsTableProps {
  data: ShopResponse[];
  isLoading: boolean;
}

interface ShopsToolbarProps {
  searchTerm: string;
  onSearch: (value: string) => void;
}
```

## 6. Zarządzanie stanem

Stan będzie zarządzany lokalnie w komponencie `ShopsView` przy użyciu `useState` oraz customowego hooka `useShops`.

**Struktura stanu:**

- `page`: number (domyślnie 1)
- `search`: string (domyślnie "")
- `debouncedSearch`: string (opóźniona wartość search)

**Custom Hook `useShops`:**

```typescript
const useShops = (page: number, search: string) => {
  // Logika fetchowania danych z API
  // Zwraca: { data: ShopResponse[], meta: PaginationMeta, isLoading: boolean, error: any }
};
```

## 7. Integracja API

**Endpoint:** `GET /shops` (zgodnie z `api-plan.md`)

**Parametry zapytania (Query Params):**

- `page`: numer strony (z offsetu i limitu). API przyjmuje `skip` i `limit`, więc frontend musi to przeliczyć: `skip = (page - 1) * limit`.
- `limit`: stała wartość (np. 10 lub 20).
- `search`: ciąg znaków do filtrowania.

**Mapowanie odpowiedzi:**
API zwraca obiekt zgodny z `ShopListResponse` (`items`/`shops`, `total`, `pagination`). Należy upewnić się, że mapujemy odpowiedź na format oczekiwany przez tabelę.

## 8. Interakcje użytkownika

1.  **Wejście na stronę:** Ładowanie domyślnej listy (strona 1, brak filtrów).
2.  **Wpisanie frazy w wyszukiwarkę:**
    - Zmiana stanu `search` (natychmiastowa aktualizacja inputa).
    - Debounce (np. 500ms).
    - Reset `page` do 1.
    - Wywołanie API z nowym parametrem `search`.
3.  **Zmiana strony:**
    - Kliknięcie w paginację.
    - Zmiana stanu `page`.
    - Wywołanie API z nowym `skip`.
    - Przewinięcie widoku do góry (opcjonalne UX).

## 9. Warunki i walidacja

- **Wyszukiwanie:** Minimalna długość frazy to zazwyczaj 2-3 znaki (lub brak limitu, API decyduje). W UI pozwalamy wpisywać od razu.
- **Paginacja:** Przycisk "Poprzednia" nieaktywny na stronie 1. Przycisk "Następna" nieaktywny, gdy `page >= totalPages`.
- **Dostępność danych:** Jeśli pole `address` jest `null`, wyświetlamy placeholder (np. "-") lub ukrywamy.

## 10. Obsługa błędów

- **Błąd pobierania danych:** Wyświetlenie komunikatu o błędzie (np. komponent `Alert` z Shadcn lub `toast`) oraz przycisku "Spróbuj ponownie".
- **Pusta lista:** Jeśli API zwróci pustą tablicę, wyświetlamy komponent `EmptyState` z informacją "Nie znaleziono sklepów spełniających kryteria".

## 11. Kroki implementacji

1.  **Przygotowanie API Clienta:**
    - Upewnij się, że istnieje funkcja w serwisie API (np. `api.shops.list()`) obsługująca parametry `search`, `skip`, `limit`.
2.  **Stworzenie Hooka `useShops`:**
    - Implementacja `useEffect` do pobierania danych przy zmianie zależności.
    - Obsługa stanów `loading`, `error`.
3.  **Implementacja Komponentów UI (Dumb):**
    - Stwórz `ShopsToolbar` z inputem.
    - Stwórz `ShopsTable` używając komponentów `Table` z `shadcn/ui`. Zadbaj o wersję responsywną.
4.  **Implementacja `ShopsView` (Smart):**
    - Połącz hooka z komponentami UI.
    - Zaimplementuj logikę `debounce` dla wyszukiwania.
    - Obsłuż paginację.
5.  **Integracja ze stroną Astro:**
    - Dodaj `ShopsView` do `src/pages/shops.astro`.
6.  **Weryfikacja:**
    - Sprawdź działanie wyszukiwania.
    - Sprawdź paginację.
    - Sprawdź zachowanie przy braku danych i błędach API.
