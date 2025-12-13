# Plan implementacji widoku Lista Paragonów

## 1. Przegląd

Widok "Lista Paragonów" (`/bills`) umożliwia użytkownikom przeglądanie historii wszystkich zakupów z możliwością filtrowania i sortowania. Widok ma charakter **read-only** i służy do wizualizacji danych zgromadzonych przez bota Telegram podczas przetwarzania paragonów. Użytkownik może przeglądać swoje paragony, filtrować je według statusu przetwarzania, sklepu oraz zakresu dat, a także sortować według różnych kryteriów.

Główne funkcjonalności:

- Przeglądanie listy paragonów z paginacją server-side
- Filtrowanie paragonów według statusu przetwarzania (pending, processing, completed, error)
- Filtrowanie paragonów według sklepu
- Filtrowanie paragonów według zakresu dat (date_from, date_to)
- Sortowanie paragonów (domyślnie: najnowsze pierwsze)
- Wyświetlanie kluczowych informacji: data, sklep, kwota, status, liczba pozycji
- Nawigacja do szczegółów paragonu (kliknięcie w wiersz)
- Responsywny design (Mobile First)

## 2. Routing widoku

**Ścieżka:** `/bills`

**Plik:** `astro/src/pages/bills.astro`

**Struktura:**

- Strona Astro wykorzystuje Layout główny (`Layout.astro`)
- Główny komponent React `BillsView` jest ładowany z dyrektywą `client:load` (Islands Architecture)
- Strona jest statyczna, ale komponent React zapewnia interaktywność

**Przykładowa implementacja:**

```astro
---
import Layout from '../layouts/Layout.astro';
import { BillsView } from '@/components/bills/BillsView';
---

<Layout>
  <BillsView client:load />
</Layout>
```

## 3. Struktura komponentów

```
BillsView (React)
├── BillsToolbar (React)
│   ├── Select (Shadcn/ui) - filtr statusu
│   ├── Select (Shadcn/ui) - filtr sklepu
│   └── DateRangePicker (Shadcn/ui) - filtr zakresu dat
├── BillsTable (React)
│   ├── Table (Shadcn/ui)
│   │   ├── TableHeader
│   │   │   └── TableRow z TableHead (z możliwością sortowania)
│   │   └── TableBody
│   │       └── TableRow z TableCell (klikalne wiersze)
│   ├── BillStatusBadge (React) - wizualizacja statusu
│   └── Skeleton (Shadcn/ui) - stan ładowania
└── PaginationControls (React)
    ├── Button (Shadcn/ui) - poprzednia strona
    ├── Text - informacja o stronie
    └── Button (Shadcn/ui) - następna strona
```

**Hierarchia:**

- `BillsView` - główny kontener, zarządza stanem i logiką
- `BillsToolbar` - pasek narzędzi z filtrami (status, sklep, zakres dat)
- `BillsTable` - tabela z danymi paragonów
- `BillStatusBadge` - komponent wizualizujący status paragonu
- `PaginationControls` - kontrolki paginacji (wbudowane w `BillsView`)

## 4. Szczegóły komponentów

### BillsView

**Opis komponentu:**
Główny komponent widoku odpowiedzialny za zarządzanie stanem, pobieranie danych z API oraz koordynację interakcji między komponentami potomnymi. Komponent wykorzystuje custom hook `useBills` do zarządzania danymi, paginacją i filtrowaniem. Komponent obsługuje również nawigację do szczegółów paragonu po kliknięciu w wiersz tabeli.

**Główne elementy:**

- Kontener główny (`<div className="container mx-auto py-10 px-4 md:px-6 space-y-6">`)
- Nagłówek sekcji z tytułem i opisem
- `BillsToolbar` - pasek narzędzi z filtrami
- `BillsTable` - tabela z danymi
- Sekcja paginacji z przyciskami nawigacji
- Obsługa błędów z możliwością ponowienia zapytania

**Obsługiwane zdarzenia:**

- `handleStatusFilterChange(status: ProcessingStatus | undefined)` - aktualizacja filtra statusu
- `handleShopFilterChange(shopId: number | undefined)` - aktualizacja filtra sklepu
- `handleDateRangeChange(dateFrom: string | undefined, dateTo: string | undefined)` - aktualizacja zakresu dat
- `handlePageChange(newPage: number)` - zmiana strony paginacji
- `handleRowClick(billId: number)` - nawigacja do szczegółów paragonu
- `handleRetry()` - ponowienie zapytania po błędzie

**Obsługiwana walidacja:**

- Walidacja parametrów zapytania odbywa się po stronie API endpointu
- Frontend nie wykonuje walidacji danych wejściowych (zgodnie z zasadą "trust but verify")
- Sprawdzanie, czy `skip` i `limit` są w poprawnych zakresach (obsługiwane przez hook)
- Walidacja zakresu dat: `date_from` nie może być późniejsza niż `date_to` (walidacja po stronie frontendu przed wysłaniem zapytania)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillResponse` - pojedynczy paragon
  - `BillListResponse` - odpowiedź API z listą paragonów
  - `BillsQueryParams` - parametry zapytania
  - `ProcessingStatus` - enum statusu przetwarzania
- Custom hook `useBills` zwraca typ `UseBillsReturn`

**Propsy:**
Komponent nie przyjmuje żadnych propsów (jest komponentem głównym widoku).

### BillsToolbar

**Opis komponentu:**
Komponent paska narzędzi zawierający filtry: status przetwarzania, sklep oraz zakres dat. Zapewnia interfejs do filtrowania paragonów. Zmiany filtrów są natychmiast przekazywane do hooka `useBills`, który zarządza debouncingiem i resetowaniem paginacji.

**Główne elementy:**

- Kontener flexbox z responsywnym układem (`flex flex-col md:flex-row items-center justify-between gap-4 py-4`)
- `Select` (Shadcn/ui) - filtr statusu przetwarzania
- `Select` (Shadcn/ui) - filtr sklepu (opcjonalny, jeśli dostępne są sklepy)
- `DateRangePicker` lub dwa osobne `Input` z typem `date` - filtr zakresu dat
- Przycisk "Wyczyść filtry" (opcjonalny, gdy aktywne są filtry)

**Obsługiwane zdarzenia:**

- `onStatusChange(status: ProcessingStatus | undefined)` - zmiana filtra statusu
- `onShopChange(shopId: number | undefined)` - zmiana filtra sklepu
- `onDateRangeChange(dateFrom: string | undefined, dateTo: string | undefined)` - zmiana zakresu dat
- `onClearFilters()` - wyczyszczenie wszystkich filtrów

**Obsługiwana walidacja:**

- Walidacja zakresu dat: `date_from` nie może być późniejsza niż `date_to` (walidacja po stronie frontendu)
- Wyświetlanie komunikatu błędu, jeśli zakres dat jest nieprawidłowy
- Blokowanie wysłania zapytania z nieprawidłowym zakresem dat

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `ProcessingStatus` - enum statusu przetwarzania
  - `ShopResponse` - typ sklepu (dla listy sklepów w filtrze)
- Propsy komponentu:
  - `status?: ProcessingStatus` - aktualny filtr statusu
  - `shopId?: number` - aktualny filtr sklepu
  - `dateFrom?: string` - data początkowa (format ISO 8601)
  - `dateTo?: string` - data końcowa (format ISO 8601)
  - `shops?: Array<Pick<Shop, 'id' | 'name'>>` - lista sklepów do wyboru (opcjonalna)
  - `onStatusChange: (status: ProcessingStatus | undefined) => void`
  - `onShopChange: (shopId: number | undefined) => void`
  - `onDateRangeChange: (dateFrom: string | undefined, dateTo: string | undefined) => void`
  - `onClearFilters?: () => void` - opcjonalna funkcja czyszczenia filtrów

**Propsy:**

```typescript
interface BillsToolbarProps {
  status?: ProcessingStatus;
  shopId?: number;
  dateFrom?: string;
  dateTo?: string;
  shops?: Array<Pick<Shop, 'id' | 'name'>>;
  onStatusChange: (status: ProcessingStatus | undefined) => void;
  onShopChange: (shopId: number | undefined) => void;
  onDateRangeChange: (
    dateFrom: string | undefined,
    dateTo: string | undefined
  ) => void;
  onClearFilters?: () => void;
}
```

### BillsTable

**Opis komponentu:**
Komponent tabeli wyświetlający listę paragonów. Tabela jest responsywna i ukrywa niektóre kolumny na urządzeniach mobilnych. Wiersze są klikalne i prowadzą do szczegółów paragonu. Komponent obsługuje stany: ładowanie (skeleton), pusta lista oraz błąd.

**Główne elementy:**

- Kontener z obramowaniem (`<div className="rounded-md border">`)
- `Table` (Shadcn/ui) - główna tabela
  - `TableHeader` z `TableRow` i `TableHead` dla kolumn:
    - Data (z możliwością sortowania)
    - Sklep (z możliwością sortowania)
    - Kwota (z możliwością sortowania, wyrównanie do prawej)
    - Status (z możliwością sortowania)
    - Liczba pozycji (z możliwością sortowania, wyrównanie do prawej, ukryte na mobile)
    - Akcje (ukryte na mobile, opcjonalne)
  - `TableBody` z `TableRow` i `TableCell` dla każdego paragonu
- `Skeleton` (Shadcn/ui) - stan ładowania (5 wierszy)
- Komunikat "Brak paragonów" - stan pustej listy
- `BillStatusBadge` - komponent wizualizujący status w kolumnie Status

**Obsługiwane zdarzenia:**

- `onRowClick(billId: number)` - kliknięcie w wiersz (nawigacja do szczegółów)
- `onSortChange(column: string, direction: 'asc' | 'desc' | undefined)` - zmiana sortowania (opcjonalne, jeśli sortowanie jest po stronie frontendu)

**Obsługiwana walidacja:**

- Sprawdzanie, czy dane są puste (wyświetlenie komunikatu)
- Sprawdzanie, czy dane są w poprawnym formacie (obsługiwane przez TypeScript)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillResponse` - pojedynczy paragon
- Propsy komponentu:
  - `data: BillResponse[]` - lista paragonów do wyświetlenia
  - `isLoading: boolean` - stan ładowania
  - `onRowClick?: (billId: number) => void` - opcjonalna funkcja obsługi kliknięcia w wiersz

**Propsy:**

```typescript
interface BillsTableProps {
  data: BillResponse[];
  isLoading: boolean;
  onRowClick?: (billId: number) => void;
}
```

### BillStatusBadge

**Opis komponentu:**
Komponent wizualizujący status paragonu za pomocą kolorowego badge'a. Różne statusy mają różne kolory zgodnie z designem systemu:

- `pending` - szary (secondary)
- `processing` - niebieski (default/primary)
- `completed` - zielony (success, custom variant)
- `error` - czerwony (destructive)

**Główne elementy:**

- `Badge` (Shadcn/ui) z odpowiednim wariantem kolorystycznym
- Tekst statusu w języku polskim (tłumaczenie enum na czytelny tekst)

**Obsługiwane zdarzenia:**
Brak (komponent prezentacyjny).

**Obsługiwana walidacja:**
Brak (komponent prezentacyjny).

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `ProcessingStatus` - enum statusu przetwarzania
- Propsy komponentu:
  - `status: ProcessingStatus` - status paragonu do wyświetlenia

**Propsy:**

```typescript
interface BillStatusBadgeProps {
  status: ProcessingStatus;
}
```

**Mapowanie statusów na warianty:**

- `pending` → `variant="secondary"` (szary)
- `processing` → `variant="default"` (niebieski)
- `completed` → custom variant lub `variant="outline"` z zielonym kolorem (wymaga rozszerzenia Badge)
- `error` → `variant="destructive"` (czerwony)

**Tłumaczenia statusów:**

- `pending` → "Oczekujący"
- `processing` → "Przetwarzanie"
- `completed` → "Zakończony"
- `error` → "Błąd"

## 5. Typy

### Typy z `@/types` (już istniejące)

#### BillResponse

```typescript
export interface BillResponse
  extends Pick<
    Bill,
    'id' | 'bill_date' | 'total_amount' | 'status' | 'created_at'
  > {
  shop: ShopResponse | null;
  items_count: number;
}
```

**Pola:**

- `id: number` - unikalny identyfikator paragonu
- `bill_date: string` - data paragonu (ISO 8601)
- `total_amount: number | null` - łączna kwota paragonu (może być null, jeśli paragon jest w trakcie przetwarzania)
- `status: ProcessingStatus` - status przetwarzania paragonu
- `created_at: string` - data utworzenia rekordu (ISO 8601)
- `shop: ShopResponse | null` - informacje o sklepie (może być null, jeśli sklep nie został rozpoznany)
- `items_count: number` - liczba pozycji w paragonie

#### BillListResponse

```typescript
export type BillListResponse = PaginatedResponse<BillResponse>;
```

**Struktura:**

- `items: BillResponse[]` - lista paragonów
- `total: number` - całkowita liczba paragonów (przed paginacją)
- `skip: number` - liczba pominiętych rekordów
- `limit: number` - maksymalna liczba zwróconych rekordów

#### BillsQueryParams

```typescript
export interface BillsQueryParams {
  skip?: number;
  limit?: number;
  status?: ProcessingStatus;
  shop_id?: number;
  date_from?: string;
  date_to?: string;
}
```

**Pola:**

- `skip?: number` - liczba pominiętych rekordów (domyślnie: 0)
- `limit?: number` - maksymalna liczba zwróconych rekordów (domyślnie: 20, maksimum: 100)
- `status?: ProcessingStatus` - filtr statusu przetwarzania (opcjonalny)
- `shop_id?: number` - filtr sklepu (opcjonalny)
- `date_from?: string` - data początkowa zakresu (ISO 8601, opcjonalna)
- `date_to?: string` - data końcowa zakresu (ISO 8601, opcjonalna)

#### ProcessingStatus

```typescript
export type ProcessingStatus = Enums<'processing_status'>;
```

**Wartości:**

- `"pending"` - paragon oczekuje na przetworzenie
- `"processing"` - paragon jest w trakcie przetwarzania
- `"completed"` - paragon został pomyślnie przetworzony
- `"error"` - wystąpił błąd podczas przetwarzania paragonu

#### ShopResponse

```typescript
export interface ShopResponse
  extends Pick<Shop, 'id' | 'name' | 'address' | 'created_at'> {
  bills_count: number;
}
```

**Pola:**

- `id: number` - unikalny identyfikator sklepu
- `name: string` - nazwa sklepu
- `address: string | null` - adres sklepu (opcjonalny)
- `created_at: string` - data utworzenia rekordu (ISO 8601)
- `bills_count: number` - liczba paragonów z tego sklepu

### Nowe typy (do utworzenia)

#### UseBillsReturn

```typescript
interface UseBillsReturn {
  data: BillResponse[];
  total: number;
  limit: number;
  isLoading: boolean;
  error: Error | null;
  skip: number;
  status?: ProcessingStatus;
  shopId?: number;
  dateFrom?: string;
  dateTo?: string;
  setSkip: (skip: number) => void;
  setStatus: (status: ProcessingStatus | undefined) => void;
  setShopId: (shopId: number | undefined) => void;
  setDateFrom: (dateFrom: string | undefined) => void;
  setDateTo: (dateTo: string | undefined) => void;
  refetch: () => Promise<void>;
}
```

**Pola:**

- `data: BillResponse[]` - lista paragonów
- `total: number` - całkowita liczba paragonów
- `limit: number` - aktualny limit paginacji
- `isLoading: boolean` - stan ładowania
- `error: Error | null` - błąd (jeśli wystąpił)
- `skip: number` - aktualna wartość skip
- `status?: ProcessingStatus` - aktualny filtr statusu
- `shopId?: number` - aktualny filtr sklepu
- `dateFrom?: string` - aktualna data początkowa
- `dateTo?: string` - aktualna data końcowa
- `setSkip: (skip: number) => void` - funkcja ustawiająca skip
- `setStatus: (status: ProcessingStatus | undefined) => void` - funkcja ustawiająca filtr statusu
- `setShopId: (shopId: number | undefined) => void` - funkcja ustawiająca filtr sklepu
- `setDateFrom: (dateFrom: string | undefined) => void` - funkcja ustawiająca datę początkową
- `setDateTo: (dateTo: string | undefined) => void` - funkcja ustawiająca datę końcową
- `refetch: () => Promise<void>` - funkcja ponownego pobrania danych

## 6. Zarządzanie stanem

Zarządzanie stanem w widoku "Lista Paragonów" odbywa się za pomocą custom hooka `useBills`, który enkapsuluje całą logikę pobierania danych, paginacji i filtrowania. Hook wykorzystuje wzorzec podobny do `useProducts` i `useShops`.

**Uwaga:** W widoku szczegółów paragonu (`/bills/[id]`) pozycje paragonu (bill_items) będą pobierane przez osobny endpoint `/api/v1/bills/{bill_id}/items` i zarządzane przez osobny custom hook `useBillItems`. Informacje o tym hooku są zawarte poniżej dla kompletności, ale jego implementacja będzie częścią planu implementacji widoku szczegółów paragonu.

### Custom Hook: useBills

**Lokalizacja:** `astro/src/components/hooks/useBills.ts`

**Funkcjonalność:**

- Zarządzanie stanem danych (`data`, `total`, `limit`, `isLoading`, `error`)
- Zarządzanie paginacją (`skip`, `setSkip`)
- Zarządzanie filtrami (`status`, `shopId`, `dateFrom`, `dateTo`)
- Automatyczne resetowanie paginacji przy zmianie filtrów
- Debouncing dla zakresu dat (opcjonalny, jeśli używamy DateRangePicker z wbudowanym debouncingiem)
- Pobieranie danych z API za pomocą funkcji `getBills` z service layer
- Obsługa błędów z możliwością ponowienia zapytania

**Implementacja wzorca:**

Hook powinien być zaimplementowany zgodnie z wzorcem używanym w `useProducts` i `useShops`:

1. Używa `useState` do zarządzania stanem lokalnym
2. Używa `useEffect` do automatycznego pobierania danych przy zmianie zależności
3. Używa `useCallback` do memoizacji funkcji pobierania danych
4. Resetuje `skip` do 0 przy zmianie filtrów (oprócz paginacji)
5. Obsługuje debouncing dla zakresu dat (jeśli potrzebny)

**Przykładowa struktura:**

```typescript
export const useBills = (
  initialSkip: number = 0,
  initialLimit: number = 20
): UseBillsReturn => {
  const [data, setData] = useState<BillResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const [skip, setSkip] = useState<number>(initialSkip);
  const [status, setStatus] = useState<ProcessingStatus | undefined>(undefined);
  const [shopId, setShopId] = useState<number | undefined>(undefined);
  const [dateFrom, setDateFrom] = useState<string | undefined>(undefined);
  const [dateTo, setDateTo] = useState<string | undefined>(undefined);

  // Reset skip when filters change
  useEffect(() => {
    setSkip(0);
  }, [status, shopId, dateFrom, dateTo]);

  // Fetch data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getBills({
        skip,
        limit: initialLimit,
        status,
        shop_id: shopId,
        date_from: dateFrom,
        date_to: dateTo,
      });

      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
    } catch (err) {
      console.error('useBills error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [skip, initialLimit, status, shopId, dateFrom, dateTo]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    total,
    limit,
    isLoading,
    error,
    skip,
    status,
    shopId,
    dateFrom,
    dateTo,
    setSkip,
    setStatus,
    setShopId,
    setDateFrom,
    setDateTo,
    refetch: fetchData,
  };
};
```

### Custom Hook: useBillItems (dla widoku szczegółów paragonu)

**Uwaga:** Ten hook będzie używany w widoku szczegółów paragonu (`/bills/[id]`), a nie w widoku listy paragonów. Informacje są zawarte tutaj dla kompletności.

**Lokalizacja:** `astro/src/components/hooks/useBillItems.ts`

**Funkcjonalność:**

- Zarządzanie stanem pozycji paragonu (`data`, `total`, `limit`, `isLoading`, `error`)
- Zarządzanie paginacją (`skip`, `setSkip`)
- Pobieranie danych z API za pomocą funkcji `getBillItems` z service layer
- Obsługa błędów z możliwością ponowienia zapytania
- Automatyczne pobieranie danych przy zmianie `billId`

**Przykładowa struktura:**

```typescript
interface UseBillItemsReturn {
  data: BillItemResponse[];
  total: number;
  limit: number;
  isLoading: boolean;
  error: Error | null;
  skip: number;
  setSkip: (skip: number) => void;
  refetch: () => Promise<void>;
}

export const useBillItems = (
  billId: number,
  initialSkip: number = 0,
  initialLimit: number = 100
): UseBillItemsReturn => {
  const [data, setData] = useState<BillItemResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const [skip, setSkip] = useState<number>(initialSkip);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!billId) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await getBillItems(billId, {
        skip,
        limit: initialLimit,
      });

      setData(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
    } catch (err) {
      console.error('useBillItems error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setData([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [billId, skip, initialLimit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    total,
    limit,
    isLoading,
    error,
    skip,
    setSkip,
    refetch: fetchData,
  };
};
```

### Service Layer: getBills

**Lokalizacja:** `astro/src/lib/services/bills.ts`

**Funkcjonalność:**

- Budowanie query string z parametrami zapytania
- Wykonywanie zapytania HTTP GET do endpointu `/api/bills`
- Obsługa odpowiedzi API (wrapped i unwrapped)
- Obsługa błędów HTTP
- Zwracanie danych w formacie `BillListResponse`

**Implementacja wzorca:**

Service powinien być zaimplementowany zgodnie z wzorcem używanym w `getProducts` i `getShops`:

1. Buduje `URLSearchParams` z parametrami zapytania
2. Wykonuje `fetch` do endpointu `/api/bills`
3. Sprawdza status odpowiedzi (`response.ok`)
4. Parsuje odpowiedź JSON
5. Obsługuje zarówno wrapped (`ApiResponse<BillListResponse>`) jak i unwrapped (`BillListResponse`) formaty odpowiedzi
6. Rzuca błędy w przypadku niepowodzenia

### Service Layer: getBillItems (dla widoku szczegółów paragonu)

**Uwaga:** Ta funkcja będzie używana w widoku szczegółów paragonu (`/bills/[id]`), a nie w widoku listy paragonów. Informacje są zawarte tutaj dla kompletności.

**Lokalizacja:** `astro/src/lib/services/bills.ts` (lub osobny plik `billItems.ts`)

**Funkcjonalność:**

- Budowanie query string z parametrami paginacji
- Wykonywanie zapytania HTTP GET do endpointu `/api/bills/{bill_id}/items`
- Obsługa odpowiedzi API (wrapped i unwrapped)
- Obsługa błędów HTTP (403, 404, 500)
- Zwracanie danych w formacie `BillItemListResponse`

**Implementacja wzorca:**

Service powinien być zaimplementowany podobnie do `getBills`:

1. Buduje `URLSearchParams` z parametrami paginacji (`skip`, `limit`)
2. Wykonuje `fetch` do endpointu `/api/bills/${billId}/items?${queryParams}`
3. Sprawdza status odpowiedzi (`response.ok`)
4. Parsuje odpowiedź JSON
5. Obsługuje zarówno wrapped (`ApiResponse<BillItemListResponse>`) jak i unwrapped (`BillItemListResponse`) formaty odpowiedzi
6. Rzuca błędy w przypadku niepowodzenia (403, 404, 500)

**Przykładowa implementacja:**

```typescript
export const getBillItems = async (
  billId: number,
  params: { skip?: number; limit?: number }
): Promise<BillItemListResponse> => {
  const queryParams = new URLSearchParams();

  const limit = params.limit || 100;
  queryParams.append('limit', limit.toString());

  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await fetch(
      `/api/bills/${billId}/items?${queryParams.toString()}`
    );

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Brak dostępu do tego paragonu');
      }
      if (response.status === 404) {
        throw new Error('Paragon nie został znaleziony');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<BillItemListResponse> | BillItemListResponse =
      await response.json();

    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch bill items');
      }
      return data.data;
    }

    return data as BillItemListResponse;
  } catch (error) {
    console.error('Error fetching bill items:', error);
    throw error;
  }
};
```

## 7. Integracja API

### Endpoint API

**URL:** `/api/bills`

**Metoda:** `GET`

**Query Parameters:**

- `skip` (optional, number, default: 0) - liczba pominiętych rekordów
- `limit` (optional, number, default: 20, max: 100) - maksymalna liczba zwróconych rekordów
- `status` (optional, string) - filtr statusu przetwarzania (pending, processing, completed, error)
- `shop_id` (optional, number) - filtr sklepu (ID sklepu)
- `date_from` (optional, string, ISO 8601) - data początkowa zakresu
- `date_to` (optional, string, ISO 8601) - data końcowa zakresu

**Request Headers:**

- `Authorization: Bearer <access_token>` - token JWT (wymagany)

**Response Body (Success - 200 OK):**

```typescript
{
  items: BillResponse[];
  total: number;
  skip: number;
  limit: number;
}
```

**Przykładowa odpowiedź:**

```json
{
  "items": [
    {
      "id": 1,
      "bill_date": "2024-01-15T10:30:00Z",
      "total_amount": 45.67,
      "status": "completed",
      "shop": {
        "id": 1,
        "name": "Biedronka",
        "address": "ul. Przykładowa 123",
        "created_at": "2024-01-01T00:00:00Z",
        "bills_count": 15
      },
      "items_count": 8,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

**Response Body (Error - 401 Unauthorized):**

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token",
  "status_code": 401
}
```

**Response Body (Error - 400 Bad Request):**

```json
{
  "error": "Bad Request",
  "message": "Invalid query parameters",
  "status_code": 400
}
```

### Endpoint API dla pozycji paragonu (Bill Items)

**Uwaga:** Pozycje paragonu (bill_items) są pobierane przez osobny endpoint, który będzie używany w widoku szczegółów paragonu (`/bills/[id]`). Informacje o tym endpoincie są zawarte tutaj dla kompletności, ale implementacja tego endpointu będzie częścią planu implementacji widoku szczegółów paragonu.

**URL:** `/api/v1/bills/{bill_id}/items`

**Metoda:** `GET`

**Path Parameters:**

- `bill_id` (required, number) - ID paragonu

**Query Parameters:**

- `skip` (optional, number, default: 0) - liczba pominiętych rekordów
- `limit` (optional, number, default: 100, max: 100) - maksymalna liczba zwróconych rekordów

**Request Headers:**

- `Authorization: Bearer <access_token>` - token JWT (wymagany)

**Response Body (Success - 200 OK):**

```typescript
{
  items: BillItemResponse[];
  total: number;
  skip: number;
  limit: number;
}
```

**Przykładowa odpowiedź:**

```json
{
  "items": [
    {
      "id": 1,
      "quantity": 2.0,
      "unit_price": 12.5,
      "total_price": 25.0,
      "original_text": "Mleko 3.2% 1L",
      "confidence_score": 0.95,
      "is_verified": true,
      "verification_source": "user",
      "product": {
        "id": 5,
        "name": "Mleko 3.2%",
        "category": {
          "id": 3,
          "name": "Nabiał"
        },
        "synonyms": ["Mleko", "Mleko 3.2%"],
        "usage_count": 15,
        "created_at": "2024-01-01T00:00:00Z"
      }
    }
  ],
  "total": 8,
  "skip": 0,
  "limit": 100
}
```

**Response Body (Error - 403 Forbidden):**

```json
{
  "error": "BillAccessDenied",
  "message": "Bill does not belong to the current user",
  "status_code": 403
}
```

**Response Body (Error - 404 Not Found):**

```json
{
  "error": "ResourceNotFound",
  "message": "Bill with id 123 not found",
  "status_code": 404
}
```

**Uwagi implementacyjne:**

- Endpoint automatycznie weryfikuje ownership - sprawdza, czy paragon należy do zalogowanego użytkownika
- Jeśli paragon nie istnieje lub nie należy do użytkownika, zwracany jest odpowiedni błąd (404 lub 403)
- Endpoint zwraca paginowaną listę pozycji z relacjami (product, category) załadowanymi eager loading
- Pozycje są sortowane według `id` (kolejność dodania)

### Astro API Endpoint dla listy paragonów

**Lokalizacja:** `astro/src/pages/api/bills/index.ts`

**Funkcjonalność:**

- Proxy endpoint, który przekazuje zapytanie do backendu FastAPI
- Obsługa autoryzacji (przekazanie tokena JWT)
- Obsługa query parameters
- Obsługa błędów HTTP

**Implementacja wzorca:**

Endpoint powinien być zaimplementowany zgodnie z wzorcem używanym w `api/products/index.ts` i `api/shops/index.ts`:

1. Pobiera query parameters z `Astro.url.searchParams`
2. Buduje URL do backendu FastAPI z query parameters
3. Pobiera token JWT z cookies lub headers
4. Wykonuje zapytanie do backendu z tokenem w headerze `Authorization`
5. Zwraca odpowiedź z backendu (lub błąd)

### Astro API Endpoint dla pozycji paragonu (przyszła implementacja)

**Lokalizacja:** `astro/src/pages/api/bills/[id]/items.ts` (lub `astro/src/pages/api/bills/[bill_id]/items.ts`)

**Funkcjonalność:**

- Proxy endpoint dla pobierania pozycji konkretnego paragonu
- Obsługa autoryzacji (przekazanie tokena JWT)
- Obsługa query parameters (skip, limit)
- Obsługa błędów HTTP

**Implementacja wzorca:**

Endpoint powinien być zaimplementowany podobnie do głównego endpointu bills:

1. Pobiera `bill_id` z parametrów ścieżki (`Astro.params.bill_id` lub `Astro.params.id`)
2. Pobiera query parameters z `Astro.url.searchParams` (skip, limit)
3. Buduje URL do backendu FastAPI: `/api/v1/bills/{bill_id}/items?skip={skip}&limit={limit}`
4. Pobiera token JWT z cookies lub headers
5. Wykonuje zapytanie do backendu z tokenem w headerze `Authorization`
6. Zwraca odpowiedź z backendu (lub błąd)

## 8. Interakcje użytkownika

### Filtrowanie

1. **Filtr statusu:**

   - Użytkownik wybiera status z dropdowna `Select`
   - Hook `useBills` resetuje paginację do pierwszej strony (`skip = 0`)
   - Hook automatycznie pobiera nowe dane z API z filtrem statusu
   - Tabela wyświetla tylko paragony z wybranym statusem

2. **Filtr sklepu:**

   - Użytkownik wybiera sklep z dropdowna `Select`
   - Hook `useBills` resetuje paginację do pierwszej strony (`skip = 0`)
   - Hook automatycznie pobiera nowe dane z API z filtrem sklepu
   - Tabela wyświetla tylko paragony z wybranego sklepu

3. **Filtr zakresu dat:**

   - Użytkownik wybiera datę początkową i/lub końcową w `DateRangePicker` lub dwóch osobnych polach `Input` z typem `date`
   - Hook `useBills` resetuje paginację do pierwszej strony (`skip = 0`)
   - Hook automatycznie pobiera nowe dane z API z filtrem zakresu dat
   - Tabela wyświetla tylko paragony z wybranego zakresu dat
   - Jeśli `date_from` jest późniejsza niż `date_to`, wyświetlany jest komunikat błędu i zapytanie nie jest wysyłane

4. **Wyczyść filtry:**
   - Użytkownik klika przycisk "Wyczyść filtry" (jeśli dostępny)
   - Wszystkie filtry są resetowane do wartości domyślnych (undefined)
   - Hook automatycznie pobiera wszystkie paragony (bez filtrów)

### Sortowanie

- Sortowanie może być zaimplementowane po stronie frontendu (sortowanie lokalne) lub po stronie backendu (sortowanie server-side)
- Jeśli sortowanie jest po stronie frontendu:
  - Użytkownik klika w nagłówek kolumny
  - Komponent `BillsTable` sortuje lokalnie dane według wybranej kolumny
  - Zmiana kierunku sortowania (asc/desc) jest wizualizowana przez ikonę strzałki w nagłówku
- Jeśli sortowanie jest po stronie backendu:
  - Użytkownik klika w nagłówek kolumny
  - Hook `useBills` dodaje parametr `sort_by` i `sort_order` do zapytania API
  - Backend zwraca posortowane dane

### Paginacja

1. **Następna strona:**

   - Użytkownik klika przycisk "Następna"
   - Hook `useBills` zwiększa `skip` o wartość `limit`
   - Hook automatycznie pobiera nową stronę danych z API
   - Tabela wyświetla nową stronę paragonów
   - Strona przewija się do góry (opcjonalnie, `window.scrollTo({ top: 0, behavior: 'smooth' })`)

2. **Poprzednia strona:**

   - Użytkownik klika przycisk "Poprzednia"
   - Hook `useBills` zmniejsza `skip` o wartość `limit`
   - Hook automatycznie pobiera poprzednią stronę danych z API
   - Tabela wyświetla poprzednią stronę paragonów
   - Strona przewija się do góry (opcjonalnie)

3. **Przyciski paginacji są nieaktywne:**
   - Przycisk "Poprzednia" jest nieaktywny, gdy `currentPage <= 1`
   - Przycisk "Następna" jest nieaktywny, gdy `currentPage >= totalPages`
   - Przyciski są również nieaktywne podczas ładowania danych (`isLoading === true`)

### Nawigacja do szczegółów

1. **Kliknięcie w wiersz tabeli:**
   - Użytkownik klika w dowolne miejsce wiersza tabeli
   - Komponent `BillsTable` wywołuje funkcję `onRowClick(billId)`
   - Komponent `BillsView` obsługuje to zdarzenie i nawiguje do `/bills/[id]` za pomocą `window.location.href` lub routera (jeśli dostępny)
   - Użytkownik jest przekierowywany do widoku szczegółów paragonu

### Obsługa błędów

1. **Błąd pobierania danych:**

   - Jeśli zapytanie API zwraca błąd, hook `useBills` ustawia `error` na obiekt `Error`
   - Komponent `BillsView` wyświetla komunikat błędu z przyciskiem "Spróbuj ponownie"
   - Użytkownik klika przycisk "Spróbuj ponownie"
   - Komponent `BillsView` wywołuje funkcję `refetch()` z hooka
   - Hook ponownie pobiera dane z API

2. **Błąd walidacji zakresu dat:**
   - Jeśli `date_from` jest późniejsza niż `date_to`, komponent `BillsToolbar` wyświetla komunikat błędu pod polami dat
   - Zapytanie do API nie jest wysyłane, dopóki zakres dat nie jest poprawny

## 9. Warunki i walidacja

### Warunki wymagane przez API

1. **Parametry paginacji:**

   - `skip` musi być liczbą całkowitą >= 0
   - `limit` musi być liczbą całkowitą >= 1 i <= 100
   - Jeśli parametry nie są podane, używane są wartości domyślne (skip=0, limit=20)

2. **Filtr statusu:**

   - `status` musi być jednym z wartości enum `ProcessingStatus`: "pending", "processing", "completed", "error"
   - Jeśli status nie jest podany, zwracane są paragony ze wszystkich statusów

3. **Filtr sklepu:**

   - `shop_id` musi być liczbą całkowitą > 0
   - Jeśli shop_id nie jest podane, zwracane są paragony ze wszystkich sklepów

4. **Filtr zakresu dat:**

   - `date_from` musi być w formacie ISO 8601 (np. "2024-01-15T00:00:00Z")
   - `date_to` musi być w formacie ISO 8601 (np. "2024-01-15T23:59:59Z")
   - `date_from` nie może być późniejsza niż `date_to` (walidacja po stronie frontendu)
   - Jeśli zakres dat nie jest podany, zwracane są paragony ze wszystkich dat

5. **Autoryzacja:**
   - Token JWT musi być ważny i nie wygasły
   - Token musi być przekazany w headerze `Authorization: Bearer <token>`

### Walidacja po stronie frontendu

1. **Walidacja zakresu dat:**

   - Komponent `BillsToolbar` sprawdza, czy `dateFrom` nie jest późniejsza niż `dateTo`
   - Jeśli warunek nie jest spełniony, wyświetlany jest komunikat błędu pod polami dat
   - Zapytanie do API nie jest wysyłane, dopóki zakres dat nie jest poprawny

2. **Walidacja parametrów paginacji:**

   - Hook `useBills` sprawdza, czy `skip` i `limit` są w poprawnych zakresach przed wysłaniem zapytania
   - Jeśli parametry są nieprawidłowe, używane są wartości domyślne

3. **Walidacja typu danych:**
   - TypeScript zapewnia typową walidację na poziomie kompilacji
   - Wszystkie propsy komponentów są typowane, co zapobiega przekazaniu nieprawidłowych wartości

### Wpływ warunków na stan interfejsu

1. **Nieprawidłowy zakres dat:**

   - Komunikat błędu jest wyświetlany pod polami dat w `BillsToolbar`
   - Przycisk "Wyczyść filtry" może być bardziej widoczny
   - Tabela nie jest aktualizowana (zachowuje poprzednie dane)

2. **Błąd autoryzacji (401):**

   - Komunikat błędu jest wyświetlany w `BillsView`
   - Użytkownik może być przekierowany do strony logowania (opcjonalnie)

3. **Błąd serwera (500):**

   - Komunikat błędu jest wyświetlany w `BillsView`
   - Przycisk "Spróbuj ponownie" jest dostępny

4. **Brak danych:**
   - Komunikat "Nie znaleziono paragonów spełniających kryteria" jest wyświetlany w `BillsTable`
   - Filtry pozostają aktywne (użytkownik może je zmienić)

## 10. Obsługa błędów

### Scenariusze błędów

1. **Błąd sieci (Network Error):**

   - **Przyczyna:** Brak połączenia z internetem, timeout, problemy z serwerem
   - **Obsługa:** Hook `useBills` przechwytuje błąd i ustawia `error` na obiekt `Error` z odpowiednim komunikatem
   - **UI:** Komponent `BillsView` wyświetla komunikat błędu z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Użytkownik może kliknąć "Spróbuj ponownie", aby ponownie pobrać dane

2. **Błąd autoryzacji (401 Unauthorized):**

   - **Przyczyna:** Token JWT jest nieprawidłowy, wygasły lub brak tokena
   - **Obsługa:** Hook `useBills` przechwytuje błąd HTTP 401 i ustawia `error` na obiekt `Error` z komunikatem "Brak autoryzacji"
   - **UI:** Komponent `BillsView` wyświetla komunikat błędu z informacją o potrzebie ponownego zalogowania
   - **Akcja użytkownika:** Użytkownik może być przekierowany do strony logowania (opcjonalnie) lub może odświeżyć stronę

3. **Błąd walidacji (400 Bad Request):**

   - **Przyczyna:** Nieprawidłowe parametry zapytania (np. nieprawidłowy format daty, nieprawidłowy status)
   - **Obsługa:** Hook `useBills` przechwytuje błąd HTTP 400 i ustawia `error` na obiekt `Error` z komunikatem z API
   - **UI:** Komponent `BillsView` wyświetla komunikat błędu z szczegółami walidacji
   - **Akcja użytkownika:** Użytkownik może poprawić parametry filtrów i spróbować ponownie

4. **Błąd serwera (500 Internal Server Error):**

   - **Przyczyna:** Błąd po stronie serwera (baza danych, przetwarzanie, itp.)
   - **Obsługa:** Hook `useBills` przechwytuje błąd HTTP 500 i ustawia `error` na obiekt `Error` z komunikatem "Błąd serwera"
   - **UI:** Komponent `BillsView` wyświetla komunikat błędu z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Użytkownik może kliknąć "Spróbuj ponownie", aby ponownie pobrać dane

5. **Brak danych (Empty Response):**

   - **Przyczyna:** Brak paragonów spełniających kryteria filtrów
   - **Obsługa:** Hook `useBills` zwraca pustą tablicę `data = []` i `total = 0`
   - **UI:** Komponent `BillsTable` wyświetla komunikat "Nie znaleziono paragonów spełniających kryteria"
   - **Akcja użytkownika:** Użytkownik może zmienić filtry lub wyczyścić je, aby zobaczyć więcej wyników

6. **Błąd walidacji zakresu dat (Frontend):**
   - **Przyczyna:** `date_from` jest późniejsza niż `date_to`
   - **Obsługa:** Komponent `BillsToolbar` sprawdza warunek przed wysłaniem zapytania i wyświetla komunikat błędu
   - **UI:** Komunikat błędu jest wyświetlany pod polami dat w `BillsToolbar`
   - **Akcja użytkownika:** Użytkownik może poprawić zakres dat

### Komponenty obsługi błędów

1. **Komunikat błędu w BillsView:**

   - Wyświetlany, gdy `error !== null`
   - Zawiera komunikat błędu i przycisk "Spróbuj ponownie"
   - Stylizowany jako `border-destructive` z odpowiednimi kolorami

2. **Komunikat błędu w BillsToolbar:**

   - Wyświetlany pod polami dat, gdy zakres dat jest nieprawidłowy
   - Zawiera komunikat "Data początkowa nie może być późniejsza niż data końcowa"
   - Stylizowany jako tekst `text-destructive`

3. **Komunikat "Brak danych" w BillsTable:**
   - Wyświetlany, gdy `data.length === 0` i `!isLoading`
   - Zawiera komunikat "Nie znaleziono paragonów spełniających kryteria"
   - Stylizowany jako tekst `text-muted-foreground` z wyśrodkowaniem

### Strategie obsługi błędów

1. **Graceful Degradation:**

   - Jeśli wystąpi błąd podczas pobierania danych, interfejs nie psuje się całkowicie
   - Komunikat błędu jest wyświetlany, ale reszta interfejsu (filtry, paginacja) pozostaje funkcjonalna
   - Użytkownik może spróbować ponownie bez przeładowania strony

2. **Retry Mechanism:**

   - Przycisk "Spróbuj ponownie" pozwala użytkownikowi ponownie pobrać dane bez przeładowania strony
   - Hook `useBills` udostępnia funkcję `refetch()`, która ponownie wykonuje zapytanie

3. **Error Logging:**
   - Błędy są logowane do konsoli przeglądarki za pomocą `console.error()`
   - W przyszłości można dodać integrację z systemem monitoringu błędów (np. Sentry)

## 11. Kroki implementacji

### Krok 1: Utworzenie struktury plików

1. Utwórz katalog `astro/src/components/bills/`
2. Utwórz pliki:
   - `BillsView.tsx` - główny komponent widoku
   - `BillsToolbar.tsx` - komponent paska narzędzi z filtrami
   - `BillsTable.tsx` - komponent tabeli z danymi
   - `BillStatusBadge.tsx` - komponent wizualizujący status paragonu

### Krok 2: Utworzenie service layer

1. Utwórz plik `astro/src/lib/services/bills.ts`
2. Zaimplementuj funkcję `getBills(params: BillsQueryParams): Promise<BillListResponse>`
3. Funkcja powinna:
   - Budować query string z parametrami
   - Wykonywać zapytanie HTTP GET do `/api/bills`
   - Obsługiwać odpowiedzi (wrapped i unwrapped)
   - Rzucać błędy w przypadku niepowodzenia

### Krok 3: Utworzenie custom hooka

1. Utwórz plik `astro/src/components/hooks/useBills.ts`
2. Zaimplementuj hook `useBills` zgodnie z wzorcem z `useProducts` i `useShops`
3. Hook powinien:
   - Zarządzać stanem danych, paginacji i filtrów
   - Automatycznie resetować paginację przy zmianie filtrów
   - Pobierać dane z API za pomocą `getBills`
   - Obsługiwać błędy

### Krok 4: Utworzenie komponentu BillStatusBadge

1. Zaimplementuj komponent `BillStatusBadge` w `BillStatusBadge.tsx`
2. Komponent powinien:
   - Przyjmować prop `status: ProcessingStatus`
   - Wyświetlać badge z odpowiednim kolorem i tekstem
   - Tłumaczyć statusy na język polski

### Krok 5: Utworzenie komponentu BillsTable

1. Zaimplementuj komponent `BillsTable` w `BillsTable.tsx`
2. Komponent powinien:
   - Wyświetlać tabelę z kolumnami: Data, Sklep, Kwota, Status, Liczba pozycji
   - Obsługiwać stan ładowania (skeleton)
   - Obsługiwać stan pustej listy
   - Obsługiwać kliknięcie w wiersz (nawigacja do szczegółów)
   - Używać komponentu `BillStatusBadge` do wyświetlania statusu
   - Być responsywny (ukrywać niektóre kolumny na mobile)

### Krok 6: Utworzenie komponentu BillsToolbar

1. Zaimplementuj komponent `BillsToolbar` w `BillsToolbar.tsx`
2. Komponent powinien:
   - Wyświetlać filtry: status, sklep, zakres dat
   - Obsługiwać zmiany filtrów i wywoływać callbacki
   - Walidować zakres dat (date_from nie może być późniejsza niż date_to)
   - Wyświetlać komunikat błędu przy nieprawidłowym zakresie dat
   - Opcjonalnie: wyświetlać przycisk "Wyczyść filtry"

### Krok 7: Utworzenie komponentu BillsView

1. Zaimplementuj komponent `BillsView` w `BillsView.tsx`
2. Komponent powinien:
   - Używać hooka `useBills` do zarządzania danymi
   - Renderować nagłówek sekcji z tytułem i opisem
   - Renderować `BillsToolbar` z odpowiednimi propsami
   - Renderować `BillsTable` z danymi
   - Renderować kontrolki paginacji
   - Obsługiwać błędy z możliwością ponowienia zapytania
   - Obsługiwać nawigację do szczegółów paragonu

### Krok 8: Utworzenie strony Astro

1. Utwórz plik `astro/src/pages/bills.astro`
2. Strona powinna:
   - Importować `Layout` i `BillsView`
   - Renderować `BillsView` z dyrektywą `client:load`

### Krok 9: Utworzenie Astro API endpoint

1. Utwórz plik `astro/src/pages/api/bills/index.ts`
2. Endpoint powinien:
   - Obsługiwać metodę GET
   - Pobierać query parameters z `Astro.url.searchParams`
   - Pobierać token JWT z cookies lub headers
   - Wykonywać zapytanie do backendu FastAPI z tokenem
   - Zwracać odpowiedź z backendu

### Krok 10: Pobranie listy sklepów dla filtra (opcjonalne)

1. Jeśli filtr sklepu ma wyświetlać listę dostępnych sklepów:
   - Użyj istniejącego hooka `useShops` w `BillsView`
   - Przekaż listę sklepów do `BillsToolbar` jako prop `shops`
   - `BillsToolbar` wyświetli dropdown z listą sklepów

### Krok 11: Testowanie

1. Przetestuj wszystkie scenariusze:
   - Wyświetlanie listy paragonów
   - Filtrowanie według statusu
   - Filtrowanie według sklepu
   - Filtrowanie według zakresu dat
   - Paginacja (następna/poprzednia strona)
   - Nawigacja do szczegółów paragonu (kliknięcie w wiersz)
   - Obsługa błędów (sieć, autoryzacja, serwer)
   - Walidacja zakresu dat
   - Responsywność (mobile/desktop)

### Krok 12: Optymalizacja i poprawki

1. Sprawdź wydajność:

   - Debouncing dla zakresu dat (jeśli potrzebny)
   - Memoizacja komponentów (jeśli potrzebna)
   - Lazy loading (jeśli potrzebny)

2. Sprawdź dostępność (a11y):

   - Klawiatura nawigacja
   - ARIA labels
   - Focus management

3. Sprawdź zgodność z designem:
   - Kolory i style zgodne z Shadcn/ui
   - Responsywność zgodna z Mobile First
   - Dark mode (jeśli dostępny)
