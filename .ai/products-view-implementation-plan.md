# Plan implementacji widoku Katalog Produktów

## 1. Przegląd

Widok "Katalog Produktów" (`/products`) umożliwia użytkownikom przeglądanie bazy wiedzy o produktach i ich kategoryzacji. Widok ma charakter **read-only** i służy do wizualizacji danych zgromadzonych przez system podczas przetwarzania paragonów. Użytkownik może przeglądać znormalizowane nazwy produktów, przypisane kategorie oraz synonimy (warianty nazw odczytane przez OCR).

Główne funkcjonalności:

- Przeglądanie listy produktów z paginacją
- Wyszukiwanie produktów po nazwie (debounced, live search)
- Filtrowanie produktów po kategorii
- Wyświetlanie synonimów produktów jako tagi/badges
- Wyświetlanie liczby użyć produktu (usage_count)
- Responsywny design (Mobile First)

## 2. Routing widoku

**Ścieżka:** `/products`

**Plik:** `astro/src/pages/products.astro`

**Struktura:**

- Strona Astro wykorzystuje Layout główny (`Layout.astro`)
- Główny komponent React `ProductsView` jest ładowany z dyrektywą `client:load` (Islands Architecture)
- Strona jest statyczna, ale komponent React zapewnia interaktywność

## 3. Struktura komponentów

```
ProductsView (React)
├── ProductsToolbar (React)
│   ├── Input (Shadcn/ui) - wyszukiwanie
│   └── Select (Shadcn/ui) - filtr kategorii
├── ProductsTable (React)
│   ├── Table (Shadcn/ui)
│   │   ├── TableHeader
│   │   │   └── TableRow z TableHead
│   │   └── TableBody
│   │       └── TableRow z TableCell
│   └── Skeleton (Shadcn/ui) - stan ładowania
└── PaginationControls (React)
    ├── Button (Shadcn/ui) - poprzednia strona
    ├── Text - informacja o stronie
    └── Button (Shadcn/ui) - następna strona
```

**Hierarchia:**

- `ProductsView` - główny kontener, zarządza stanem i logiką
- `ProductsToolbar` - pasek narzędzi z wyszukiwaniem i filtrem
- `ProductsTable` - tabela z danymi produktów
- `PaginationControls` - kontrolki paginacji (wbudowane w `ProductsView`)

## 4. Szczegóły komponentów

### ProductsView

**Opis komponentu:**
Główny komponent widoku odpowiedzialny za zarządzanie stanem, pobieranie danych z API oraz koordynację interakcji między komponentami potomnymi. Komponent wykorzystuje custom hook `useProducts` do zarządzania danymi, paginacją i wyszukiwaniem.

**Główne elementy:**

- Kontener główny (`<div className="container mx-auto py-10 px-4 md:px-6 space-y-6">`)
- Nagłówek sekcji z tytułem i opisem
- `ProductsToolbar` - pasek narzędzi
- `ProductsTable` - tabela z danymi
- Sekcja paginacji z przyciskami nawigacji
- Obsługa błędów z możliwością ponowienia zapytania

**Obsługiwane zdarzenia:**

- `handleSearchChange(value: string)` - aktualizacja wyszukiwania
- `handleCategoryFilterChange(categoryId: number | undefined)` - zmiana filtra kategorii
- `handlePageChange(newPage: number)` - zmiana strony paginacji
- `handleRetry()` - ponowienie zapytania po błędzie

**Obsługiwana walidacja:**

- Walidacja parametrów zapytania odbywa się po stronie API endpointu
- Frontend nie wykonuje walidacji danych wejściowych (zgodnie z zasadą "trust but verify")
- Sprawdzanie, czy `skip` i `limit` są w poprawnych zakresach (obsługiwane przez hook)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `ProductResponse` - pojedynczy produkt
  - `ProductListResponse` - odpowiedź API z listą produktów
  - `ProductsQueryParams` - parametry zapytania
- Custom hook `useProducts` zwraca typ `UseProductsReturn`

**Propsy:**
Komponent nie przyjmuje żadnych propsów (jest komponentem głównym widoku).

### ProductsToolbar

**Opis komponentu:**
Komponent paska narzędzi zawierający pole wyszukiwania oraz filtr kategorii. Zapewnia interfejs do filtrowania i wyszukiwania produktów. Wyszukiwanie jest debounced (500ms) przez hook `useProducts`.

**Główne elementy:**

- Kontener flexbox (`<div className="flex items-center justify-between gap-4 py-4">`)
- `Input` (Shadcn/ui) - pole wyszukiwania z placeholderem "Szukaj produktów..."
- `Select` (Shadcn/ui) - dropdown z kategoriami (opcjonalnie, jeśli kategorie są dostępne)
- Responsywny layout (na mobile: kolumna, na desktop: wiersz)

**Obsługiwane zdarzenia:**

- `onSearchChange(value: string)` - callback wywoływany przy zmianie wartości wyszukiwania
- `onCategoryChange(categoryId: number | undefined)` - callback wywoływany przy zmianie filtra kategorii

**Obsługiwana walidacja:**

- Brak walidacji po stronie komponentu (wartości są przekazywane do rodzica)
- Maksymalna długość wyszukiwania może być ograniczona przez atrybut `maxLength` (opcjonalnie)

**Typy:**

- `ProductsToolbarProps`:
  ```typescript
  interface ProductsToolbarProps {
    searchTerm: string;
    categoryId?: number;
    categories?: Array<Pick<Category, 'id' | 'name'>>;
    onSearchChange: (value: string) => void;
    onCategoryChange: (categoryId: number | undefined) => void;
  }
  ```

**Propsy:**

- `searchTerm: string` - aktualna wartość wyszukiwania
- `categoryId?: number` - wybrana kategoria (opcjonalnie)
- `categories?: Array<Pick<Category, 'id' | 'name'>>` - lista kategorii do wyboru (opcjonalnie, jeśli filtrowanie po kategorii jest wymagane)
- `onSearchChange: (value: string) => void` - callback zmiany wyszukiwania
- `onCategoryChange: (categoryId: number | undefined) => void` - callback zmiany filtra kategorii

### ProductsTable

**Opis komponentu:**
Komponent tabeli wyświetlający listę produktów w formie tabeli. Obsługuje stany: ładowanie (skeleton), pusta lista, błąd oraz normalne wyświetlanie danych. Tabela jest responsywna - na urządzeniach mobilnych niektóre kolumny mogą być ukryte.

**Główne elementy:**

- Kontener z obramowaniem (`<div className="rounded-md border">`)
- `Table` (Shadcn/ui) - główna tabela
  - `TableHeader` z `TableRow` i `TableHead` - nagłówki kolumn
  - `TableBody` z `TableRow` i `TableCell` - wiersze danych
- `Skeleton` (Shadcn/ui) - placeholdery podczas ładowania
- Komunikat o braku danych (gdy `data.length === 0`)

**Kolumny tabeli:**

1. **Nazwa produktu** - `product.name` (zawsze widoczna)
2. **Kategoria** - `product.category.name` (ukryta na mobile: `hidden md:table-cell`)
3. **Synonimy** - lista tagów/badges z `product.synonyms` (zawsze widoczna)
4. **Liczba użyć** - `product.usage_count` (ukryta na mobile: `hidden md:table-cell`, wyrównana do prawej: `text-right`)

**Obsługiwane zdarzenia:**

- Brak interaktywnych zdarzeń (widok read-only, brak kliknięć w wiersze)

**Obsługiwana walidacja:**

- Sprawdzanie, czy `data` jest tablicą
- Sprawdzanie, czy `isLoading` jest boolean
- Obsługa pustej listy (`data.length === 0`)

**Typy:**

- `ProductsTableProps`:
  ```typescript
  interface ProductsTableProps {
    data: ProductResponse[];
    isLoading: boolean;
  }
  ```
- Wykorzystuje `ProductResponse` z `@/types`

**Propsy:**

- `data: ProductResponse[]` - tablica produktów do wyświetlenia
- `isLoading: boolean` - flaga stanu ładowania

### SynonymsList (komponent pomocniczy, opcjonalny)

**Opis komponentu:**
Komponent wyświetlający listę synonimów produktu jako tagi/badges. Jeśli synonimy nie są dostępne, wyświetla tekst "-" lub "Brak synonimów".

**Główne elementy:**

- Kontener flexbox z wrap (`<div className="flex flex-wrap gap-1">`)
- `Badge` (Shadcn/ui) - pojedynczy tag synonimu
- Maksymalna liczba wyświetlanych synonimów (np. 3) z możliwością rozszerzenia (opcjonalnie)

**Obsługiwane zdarzenia:**

- Brak (komponent prezentacyjny)

**Obsługiwana walidacja:**

- Sprawdzanie, czy `synonyms` jest tablicą
- Obsługa pustej tablicy synonimów

**Typy:**

- `SynonymsListProps`:
  ```typescript
  interface SynonymsListProps {
    synonyms: string[];
    maxVisible?: number; // opcjonalnie, domyślnie wszystkie
  }
  ```

**Propsy:**

- `synonyms: string[]` - tablica synonimów
- `maxVisible?: number` - maksymalna liczba widocznych synonimów (opcjonalnie)

## 5. Typy

### Typy istniejące (z `@/types`)

**ProductResponse:**

```typescript
interface ProductResponse
  extends Pick<Product, 'id' | 'name' | 'synonyms' | 'created_at'> {
  category: Pick<Category, 'id' | 'name'>;
  usage_count: number;
}
```

**Pola:**

- `id: number` - unikalny identyfikator produktu
- `name: string` - znormalizowana nazwa produktu
- `synonyms: string[]` - tablica synonimów (warianty nazw odczytane przez OCR)
- `created_at: string` - data utworzenia (ISO 8601)
- `category: { id: number, name: string }` - przypisana kategoria produktu
- `usage_count: number` - liczba użyć produktu w paragonach

**ProductListResponse:**

```typescript
type ProductListResponse = PaginatedResponse<ProductResponse>;
```

**Pola:**

- `items: ProductResponse[]` - tablica produktów
- `total: number` - całkowita liczba produktów (bez paginacji)
- `skip: number` - liczba pominiętych elementów
- `limit: number` - maksymalna liczba elementów na stronie

**ProductsQueryParams:**

```typescript
interface ProductsQueryParams {
  search?: string;
  category_id?: number;
  skip?: number;
  limit?: number;
}
```

**Pola:**

- `search?: string` - fraza wyszukiwania (opcjonalna)
- `category_id?: number` - ID kategorii do filtrowania (opcjonalne)
- `skip?: number` - liczba elementów do pominięcia (domyślnie 0)
- `limit?: number` - maksymalna liczba elementów (domyślnie 20)

### Typy nowe (do zdefiniowania w komponentach)

**UseProductsReturn:**

```typescript
interface UseProductsReturn {
  data: ProductResponse[];
  total: number;
  isLoading: boolean;
  error: Error | null;
  setSkip: (skip: number) => void;
  setSearch: (search: string) => void;
  setCategoryId: (categoryId: number | undefined) => void;
  skip: number;
  limit: number;
  search: string;
  categoryId?: number;
  refetch: () => Promise<void>;
}
```

**Pola:**

- `data: ProductResponse[]` - tablica produktów
- `total: number` - całkowita liczba produktów
- `isLoading: boolean` - flaga stanu ładowania
- `error: Error | null` - błąd (jeśli wystąpił)
- `setSkip: (skip: number) => void` - funkcja ustawiająca skip
- `setSearch: (search: string) => void` - funkcja ustawiająca wyszukiwanie
- `setCategoryId: (categoryId: number | undefined) => void` - funkcja ustawiająca filtr kategorii
- `skip: number` - aktualna wartość skip
- `limit: number` - aktualna wartość limit
- `search: string` - aktualna fraza wyszukiwania
- `categoryId?: number` - aktualna wybrana kategoria (opcjonalnie)
- `refetch: () => Promise<void>` - funkcja ponownego pobrania danych

## 6. Zarządzanie stanem

Widok wykorzystuje **custom hook `useProducts`** do zarządzania stanem. Hook jest zlokalizowany w `astro/src/components/hooks/useProducts.ts`.

### Stan zarządzany przez hook:

1. **Dane produktów** (`data: ProductResponse[]`) - tablica produktów z API
2. **Metadane paginacji** (`total: number`, `skip: number`, `limit: number`)
3. **Stan ładowania** (`isLoading: boolean`)
4. **Błąd** (`error: Error | null`)
5. **Wyszukiwanie** (`search: string`, `debouncedSearch: string`) - debounced z opóźnieniem 500ms
6. **Filtr kategorii** (`categoryId: number | undefined`)

### Logika hooka:

- **Debouncing wyszukiwania:** Wartość `search` jest debounced do `debouncedSearch` z opóźnieniem 500ms. Przy zmianie wyszukiwania `skip` jest resetowany do 0.
- **Automatyczne pobieranie:** Hook automatycznie pobiera dane przy zmianie `skip`, `debouncedSearch` lub `categoryId`.
- **Obsługa błędów:** Błędy są przechowywane w stanie `error` i nie powodują crashu aplikacji.
- **Reset paginacji:** Przy zmianie wyszukiwania lub filtra kategorii, `skip` jest resetowany do 0.

### Wzorzec implementacji:

Hook powinien być zgodny z wzorcem używanym w `useShops` i `useCategories`:

- Używa `useState` do zarządzania stanem
- Używa `useEffect` do debouncingu wyszukiwania
- Używa `useCallback` do memoizacji funkcji `fetchData`
- Używa `useEffect` do automatycznego pobierania danych

## 7. Integracja API

### Endpoint backendowy

**URL:** `GET /api/v1/product-indexes` (lub `/api/v1/products` w zależności od konwencji backendu)

**Query Parameters:**

- `search?: string` - wyszukiwanie po nazwie produktu
- `category_id?: number` - filtrowanie po kategorii
- `skip?: number` - liczba elementów do pominięcia (domyślnie 0)
- `limit?: number` - maksymalna liczba elementów (domyślnie 20, max 100)

**Response:**

```typescript
{
  "items": ProductResponse[],
  "total": number,
  "skip": number,
  "limit": number
}
```

### Endpoint proxy Astro

**Plik:** `astro/src/pages/api/products/index.ts`

**Metoda:** `GET`

**Funkcjonalność:**

- Walidacja parametrów zapytania za pomocą Zod
- Proxy request do backendu
- Obsługa błędów i zwracanie odpowiedzi w formacie `ApiResponse<ProductListResponse>`

**Walidacja (Zod schema):**

```typescript
const ProductsQuerySchema = z.object({
  search: z.string().optional().default(''),
  category_id: z.coerce.number().int().positive().optional(),
  skip: z.coerce.number().int().min(0).default(0),
  limit: z.coerce.number().int().min(1).max(100).default(20),
});
```

### Service layer

**Plik:** `astro/src/lib/services/products.ts`

**Funkcja:** `getProducts(params: ProductsQueryParams): Promise<ProductListResponse>`

**Funkcjonalność:**

- Budowanie query string z parametrów
- Wywołanie endpointu proxy `/api/products`
- Obsługa odpowiedzi (zarówno `ApiResponse<T>` jak i bezpośredniej)
- Rzucanie błędów w przypadku niepowodzenia

### Typy żądań i odpowiedzi

**Request (ProductsQueryParams):**

```typescript
interface ProductsQueryParams {
  search?: string;
  category_id?: number;
  skip?: number;
  limit?: number;
}
```

**Response (ProductListResponse):**

```typescript
type ProductListResponse = PaginatedResponse<ProductResponse>;
```

## 8. Interakcje użytkownika

### 1. Wyszukiwanie produktów

**Akcja użytkownika:** Wprowadzenie tekstu w pole wyszukiwania

**Oczekiwany wynik:**

- Wartość jest aktualizowana w czasie rzeczywistym (bez debouncingu w UI)
- Po 500ms bez zmian, zapytanie jest wysyłane do API
- Lista produktów jest filtrowana zgodnie z frazą wyszukiwania
- Paginacja jest resetowana do pierwszej strony
- Stan ładowania jest wyświetlany podczas pobierania danych

**Implementacja:**

- `ProductsToolbar` wywołuje `onSearchChange` przy każdej zmianie
- `ProductsView` aktualizuje `search` przez `setSearch` z hooka
- Hook debounce'uje wartość i automatycznie pobiera dane

### 2. Filtrowanie po kategorii

**Akcja użytkownika:** Wybór kategorii z dropdowna

**Oczekiwany wynik:**

- Lista produktów jest filtrowana do wybranej kategorii
- Paginacja jest resetowana do pierwszej strony
- Jeśli wybrano "Wszystkie kategorie", filtr jest usuwany
- Stan ładowania jest wyświetlany podczas pobierania danych

**Implementacja:**

- `ProductsToolbar` wywołuje `onCategoryChange` przy zmianie
- `ProductsView` aktualizuje `categoryId` przez `setCategoryId` z hooka
- Hook automatycznie pobiera dane z nowym filtrem

### 3. Nawigacja paginacji

**Akcja użytkownika:** Kliknięcie przycisku "Poprzednia" lub "Następna"

**Oczekiwany wynik:**

- Przejście do poprzedniej/następnej strony
- Lista produktów jest aktualizowana
- Strona jest przewijana do góry (smooth scroll)
- Przyciski są wyłączone, gdy nie ma poprzedniej/następnej strony

**Implementacja:**

- `ProductsView` oblicza `currentPage` z `skip` i `limit`
- `handlePageChange` oblicza nowy `skip` i aktualizuje go przez `setSkip`
- Hook automatycznie pobiera dane z nowym `skip`

### 4. Obsługa błędów

**Akcja użytkownika:** Kliknięcie przycisku "Spróbuj ponownie" po błędzie

**Oczekiwany wynik:**

- Zapytanie jest ponawiane z tymi samymi parametrami
- Stan ładowania jest wyświetlany
- W przypadku sukcesu, dane są wyświetlone
- W przypadku błędu, komunikat błędu pozostaje widoczny

**Implementacja:**

- `ProductsView` wywołuje `refetch()` z hooka
- Hook ponownie wykonuje `fetchData` z aktualnymi parametrami

## 9. Warunki i walidacja

### Warunki weryfikowane przez interfejs

1. **Pusta lista produktów:**

   - **Warunek:** `data.length === 0 && !isLoading`
   - **Komponent:** `ProductsTable`
   - **Wpływ na stan:** Wyświetlany jest komunikat "Nie znaleziono produktów spełniających kryteria."
   - **Akcja użytkownika:** Użytkownik może zmienić wyszukiwanie lub filtr

2. **Stan ładowania:**

   - **Warunek:** `isLoading === true`
   - **Komponent:** `ProductsTable`
   - **Wpływ na stan:** Wyświetlane są skeleton placeholdery zamiast danych
   - **Akcja użytkownika:** Użytkownik czeka na załadowanie danych

3. **Błąd API:**

   - **Warunek:** `error !== null`
   - **Komponent:** `ProductsView`
   - **Wpływ na stan:** Wyświetlany jest komunikat błędu z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Użytkownik może kliknąć "Spróbuj ponownie" lub zmienić parametry wyszukiwania

4. **Brak następnej strony:**

   - **Warunek:** `currentPage >= totalPages`
   - **Komponent:** `ProductsView` (PaginationControls)
   - **Wpływ na stan:** Przycisk "Następna" jest wyłączony
   - **Akcja użytkownika:** Użytkownik nie może przejść do następnej strony

5. **Brak poprzedniej strony:**
   - **Warunek:** `currentPage <= 1`
   - **Komponent:** `ProductsView` (PaginationControls)
   - **Wpływ na stan:** Przycisk "Poprzednia" jest wyłączony
   - **Akcja użytkownika:** Użytkownik nie może przejść do poprzedniej strony

### Walidacja parametrów zapytania

Walidacja parametrów zapytania odbywa się w endpointzie proxy (`/api/products/index.ts`) za pomocą Zod:

- `search`: string (opcjonalny, domyślnie '')
- `category_id`: number, int, positive (opcjonalny)
- `skip`: number, int, min 0 (domyślnie 0)
- `limit`: number, int, min 1, max 100 (domyślnie 20)

W przypadku nieprawidłowych parametrów, endpoint zwraca błąd 400 z opisem błędów walidacji.

## 10. Obsługa błędów

### Scenariusze błędów

1. **Błąd sieci (Network Error):**

   - **Przyczyna:** Brak połączenia z internetem, timeout
   - **Obsługa:** Hook przechwytuje błąd i ustawia `error` w stanie
   - **UI:** Wyświetlany jest komunikat "Wystąpił błąd podczas pobierania danych" z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Może kliknąć "Spróbuj ponownie" lub sprawdzić połączenie

2. **Błąd 401 (Unauthorized):**

   - **Przyczyna:** Wygaśnięcie sesji, brak autoryzacji
   - **Obsługa:** Endpoint proxy zwraca błąd 401
   - **UI:** Powinien być obsłużony przez globalny error handler (przekierowanie do logowania)
   - **Akcja użytkownika:** Użytkownik jest przekierowywany do strony logowania

3. **Błąd 400 (Bad Request):**

   - **Przyczyna:** Nieprawidłowe parametry zapytania
   - **Obsługa:** Endpoint proxy zwraca błąd 400 z opisem błędów walidacji
   - **UI:** Wyświetlany jest komunikat błędu z szczegółami walidacji
   - **Akcja użytkownika:** Użytkownik może poprawić parametry wyszukiwania

4. **Błąd 500 (Internal Server Error):**

   - **Przyczyna:** Błąd po stronie backendu
   - **Obsługa:** Endpoint proxy zwraca błąd 500
   - **UI:** Wyświetlany jest komunikat "Wystąpił błąd serwera" z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Może kliknąć "Spróbuj ponownie" lub skontaktować się z supportem

5. **Pusta odpowiedź API:**

   - **Przyczyna:** API zwraca pustą listę (brak produktów)
   - **Obsługa:** Hook ustawia `data = []` i `total = 0`
   - **UI:** Wyświetlany jest komunikat "Nie znaleziono produktów spełniających kryteria."
   - **Akcja użytkownika:** Może zmienić wyszukiwanie lub filtr

6. **Nieprawidłowa struktura odpowiedzi:**
   - **Przyczyna:** API zwraca nieoczekiwaną strukturę danych
   - **Obsługa:** Service layer rzuca błąd, hook przechwytuje i ustawia `error`
   - **UI:** Wyświetlany jest komunikat błędu z możliwością ponowienia
   - **Akcja użytkownika:** Może kliknąć "Spróbuj ponownie"

### Strategia obsługi błędów

- **Graceful degradation:** Błędy nie powodują crashu aplikacji
- **Informacyjne komunikaty:** Komunikaty błędów są jasne i zrozumiałe dla użytkownika
- **Możliwość ponowienia:** Wszystkie błędy (oprócz 401) umożliwiają ponowienie zapytania
- **Logowanie błędów:** Błędy są logowane do konsoli dla celów debugowania

## 11. Kroki implementacji

### Krok 1: Utworzenie endpointu proxy API

1. Utwórz plik `astro/src/pages/api/products/index.ts`
2. Zaimplementuj endpoint `GET` z walidacją Zod dla parametrów:
   - `search` (opcjonalny string)
   - `category_id` (opcjonalny number, int, positive)
   - `skip` (number, int, min 0, domyślnie 0)
   - `limit` (number, int, min 1, max 100, domyślnie 20)
3. Zaimplementuj proxy do backendu (`/api/v1/product-indexes` lub `/api/v1/products`)
4. Obsłuż odpowiedź i zwróć w formacie `ApiResponse<ProductListResponse>`
5. Obsłuż błędy (400, 401, 500) i zwróć odpowiednie komunikaty

### Krok 2: Utworzenie service layer

1. Utwórz plik `astro/src/lib/services/products.ts`
2. Zaimplementuj funkcję `getProducts(params: ProductsQueryParams): Promise<ProductListResponse>`
3. Zbuduj query string z parametrów
4. Wywołaj endpoint proxy `/api/products`
5. Obsłuż odpowiedź (zarówno `ApiResponse<T>` jak i bezpośrednią)
6. Rzuć błąd w przypadku niepowodzenia

### Krok 3: Utworzenie custom hooka

1. Utwórz plik `astro/src/components/hooks/useProducts.ts`
2. Zaimplementuj hook zgodnie z wzorcem `useShops`:
   - Stan: `data`, `total`, `limit`, `isLoading`, `error`, `skip`, `search`, `debouncedSearch`, `categoryId`
   - Debouncing wyszukiwania (500ms)
   - Automatyczne pobieranie danych przy zmianie `skip`, `debouncedSearch`, `categoryId`
   - Funkcja `refetch` do ponownego pobrania danych
3. Zwróć interfejs `UseProductsReturn`

### Krok 4: Utworzenie komponentu ProductsToolbar

1. Utwórz plik `astro/src/components/products/ProductsToolbar.tsx`
2. Zaimplementuj komponent z:
   - Polem `Input` do wyszukiwania
   - Dropdownem `Select` do filtrowania po kategorii (opcjonalnie, jeśli kategorie są dostępne)
   - Responsywnym layoutem (kolumna na mobile, wiersz na desktop)
3. Zdefiniuj interfejs `ProductsToolbarProps`
4. Podłącz callbacks `onSearchChange` i `onCategoryChange`

### Krok 5: Utworzenie komponentu pomocniczego SynonymsList (opcjonalnie)

1. Utwórz plik `astro/src/components/products/SynonymsList.tsx`
2. Zaimplementuj komponent wyświetlający synonimy jako tagi/badges
3. Obsłuż przypadek pustej tablicy synonimów
4. Zdefiniuj interfejs `SynonymsListProps`

### Krok 6: Utworzenie komponentu ProductsTable

1. Utwórz plik `astro/src/components/products/ProductsTable.tsx`
2. Zaimplementuj komponent z:
   - Tabelą Shadcn/ui z kolumnami: Nazwa, Kategoria, Synonimy, Liczba użyć
   - Stanem ładowania (skeleton placeholdery)
   - Komunikatem o braku danych
   - Responsywnym ukrywaniem kolumn na mobile
3. Zdefiniuj interfejs `ProductsTableProps`
4. Użyj komponentu `SynonymsList` do wyświetlania synonimów (lub zaimplementuj inline)

### Krok 7: Utworzenie komponentu głównego ProductsView

1. Utwórz plik `astro/src/components/products/ProductsView.tsx`
2. Zaimplementuj komponent z:
   - Użyciem hooka `useProducts`
   - Nagłówkiem sekcji (tytuł i opis)
   - Komponentem `ProductsToolbar`
   - Komponentem `ProductsTable`
   - Kontrolkami paginacji (przyciski Poprzednia/Następna)
   - Obsługą błędów z możliwością ponowienia
3. Zaimplementuj funkcje:
   - `handleSearchChange`
   - `handleCategoryFilterChange`
   - `handlePageChange`
   - `handleRetry`

### Krok 8: Utworzenie strony Astro

1. Utwórz plik `astro/src/pages/products.astro`
2. Zaimportuj `Layout` i `ProductsView`
3. Użyj Layout jako wrapper
4. Załaduj `ProductsView` z dyrektywą `client:load`
5. Dodaj meta tagi (opcjonalnie, dla SEO)

### Krok 9: Testowanie

1. Przetestuj wyszukiwanie produktów (z debouncingiem)
2. Przetestuj filtrowanie po kategorii (jeśli zaimplementowane)
3. Przetestuj paginację (przejście między stronami)
4. Przetestuj obsługę błędów (sieć, 400, 401, 500)
5. Przetestuj responsywność (mobile i desktop)
6. Przetestuj stan ładowania (skeleton placeholdery)
7. Przetestuj pustą listę (brak produktów)

### Krok 10: Optymalizacja i poprawki

1. Sprawdź, czy wszystkie komponenty są zoptymalizowane (React.memo, useMemo, useCallback)
2. Sprawdź dostępność (ARIA labels, keyboard navigation)
3. Sprawdź zgodność z Dark Mode
4. Sprawdź wydajność (lighthouse, React DevTools)
5. Wprowadź poprawki na podstawie testów
