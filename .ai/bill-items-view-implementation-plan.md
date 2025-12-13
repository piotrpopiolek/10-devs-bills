# Plan implementacji widoku Szczegóły Paragonu

## 1. Przegląd

Widok "Szczegóły Paragonu" (`/bills/[id]`) umożliwia użytkownikom przeglądanie szczegółowych informacji o konkretnym paragonie, w tym zdjęcia paragonu, metadanych oraz listy wszystkich pozycji z paragonu. Widok ma charakter **read-only** i służy do weryfikacji poprawności odczytu paragonu przez system OCR i AI. Użytkownik może porównać zdjęcie paragonu z listą pozycji, sprawdzić wskaźniki pewności (confidence score) dla każdej pozycji oraz zobaczyć, które produkty zostały znormalizowane.

Główne funkcjonalności:

- Wyświetlanie zdjęcia paragonu z możliwością powiększenia (zoom)
- Wyświetlanie metadanych paragonu (data, sklep, suma, status)
- Wyświetlanie listy wszystkich pozycji z paragonu (bill_items)
- Wizualizacja wskaźnika pewności (confidence score) dla każdej pozycji
- Porównanie tekstu oryginalnego (OCR) z znormalizowaną nazwą produktu
- Automatyczne odświeżanie statusu paragonu (polling), gdy status to "processing"
- Nawigacja do szczegółów sklepu (kliknięcie w nazwę sklepu)
- Responsywny design (Mobile First)
- Lazy loading zdjęcia paragonu

## 2. Routing widoku

**Ścieżka:** `/bills/[id]`

**Plik:** `astro/src/pages/bills/[id].astro`

**Struktura:**

- Strona Astro wykorzystuje Layout główny (`Layout.astro`)
- Dynamic route z parametrem `id` (ID paragonu)
- Główny komponent React `BillDetailView` jest ładowany z dyrektywą `client:load` (Islands Architecture)
- Strona jest statyczna, ale komponent React zapewnia interaktywność i dynamiczne pobieranie danych

**Przykładowa implementacja:**

```astro
---
import Layout from '../../layouts/Layout.astro';
import { BillDetailView } from '@/components/bills/BillDetailView';

const { id } = Astro.params;
---

<Layout>
  <BillDetailView billId={Number(id)} client:load />
</Layout>
```

**Uwaga:** Parametr `id` z URL jest przekazywany jako prop do komponentu React, który następnie używa go do pobrania danych z API.

## 3. Struktura komponentów

```
BillDetailView (React)
├── BillHeader (React)
│   ├── Breadcrumbs (Shadcn/ui) - nawigacja okruszkowa
│   ├── Title - "Paragon #123"
│   └── BillStatusBadge (React) - status paragonu
├── BillMetadata (React)
│   ├── MetadataRow - Data paragonu
│   ├── MetadataRow - Sklep (klikalny link do /shops/[id])
│   ├── MetadataRow - Suma całkowita
│   └── MetadataRow - Status przetwarzania
├── BillImageViewer (React)
│   ├── Image (lazy loading)
│   ├── Zoom controls (opcjonalne)
│   └── Loading state (Skeleton)
├── BillItemsSection (React)
│   ├── SectionHeader - "Pozycje paragonu (8)"
│   ├── BillItemsTable (React)
│   │   ├── Table (Shadcn/ui)
│   │   │   ├── TableHeader
│   │   │   │   └── TableRow z TableHead
│   │   │   └── TableBody
│   │   │       └── TableRow z TableCell
│   │   ├── ConfidenceIndicator (React) - wizualizacja confidence score
│   │   └── Skeleton (Shadcn/ui) - stan ładowania
│   └── ItemsSummary - suma wszystkich pozycji
└── ErrorBoundary (React)
    └── ErrorMessage - obsługa błędów
```

**Hierarchia:**

- `BillDetailView` - główny kontener, zarządza stanem i logiką
- `BillHeader` - nagłówek z breadcrumbs i statusem
- `BillMetadata` - metadane paragonu
- `BillImageViewer` - komponent wyświetlający zdjęcie paragonu
- `BillItemsSection` - sekcja z pozycjami paragonu
- `BillItemsTable` - tabela z pozycjami
- `ConfidenceIndicator` - wizualizacja confidence score

## 4. Szczegóły komponentów

### BillDetailView

**Opis komponentu:**
Główny komponent widoku odpowiedzialny za zarządzanie stanem, pobieranie danych z API oraz koordynację interakcji między komponentami potomnymi. Komponent wykorzystuje custom hooki `useBillDetail` i `useBillItems` do zarządzania danymi paragonu i pozycjami. Komponent obsługuje również automatyczne odświeżanie (polling) statusu paragonu, gdy status to "processing".

**Główne elementy:**

- Kontener główny (`<div className="container mx-auto py-10 px-4 md:px-6 space-y-6">`)
- `BillHeader` - nagłówek z breadcrumbs
- `BillMetadata` - metadane paragonu
- `BillImageViewer` - zdjęcie paragonu
- `BillItemsSection` - sekcja z pozycjami
- Obsługa błędów z możliwością ponowienia zapytania
- Polling statusu (jeśli status === "processing")

**Obsługiwane zdarzenia:**

- `handleShopClick(shopId: number)` - nawigacja do szczegółów sklepu
- `handleRetry()` - ponowienie zapytania po błędzie
- Automatyczne odświeżanie statusu (polling) - gdy status === "processing"

**Obsługiwana walidacja:**

- Walidacja parametru `billId` - musi być liczbą całkowitą > 0
- Sprawdzanie, czy paragon istnieje (obsługiwane przez API)
- Sprawdzanie, czy paragon należy do użytkownika (obsługiwane przez API)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillDetailResponse` - szczegóły paragonu (z backendu, ale items są pobierane osobno)
  - `BillResponse` - podstawowe informacje o paragonie
  - `BillItemResponse` - pojedyncza pozycja paragonu
  - `BillItemListResponse` - odpowiedź API z listą pozycji
- Custom hooki `useBillDetail` i `useBillItems` zwracają odpowiednie typy

**Propsy:**

```typescript
interface BillDetailViewProps {
  billId: number;
}
```

### BillHeader

**Opis komponentu:**
Komponent nagłówka wyświetlający breadcrumbs, tytuł paragonu oraz status. Zapewnia nawigację wsteczną do listy paragonów.

**Główne elementy:**

- `Breadcrumbs` (Shadcn/ui) - ścieżka: "Paragony > #123"
- Tytuł sekcji (`<h1>Paragon #{billId}</h1>`)
- `BillStatusBadge` - status paragonu

**Obsługiwane zdarzenia:**

- Kliknięcie w breadcrumb "Paragony" - nawigacja do `/bills`

**Obsługiwana walidacja:**
Brak (komponent prezentacyjny).

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `ProcessingStatus` - enum statusu przetwarzania
- Propsy komponentu:
  - `billId: number` - ID paragonu
  - `status: ProcessingStatus` - status paragonu

**Propsy:**

```typescript
interface BillHeaderProps {
  billId: number;
  status: ProcessingStatus;
}
```

### BillMetadata

**Opis komponentu:**
Komponent wyświetlający metadane paragonu w formie czytelnej listy. Zawiera informacje o dacie, sklepie, sumie oraz statusie przetwarzania.

**Główne elementy:**

- Kontener z obramowaniem (`<div className="rounded-md border p-4">`)
- Lista metadanych (`<dl className="grid grid-cols-1 md:grid-cols-2 gap-4">`)
  - Data paragonu (`<dt>Data</dt><dd>{billDate}</dd>`)
  - Sklep (`<dt>Sklep</dt><dd><Link>{shopName}</Link></dd>`)
  - Suma całkowita (`<dt>Suma</dt><dd>{totalAmount} PLN</dd>`)
  - Status (`<dt>Status</dt><dd><BillStatusBadge /></dd>`)

**Obsługiwane zdarzenia:**

- `onShopClick(shopId: number)` - kliknięcie w nazwę sklepu (nawigacja do `/shops/[id]`)

**Obsługiwana walidacja:**

- Sprawdzanie, czy `totalAmount` jest null (wyświetlenie "-" lub "Przetwarzanie...")
- Sprawdzanie, czy `shop` jest null (wyświetlenie "Nieznany sklep")

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillResponse` - podstawowe informacje o paragonie
  - `ShopResponse` - informacje o sklepie
- Propsy komponentu:
  - `bill: BillResponse` - dane paragonu
  - `onShopClick?: (shopId: number) => void` - opcjonalna funkcja obsługi kliknięcia w sklep

**Propsy:**

```typescript
interface BillMetadataProps {
  bill: BillResponse;
  onShopClick?: (shopId: number) => void;
}
```

### BillImageViewer

**Opis komponentu:**
Komponent wyświetlający zdjęcie paragonu z możliwością powiększenia (zoom). Obsługuje lazy loading oraz stany: ładowanie, błąd, brak zdjęcia.

**Główne elementy:**

- Kontener z obramowaniem (`<div className="rounded-md border overflow-hidden">`)
- `Image` (Next.js Image lub natywny `<img>`) z lazy loading
- Zoom controls (opcjonalne, np. przycisk "Powiększ" lub modal z zoomem)
- `Skeleton` (Shadcn/ui) - stan ładowania
- Komunikat "Brak zdjęcia" - gdy `imageUrl` jest null

**Obsługiwane zdarzenia:**

- `onImageClick()` - kliknięcie w zdjęcie (otwarcie w pełnym rozmiarze lub modal)
- `onZoomIn()` - powiększenie zdjęcia
- `onZoomOut()` - pomniejszenie zdjęcia

**Obsługiwana walidacja:**

- Sprawdzanie, czy `imageUrl` jest null lub undefined
- Sprawdzanie, czy `imageUrl` jest ważny (nie wygasły)
- Obsługa błędów ładowania obrazu (onError handler)

**Typy:**

- Propsy komponentu:
  - `imageUrl: string | null` - URL zdjęcia paragonu (signed URL)
  - `imageExpiresAt: string | null` - data wygaśnięcia URL (opcjonalna)
  - `isLoading: boolean` - stan ładowania
  - `alt?: string` - tekst alternatywny dla obrazu (domyślnie: "Zdjęcie paragonu")

**Propsy:**

```typescript
interface BillImageViewerProps {
  imageUrl: string | null;
  imageExpiresAt?: string | null;
  isLoading: boolean;
  alt?: string;
}
```

**Uwagi implementacyjne:**

- Lazy loading: użyj `loading="lazy"` dla natywnego `<img>` lub `next/image` z lazy loading
- Signed URL: URL zdjęcia jest signed URL z backendu, ważny przez określony czas (np. 1 godzinę)
- Jeśli URL wygasł, należy ponownie pobrać dane paragonu, aby uzyskać nowy signed URL

### BillItemsSection

**Opis komponentu:**
Komponent sekcji zawierający nagłówek, tabelę pozycji oraz podsumowanie (suma wszystkich pozycji).

**Główne elementy:**

- Nagłówek sekcji (`<h2>Pozycje paragonu ({itemsCount})</h2>`)
- `BillItemsTable` - tabela z pozycjami
- Podsumowanie (`<div className="text-right font-medium">Suma: {totalSum} PLN</div>`)

**Obsługiwane zdarzenia:**
Brak (komponent kontenerowy).

**Obsługiwana walidacja:**

- Sprawdzanie, czy lista pozycji jest pusta (wyświetlenie komunikatu)
- Obliczanie sumy wszystkich pozycji (walidacja, czy suma zgadza się z `total_amount` paragonu)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillItemResponse[]` - lista pozycji
- Propsy komponentu:
  - `items: BillItemResponse[]` - lista pozycji paragonu
  - `isLoading: boolean` - stan ładowania
  - `totalAmount: number | null` - suma całkowita paragonu (do porównania)

**Propsy:**

```typescript
interface BillItemsSectionProps {
  items: BillItemResponse[];
  isLoading: boolean;
  totalAmount: number | null;
}
```

### BillItemsTable

**Opis komponentu:**
Komponent tabeli wyświetlający listę pozycji paragonu. Tabela jest responsywna i ukrywa niektóre kolumny na urządzeniach mobilnych. Każda pozycja wyświetla nazwę produktu (znormalizowaną lub oryginalną), ilość, ceny oraz wskaźnik pewności.

**Główne elementy:**

- Kontener z obramowaniem (`<div className="rounded-md border">`)
- `Table` (Shadcn/ui) - główna tabela
  - `TableHeader` z `TableRow` i `TableHead` dla kolumn:
    - Nazwa produktu (zawsze widoczna)
    - Tekst oryginalny (OCR) (ukryte na mobile)
    - Ilość (ukryte na mobile)
    - Cena jednostkowa (ukryte na mobile)
    - Cena całkowita (zawsze widoczna, wyrównanie do prawej)
    - Pewność (Confidence) (zawsze widoczna)
    - Status weryfikacji (ukryte na mobile)
  - `TableBody` z `TableRow` i `TableCell` dla każdej pozycji
- `Skeleton` (Shadcn/ui) - stan ładowania (5 wierszy)
- Komunikat "Brak pozycji" - stan pustej listy
- `ConfidenceIndicator` - komponent wizualizujący confidence score w każdej pozycji

**Obsługiwane zdarzenia:**
Brak (komponent prezentacyjny, read-only).

**Obsługiwana walidacja:**

- Sprawdzanie, czy dane są puste (wyświetlenie komunikatu)
- Sprawdzanie, czy dane są w poprawnym formacie (obsługiwane przez TypeScript)

**Typy:**

- Wykorzystuje typy z `@/types`:
  - `BillItemResponse` - pojedyncza pozycja paragonu
- Propsy komponentu:
  - `items: BillItemResponse[]` - lista pozycji do wyświetlenia
  - `isLoading: boolean` - stan ładowania

**Propsy:**

```typescript
interface BillItemsTableProps {
  items: BillItemResponse[];
  isLoading: boolean;
}
```

**Szczegóły wyświetlania kolumn:**

1. **Nazwa produktu:**

   - Jeśli `index_name` istnieje: `index_name` (znormalizowana nazwa, `font-medium`)
   - Jeśli `index_name` jest null: `original_text` (tekst z OCR, `italic text-muted-foreground`)
   - Tooltip z `original_text`, jeśli produkt jest znormalizowany

2. **Tekst oryginalny (OCR):**

   - `original_text` - zawsze wyświetlane, nawet jeśli produkt jest znormalizowany
   - Pomaga porównać OCR z znormalizowaną nazwą

3. **Ilość:**

   - `quantity` - konwersja z stringa na liczbę i formatowanie (np. "1.0000" → "1" lub "2.5000" → "2.5")
   - Wyświetlanie z odpowiednią jednostką (domyślnie: bez jednostki, jeśli nie określono)

4. **Cena jednostkowa:**

   - `unit_price` - konwersja z stringa na liczbę i formatowanie w PLN (np. "4.89" → "4.89 PLN")

5. **Cena całkowita:**

   - `total_price` - konwersja z stringa na liczbę i formatowanie w PLN (np. "4.89" → "4.89 PLN")
   - Wyróżniona (`font-medium`)
   - Wyrównanie do prawej (`text-right`)

6. **Pewność (Confidence):**

   - `ConfidenceIndicator` - wizualny wskaźnik na podstawie `confidence_score` (konwersja z stringa na number: `parseFloat(confidence_score)`)
   - Tooltip z wartością procentową

7. **Status weryfikacji:**
   - `is_verified` - ikona/znacznik (✓ jeśli zweryfikowane)
   - `verification_source` - źródło weryfikacji (auto/user/admin) jako tooltip

### ConfidenceIndicator

**Opis komponentu:**
Komponent wizualizujący wskaźnik pewności (confidence score) za pomocą kolorowej kropki i tooltipa. Różne zakresy confidence score mają różne kolory:

- `>= 0.8` (80%+) - zielony (wysoka pewność)
- `0.5 - 0.79` (50-79%) - żółty (średnia pewność)
- `< 0.5` (<50%) - czerwony (niska pewność)

**Główne elementy:**

- `Tooltip` (Shadcn/ui) - tooltip z wartością procentową
- Kolorowa kropka (`<div className="w-3 h-3 rounded-full" />`) z odpowiednim kolorem
- Tekst wartości procentowej w tooltipie

**Obsługiwane zdarzenia:**
Brak (komponent prezentacyjny).

**Obsługiwana walidacja:**

- Sprawdzanie, czy `score` jest null (wyświetlenie "-" lub szarej kropki)
- Konwersja `score` z stringa na number: `parseFloat(score)`
- Sprawdzanie, czy przekonwertowany `score` jest w zakresie 0.0-1.0
- Obsługa błędów konwersji (jeśli string nie jest poprawną liczbą)

**Typy:**

- Propsy komponentu:
  - `score: string | null` - confidence score jako string (format: "0.70", zakres 0.00-1.00 lub null)
  - `showTooltip?: boolean` - czy pokazać tooltip (domyślnie: true)

**Propsy:**

```typescript
interface ConfidenceIndicatorProps {
  score: number | null;
  showTooltip?: boolean;
}
```

**Mapowanie score na kolory:**

- `score >= 0.8` → `bg-green-600` (zielony)
- `score >= 0.5 && score < 0.8` → `bg-yellow-600` (żółty)
- `score < 0.5` → `bg-red-600` (czerwony)
- `score === null` → `bg-gray-400` (szary) lub tekst "-"

**Format wyświetlania:**

- Tooltip: "Pewność: {percent}%" (np. "Pewność: 70%")
- Wartość procentowa: `Math.round(parseFloat(score) * 100)` (konwersja z stringa na number)
- Jeśli `score` jest stringiem, należy go przekonwertować na number przed porównaniem: `parseFloat(score)`

## 5. Typy

### Typy z `@/types` (już istniejące)

#### BillResponse

```typescript
export interface BillResponse
  extends Pick<Bill, 'id' | 'bill_date' | 'status' | 'created_at'> {
  total_amount: number | string | null;
  shop_id?: number | null;
  shop?: ShopResponse | null;
  items_count?: number;
}
```

**Pola:**

- `id: number` - unikalny identyfikator paragonu
- `bill_date: string` - data paragonu (ISO 8601)
- `total_amount: number | string | null` - łączna kwota paragonu (może być null, jeśli paragon jest w trakcie przetwarzania)
- `status: ProcessingStatus` - status przetwarzania paragonu
- `created_at: string` - data utworzenia rekordu (ISO 8601)
- `shop_id?: number | null` - ID sklepu (opcjonalne)
- `shop?: ShopResponse | null` - informacje o sklepie (może być null)
- `items_count?: number` - liczba pozycji w paragonie (opcjonalne)

**Uwaga:** W widoku szczegółów paragonu, `BillResponse` z endpointu `/api/v1/bills/{id}` może zawierać `image_signed_url` (z backendu), ale `items` są pobierane osobno przez endpoint `/api/v1/bills/{id}/items`.

#### BillItemResponse

```typescript
export interface BillItemResponse {
  id: number;
  quantity: string;
  unit_price: string;
  total_price: string;
  original_text: string | null;
  confidence_score: string | null;
  is_verified: boolean;
  verification_source: VerificationSource;
  bill_id: number;
  index_id: number | null;
  index_name: string | null;
  category_id: number | null;
  category_name: string | null;
  created_at: string;
}
```

**Pola:**

- `id: number` - unikalny identyfikator pozycji
- `quantity: string` - ilość produktu (format: "1.0000")
- `unit_price: string` - cena jednostkowa (format: "4.89")
- `total_price: string` - cena całkowita (format: "4.89")
- `original_text: string | null` - tekst odczytany przez OCR
- `confidence_score: string | null` - wskaźnik pewności (format: "0.70", zakres 0.00-1.00)
- `is_verified: boolean` - czy pozycja została zweryfikowana
- `verification_source: VerificationSource` - źródło weryfikacji (auto/user/admin)
- `bill_id: number` - ID paragonu, do którego należy pozycja
- `index_id: number | null` - ID znormalizowanego produktu (może być null, jeśli produkt nie został rozpoznany)
- `index_name: string | null` - nazwa znormalizowanego produktu (może być null, jeśli produkt nie został rozpoznany)
- `category_id: number | null` - ID kategorii produktu
- `category_name: string | null` - nazwa kategorii produktu
- `created_at: string` - data utworzenia rekordu (ISO 8601)

#### BillItemListResponse

```typescript
export type BillItemListResponse = PaginatedResponse<BillItemResponse>;
```

**Struktura:**

- `items: BillItemResponse[]` - lista pozycji paragonu
- `total: number` - całkowita liczba pozycji (przed paginacją)
- `skip: number` - liczba pominiętych rekordów
- `limit: number` - maksymalna liczba zwróconych rekordów

#### ProcessingStatus

```typescript
export type ProcessingStatus = Enums<'processing_status'>;
```

**Wartości:**

- `"pending"` - paragon oczekuje na przetworzenie
- `"processing"` - paragon jest w trakcie przetwarzania
- `"completed"` - paragon został pomyślnie przetworzony
- `"error"` - wystąpił błąd podczas przetwarzania paragonu

#### VerificationSource

```typescript
export type VerificationSource = Enums<'verification_source'>;
```

**Wartości:**

- `"auto"` - weryfikacja automatyczna (system)
- `"user"` - weryfikacja przez użytkownika (Telegram)
- `"admin"` - weryfikacja przez administratora

**Uwaga:** W faktycznej odpowiedzi backendu nie ma zagnieżdżonego obiektu `ProductResponse`. Zamiast tego, informacje o produkcie są zwracane jako płaskie pola w `BillItemResponse`:

- `index_id: number | null` - ID produktu (odpowiednik `Product.id`)
- `index_name: string | null` - nazwa produktu (odpowiednik `Product.name`)
- `category_id: number | null` - ID kategorii (odpowiednik `Category.id`)
- `category_name: string | null` - nazwa kategorii (odpowiednik `Category.name`)

### Nowe typy (do utworzenia)

#### UseBillDetailReturn

```typescript
interface UseBillDetailReturn {
  bill: BillResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}
```

**Pola:**

- `bill: BillResponse | null` - dane paragonu (null podczas ładowania lub błędu)
- `isLoading: boolean` - stan ładowania
- `error: Error | null` - błąd (jeśli wystąpił)
- `refetch: () => Promise<void>` - funkcja ponownego pobrania danych

#### UseBillItemsReturn

```typescript
interface UseBillItemsReturn {
  items: BillItemResponse[];
  total: number;
  limit: number;
  isLoading: boolean;
  error: Error | null;
  skip: number;
  setSkip: (skip: number) => void;
  refetch: () => Promise<void>;
}
```

**Pola:**

- `items: BillItemResponse[]` - lista pozycji paragonu
- `total: number` - całkowita liczba pozycji
- `limit: number` - aktualny limit paginacji
- `isLoading: boolean` - stan ładowania
- `error: Error | null` - błąd (jeśli wystąpił)
- `skip: number` - aktualna wartość skip
- `setSkip: (skip: number) => void` - funkcja ustawiająca skip
- `refetch: () => Promise<void>` - funkcja ponownego pobrania danych

**Uwaga:** W większości przypadków wszystkie pozycje paragonu będą wyświetlane na jednej stronie (bez paginacji), ale hook obsługuje paginację na wypadek paragonów z bardzo dużą liczbą pozycji.

## 6. Zarządzanie stanem

Zarządzanie stanem w widoku szczegółów paragonu odbywa się za pomocą dwóch custom hooków: `useBillDetail` (dla danych paragonu) i `useBillItems` (dla pozycji paragonu). Dodatkowo, komponent `BillDetailView` zarządza pollingiem statusu paragonu, gdy status to "processing".

### Custom Hook: useBillDetail

**Lokalizacja:** `astro/src/components/hooks/useBillDetail.ts`

**Funkcjonalność:**

- Zarządzanie stanem danych paragonu (`bill`, `isLoading`, `error`)
- Pobieranie danych z API za pomocą funkcji `getBillDetail` z service layer
- Obsługa błędów z możliwością ponowienia zapytania
- Automatyczne pobieranie danych przy zmianie `billId`

**Implementacja wzorca:**

Hook powinien być zaimplementowany zgodnie z wzorcem używanym w `useBills`:

1. Używa `useState` do zarządzania stanem lokalnym
2. Używa `useEffect` do automatycznego pobierania danych przy zmianie `billId`
3. Używa `useCallback` do memoizacji funkcji pobierania danych
4. Obsługuje błędy HTTP (403, 404, 500)

**Przykładowa struktura:**

```typescript
export const useBillDetail = (billId: number): UseBillDetailReturn => {
  const [bill, setBill] = useState<BillResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!billId || billId <= 0) {
      setIsLoading(false);
      setError(new Error('Nieprawidłowe ID paragonu'));
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await getBillDetail(billId);
      setBill(response);
    } catch (err) {
      console.error('useBillDetail error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setBill(null);
    } finally {
      setIsLoading(false);
    }
  }, [billId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    bill,
    isLoading,
    error,
    refetch: fetchData,
  };
};
```

### Custom Hook: useBillItems

**Lokalizacja:** `astro/src/components/hooks/useBillItems.ts`

**Funkcjonalność:**

- Zarządzanie stanem pozycji paragonu (`items`, `total`, `limit`, `isLoading`, `error`)
- Zarządzanie paginacją (`skip`, `setSkip`)
- Pobieranie danych z API za pomocą funkcji `getBillItems` z service layer
- Obsługa błędów z możliwością ponowienia zapytania
- Automatyczne pobieranie danych przy zmianie `billId`

**Implementacja wzorca:**

Hook powinien być zaimplementowany zgodnie z wzorcem używanym w `useBills`:

1. Używa `useState` do zarządzania stanem lokalnym
2. Używa `useEffect` do automatycznego pobierania danych przy zmianie `billId`
3. Używa `useCallback` do memoizacji funkcji pobierania danych
4. Obsługuje błędy HTTP (403, 404, 500)

**Przykładowa struktura:**

```typescript
export const useBillItems = (
  billId: number,
  initialSkip: number = 0,
  initialLimit: number = 100
): UseBillItemsReturn => {
  const [items, setItems] = useState<BillItemResponse[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(initialLimit);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  const [skip, setSkip] = useState<number>(initialSkip);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!billId || billId <= 0) {
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

      setItems(response.items || []);
      setTotal(response.total || 0);
      setLimit(response.limit || initialLimit);
    } catch (err) {
      console.error('useBillItems error:', err);
      setError(
        err instanceof Error ? err : new Error('An unknown error occurred')
      );
      setItems([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [billId, skip, initialLimit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    items,
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

### Polling statusu paragonu

**Lokalizacja:** W komponencie `BillDetailView`

**Funkcjonalność:**

- Automatyczne odświeżanie danych paragonu, gdy status to "processing"
- Polling z interwałem (np. 5 sekund)
- Zatrzymanie pollingu, gdy status zmieni się na "completed" lub "error"
- Zatrzymanie pollingu, gdy komponent zostanie odmontowany

**Implementacja wzorca:**

```typescript
// W komponencie BillDetailView
useEffect(() => {
  if (!bill || bill.status !== 'processing') {
    return;
  }

  const intervalId = setInterval(() => {
    refetchBill();
  }, 5000); // Polling co 5 sekund

  return () => {
    clearInterval(intervalId);
  };
}, [bill?.status, refetchBill]);
```

**Uwagi:**

- Polling powinien być zatrzymany, gdy użytkownik opuści stronę (cleanup w useEffect)
- Polling powinien być zatrzymany, gdy status zmieni się na "completed" lub "error"
- Można dodać maksymalny czas pollingu (np. 5 minut), po którym polling zostanie zatrzymany

### Service Layer: getBillDetail

**Lokalizacja:** `astro/src/lib/services/bills.ts`

**Funkcjonalność:**

- Wykonywanie zapytania HTTP GET do endpointu `/api/bills/{bill_id}`
- Obsługa odpowiedzi API (wrapped i unwrapped)
- Obsługa błędów HTTP (403, 404, 500)
- Zwracanie danych w formacie `BillResponse`

**Implementacja wzorca:**

Service powinien być zaimplementowany podobnie do `getBills`:

1. Wykonuje `fetch` do endpointu `/api/bills/${billId}`
2. Sprawdza status odpowiedzi (`response.ok`)
3. Parsuje odpowiedź JSON
4. Obsługuje zarówno wrapped (`ApiResponse<BillResponse>`) jak i unwrapped (`BillResponse`) formaty odpowiedzi
5. Rzuca błędy w przypadku niepowodzenia (403, 404, 500)

**Przykładowa implementacja:**

```typescript
export const getBillDetail = async (billId: number): Promise<BillResponse> => {
  if (!billId || billId <= 0) {
    throw new Error('Nieprawidłowe ID paragonu');
  }

  try {
    const response = await apiFetch(`/api/bills/${billId}`);

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('Brak dostępu do tego paragonu');
      }
      if (response.status === 404) {
        throw new Error('Paragon nie został znaleziony');
      }
      throw new Error(`API error: ${response.status}`);
    }

    const data: ApiResponse<BillResponse> | BillResponse =
      await response.json();

    if ('data' in data && 'success' in data) {
      if (!data.success) {
        throw new Error(data.message || 'Failed to fetch bill');
      }
      return data.data;
    }

    return data as BillResponse;
  } catch (error) {
    console.error('Error fetching bill detail:', error);
    throw error;
  }
};
```

### Service Layer: getBillItems

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
  if (!billId || billId <= 0) {
    throw new Error('Nieprawidłowe ID paragonu');
  }

  const queryParams = new URLSearchParams();

  const limit = params.limit || 100;
  queryParams.append('limit', limit.toString());

  const skip = params.skip ?? 0;
  queryParams.append('skip', skip.toString());

  try {
    const response = await apiFetch(
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

### Endpoint API dla szczegółów paragonu

**URL:** `/api/v1/bills/{bill_id}`

**Metoda:** `GET`

**Path Parameters:**

- `bill_id` (required, number) - ID paragonu

**Query Parameters:**
Brak

**Request Headers:**

- `Authorization: Bearer <access_token>` - token JWT (wymagany)

**Response Body (Success - 200 OK):**

```typescript
{
  id: number;
  bill_date: string;
  total_amount: number | null;
  status: ProcessingStatus;
  image_signed_url: string | null;
  image_expires_at: string | null;
  shop: ShopResponse | null;
  items_count?: number;
  created_at: string;
  updated_at: string;
}
```

**Przykładowa odpowiedź:**

```json
{
  "id": 123,
  "bill_date": "2024-01-15T10:30:00Z",
  "total_amount": 45.67,
  "status": "completed",
  "image_signed_url": "https://storage.example.com/bills/123/image.jpg?signature=...",
  "image_expires_at": "2024-01-15T11:30:00Z",
  "shop": {
    "id": 1,
    "name": "Biedronka",
    "address": "ul. Przykładowa 123",
    "created_at": "2024-01-01T00:00:00Z",
    "bills_count": 15
  },
  "items_count": 8,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
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
- Endpoint zwraca `image_signed_url` - signed URL do zdjęcia paragonu, ważny przez określony czas (np. 1 godzinę)
- `image_expires_at` - data wygaśnięcia signed URL (może być użyta do sprawdzenia, czy URL jest nadal ważny)

### Endpoint API dla pozycji paragonu

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
      "quantity": "1.0000",
      "unit_price": "4.89",
      "total_price": "4.89",
      "is_verified": true,
      "verification_source": "user",
      "bill_id": 142,
      "index_id": null,
      "original_text": "PIĄTNICA JOG PIT. 330ML C",
      "confidence_score": "0.70",
      "category_id": 17,
      "id": 828,
      "created_at": "2025-12-12T21:01:24.864619Z",
      "index_name": null,
      "category_name": "Nabiał i Jaja"
    },
    {
      "quantity": "1.0000",
      "unit_price": "6.49",
      "total_price": "6.43",
      "is_verified": true,
      "verification_source": "user",
      "bill_id": 142,
      "index_id": null,
      "original_text": "SIERPC PLAST KROL.135G C",
      "confidence_score": "0.70",
      "category_id": 17,
      "id": 832,
      "created_at": "2025-12-12T21:01:56.556916Z",
      "index_name": null,
      "category_name": "Nabiał i Jaja"
    }
  ],
  "total": 2,
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
- Endpoint zwraca paginowaną listę pozycji z płaską strukturą (zamiast zagnieżdżonych obiektów)
- Pola numeryczne (`quantity`, `unit_price`, `total_price`, `confidence_score`) są zwracane jako stringi
- Pola `index_id` i `index_name` reprezentują znormalizowany produkt (może być null, jeśli produkt nie został rozpoznany)
- Pola `category_id` i `category_name` reprezentują kategorię produktu
- Pozycje są sortowane według `id` (kolejność dodania)

### Astro API Endpoint dla szczegółów paragonu

**Lokalizacja:** `astro/src/pages/api/bills/[id].ts` (lub `[bill_id].ts`)

**Funkcjonalność:**

- Proxy endpoint dla pobierania szczegółów konkretnego paragonu
- Obsługa autoryzacji (przekazanie tokena JWT)
- Obsługa błędów HTTP

**Implementacja wzorca:**

Endpoint powinien być zaimplementowany podobnie do głównego endpointu bills:

1. Pobiera `bill_id` z parametrów ścieżki (`Astro.params.id` lub `Astro.params.bill_id`)
2. Pobiera token JWT z cookies lub headers
3. Buduje URL do backendu FastAPI: `/api/v1/bills/{bill_id}`
4. Wykonuje zapytanie do backendu z tokenem w headerze `Authorization`
5. Zwraca odpowiedź z backendu (lub błąd)

### Astro API Endpoint dla pozycji paragonu

**Lokalizacja:** `astro/src/pages/api/bills/[id]/items.ts` (lub `[bill_id]/items.ts`)

**Funkcjonalność:**

- Proxy endpoint dla pobierania pozycji konkretnego paragonu
- Obsługa autoryzacji (przekazanie tokena JWT)
- Obsługa query parameters (skip, limit)
- Obsługa błędów HTTP

**Implementacja wzorca:**

Endpoint powinien być zaimplementowany podobnie do głównego endpointu bills:

1. Pobiera `bill_id` z parametrów ścieżki (`Astro.params.id` lub `Astro.params.bill_id`)
2. Pobiera query parameters z `Astro.url.searchParams` (skip, limit)
3. Buduje URL do backendu FastAPI: `/api/v1/bills/{bill_id}/items?skip={skip}&limit={limit}`
4. Pobiera token JWT z cookies lub headers
5. Wykonuje zapytanie do backendu z tokenem w headerze `Authorization`
6. Zwraca odpowiedź z backendu (lub błąd)

## 8. Interakcje użytkownika

### Nawigacja

1. **Kliknięcie w breadcrumb "Paragony":**

   - Użytkownik klika w breadcrumb "Paragony" w `BillHeader`
   - Komponent nawiguje do `/bills` za pomocą `window.location.href` lub routera (jeśli dostępny)
   - Użytkownik jest przekierowywany do widoku listy paragonów

2. **Kliknięcie w nazwę sklepu:**
   - Użytkownik klika w nazwę sklepu w `BillMetadata`
   - Komponent `BillDetailView` obsługuje to zdarzenie i nawiguje do `/shops/[id]`
   - Użytkownik jest przekierowywany do widoku szczegółów sklepu

### Interakcje ze zdjęciem

1. **Kliknięcie w zdjęcie paragonu:**

   - Użytkownik klika w zdjęcie w `BillImageViewer`
   - Zdjęcie otwiera się w modalnym oknie (Dialog) w pełnym rozmiarze
   - Użytkownik może zamknąć modal klikając w przycisk "Zamknij" lub poza modalem

2. **Zoom zdjęcia (opcjonalne):**
   - Użytkownik może użyć przycisków "Powiększ" / "Pomniejsz" w `BillImageViewer`
   - Zoom jest wizualizowany przez zmianę skali obrazu (CSS transform: scale)
   - Maksymalny poziom zoom: 200% (2x)

### Polling statusu

1. **Automatyczne odświeżanie:**

   - Gdy status paragonu to "processing", komponent `BillDetailView` automatycznie odświeża dane co 5 sekund
   - Hook `useBillDetail` ponownie pobiera dane paragonu
   - Jeśli status zmieni się na "completed" lub "error", polling zostaje zatrzymany
   - Jeśli użytkownik opuści stronę, polling zostaje zatrzymany (cleanup w useEffect)

2. **Wizualizacja pollingu:**
   - Podczas pollingu można wyświetlić subtelny wskaźnik (np. animowana kropka obok statusu)
   - Komunikat "Aktualizowanie statusu..." (opcjonalny)

### Obsługa błędów

1. **Błąd pobierania danych paragonu:**

   - Jeśli zapytanie API zwraca błąd, hook `useBillDetail` ustawia `error` na obiekt `Error`
   - Komponent `BillDetailView` wyświetla komunikat błędu z przyciskiem "Spróbuj ponownie"
   - Użytkownik klika przycisk "Spróbuj ponownie"
   - Komponent `BillDetailView` wywołuje funkcję `refetch()` z hooka
   - Hook ponownie pobiera dane z API

2. **Błąd pobierania pozycji:**

   - Jeśli zapytanie API zwraca błąd, hook `useBillItems` ustawia `error` na obiekt `Error`
   - Komponent `BillItemsTable` wyświetla komunikat błędu z przyciskiem "Spróbuj ponownie"
   - Użytkownik klika przycisk "Spróbuj ponownie"
   - Komponent `BillDetailView` wywołuje funkcję `refetch()` z hooka `useBillItems`
   - Hook ponownie pobiera dane z API

3. **Błąd ładowania zdjęcia:**
   - Jeśli zdjęcie nie może zostać załadowane (404, wygasły URL), `BillImageViewer` wyświetla komunikat błędu
   - Komunikat: "Nie można załadować zdjęcia paragonu"
   - Opcjonalnie: przycisk "Odśwież", który ponownie pobiera dane paragonu (aby uzyskać nowy signed URL)

## 9. Warunki i walidacja

### Warunki wymagane przez API

1. **Parametr bill_id:**

   - `bill_id` musi być liczbą całkowitą > 0
   - Jeśli `bill_id` nie jest podany lub jest nieprawidłowy, zwracany jest błąd 404

2. **Autoryzacja:**

   - Token JWT musi być ważny i nie wygasły
   - Token musi być przekazany w headerze `Authorization: Bearer <token>`
   - Jeśli token jest nieprawidłowy, zwracany jest błąd 401

3. **Ownership:**

   - Paragon musi należeć do zalogowanego użytkownika
   - Jeśli paragon nie należy do użytkownika, zwracany jest błąd 403

4. **Parametry paginacji (dla items):**
   - `skip` musi być liczbą całkowitą >= 0
   - `limit` musi być liczbą całkowitą >= 1 i <= 100
   - Jeśli parametry nie są podane, używane są wartości domyślne (skip=0, limit=100)

### Walidacja po stronie frontendu

1. **Walidacja billId:**

   - Komponent `BillDetailView` sprawdza, czy `billId` jest liczbą całkowitą > 0 przed wysłaniem zapytania
   - Jeśli `billId` jest nieprawidłowy, wyświetlany jest komunikat błędu bez wysyłania zapytania

2. **Walidacja signed URL:**

   - Komponent `BillImageViewer` sprawdza, czy `imageUrl` nie jest null przed wyświetleniem
   - Opcjonalnie: sprawdza, czy `imageExpiresAt` nie minął (jeśli dostępne)
   - Jeśli URL wygasł, można automatycznie ponownie pobrać dane paragonu, aby uzyskać nowy signed URL

3. **Walidacja typu danych:**
   - TypeScript zapewnia typową walidację na poziomie kompilacji
   - Wszystkie propsy komponentów są typowane, co zapobiega przekazaniu nieprawidłowych wartości

### Wpływ warunków na stan interfejsu

1. **Nieprawidłowe billId:**

   - Komunikat błędu jest wyświetlany w `BillDetailView`
   - Komponenty potomne nie są renderowane

2. **Błąd autoryzacji (401):**

   - Komunikat błędu jest wyświetlany w `BillDetailView`
   - Użytkownik może być przekierowany do strony logowania (opcjonalnie)

3. **Brak dostępu (403):**

   - Komunikat błędu jest wyświetlany w `BillDetailView`
   - Komunikat: "Nie masz dostępu do tego paragonu"

4. **Paragon nie istnieje (404):**

   - Komunikat błędu jest wyświetlany w `BillDetailView`
   - Komunikat: "Paragon nie został znaleziony"
   - Opcjonalnie: przycisk "Powrót do listy paragonów"

5. **Brak zdjęcia:**

   - Komunikat "Brak zdjęcia paragonu" jest wyświetlany w `BillImageViewer`
   - Reszta widoku (metadane, pozycje) pozostaje widoczna

6. **Brak pozycji:**
   - Komunikat "Brak pozycji w paragonie" jest wyświetlany w `BillItemsTable`
   - Może to oznaczać, że paragon jest w trakcie przetwarzania lub wystąpił błąd

## 10. Obsługa błędów

### Scenariusze błędów

1. **Błąd sieci (Network Error):**

   - **Przyczyna:** Brak połączenia z internetem, timeout, problemy z serwerem
   - **Obsługa:** Hooki `useBillDetail` i `useBillItems` przechwytują błąd i ustawiają `error` na obiekt `Error` z odpowiednim komunikatem
   - **UI:** Komponenty wyświetlają komunikat błędu z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Użytkownik może kliknąć "Spróbuj ponownie", aby ponownie pobrać dane

2. **Błąd autoryzacji (401 Unauthorized):**

   - **Przyczyna:** Token JWT jest nieprawidłowy, wygasły lub brak tokena
   - **Obsługa:** Hooki przechwytują błąd HTTP 401 i ustawiają `error` na obiekt `Error` z komunikatem "Brak autoryzacji"
   - **UI:** Komponent `BillDetailView` wyświetla komunikat błędu z informacją o potrzebie ponownego zalogowania
   - **Akcja użytkownika:** Użytkownik może być przekierowany do strony logowania (opcjonalnie) lub może odświeżyć stronę

3. **Brak dostępu (403 Forbidden):**

   - **Przyczyna:** Paragon nie należy do zalogowanego użytkownika
   - **Obsługa:** Hooki przechwytują błąd HTTP 403 i ustawiają `error` na obiekt `Error` z komunikatem "Brak dostępu do tego paragonu"
   - **UI:** Komponent `BillDetailView` wyświetla komunikat błędu z informacją o braku dostępu
   - **Akcja użytkownika:** Użytkownik może kliknąć "Powrót do listy paragonów"

4. **Paragon nie istnieje (404 Not Found):**

   - **Przyczyna:** Paragon o podanym ID nie istnieje w bazie danych
   - **Obsługa:** Hooki przechwytują błąd HTTP 404 i ustawiają `error` na obiekt `Error` z komunikatem "Paragon nie został znaleziony"
   - **UI:** Komponent `BillDetailView` wyświetla komunikat błędu z informacją o braku paragonu
   - **Akcja użytkownika:** Użytkownik może kliknąć "Powrót do listy paragonów"

5. **Błąd serwera (500 Internal Server Error):**

   - **Przyczyna:** Błąd po stronie serwera (baza danych, przetwarzanie, itp.)
   - **Obsługa:** Hooki przechwytują błąd HTTP 500 i ustawiają `error` na obiekt `Error` z komunikatem "Błąd serwera"
   - **UI:** Komponenty wyświetlają komunikat błędu z przyciskiem "Spróbuj ponownie"
   - **Akcja użytkownika:** Użytkownik może kliknąć "Spróbuj ponownie", aby ponownie pobrać dane

6. **Błąd ładowania zdjęcia:**

   - **Przyczyna:** Signed URL wygasł, zdjęcie zostało usunięte, problemy z serwerem storage
   - **Obsługa:** Komponent `BillImageViewer` obsługuje błąd `onError` na elemencie `<img>`
   - **UI:** Komunikat "Nie można załadować zdjęcia paragonu" jest wyświetlany w `BillImageViewer`
   - **Akcja użytkownika:** Opcjonalnie: przycisk "Odśwież", który ponownie pobiera dane paragonu (aby uzyskać nowy signed URL)

7. **Brak danych (Empty Response):**
   - **Przyczyna:** Paragon istnieje, ale nie ma jeszcze pozycji (status: "processing" lub "pending")
   - **Obsługa:** Hook `useBillItems` zwraca pustą tablicę `items = []` i `total = 0`
   - **UI:** Komponent `BillItemsTable` wyświetla komunikat "Brak pozycji w paragonie. Paragon może być w trakcie przetwarzania."
   - **Akcja użytkownika:** Użytkownik może poczekać na zakończenie przetwarzania (polling automatycznie odświeży dane)

### Komponenty obsługi błędów

1. **Komunikat błędu w BillDetailView:**

   - Wyświetlany, gdy `error !== null` w `useBillDetail`
   - Zawiera komunikat błędu i przycisk "Spróbuj ponownie"
   - Stylizowany jako `border-destructive` z odpowiednimi kolorami
   - Opcjonalnie: przycisk "Powrót do listy paragonów"

2. **Komunikat błędu w BillItemsTable:**

   - Wyświetlany, gdy `error !== null` w `useBillItems`
   - Zawiera komunikat błędu i przycisk "Spróbuj ponownie"
   - Stylizowany jako `border-destructive` z odpowiednimi kolorami

3. **Komunikat błędu w BillImageViewer:**

   - Wyświetlany, gdy zdjęcie nie może zostać załadowane
   - Zawiera komunikat "Nie można załadować zdjęcia paragonu"
   - Opcjonalnie: przycisk "Odśwież", który ponownie pobiera dane paragonu

4. **Komunikat "Brak danych" w BillItemsTable:**
   - Wyświetlany, gdy `items.length === 0` i `!isLoading` i `!error`
   - Zawiera komunikat "Brak pozycji w paragonie. Paragon może być w trakcie przetwarzania."
   - Stylizowany jako tekst `text-muted-foreground` z wyśrodkowaniem

### Strategie obsługi błędów

1. **Graceful Degradation:**

   - Jeśli wystąpi błąd podczas pobierania danych paragonu, interfejs nie psuje się całkowicie
   - Komunikat błędu jest wyświetlany, ale reszta interfejsu (jeśli dostępna) pozostaje funkcjonalna
   - Użytkownik może spróbować ponownie bez przeładowania strony

2. **Retry Mechanism:**

   - Przycisk "Spróbuj ponownie" pozwala użytkownikowi ponownie pobrać dane bez przeładowania strony
   - Hooki udostępniają funkcję `refetch()`, która ponownie wykonuje zapytanie

3. **Polling z obsługą błędów:**

   - Jeśli podczas pollingu wystąpi błąd, polling zostaje zatrzymany
   - Komunikat błędu jest wyświetlany użytkownikowi
   - Użytkownik może ręcznie ponownie włączyć polling (przez przycisk "Spróbuj ponownie")

4. **Error Logging:**
   - Błędy są logowane do konsoli przeglądarki za pomocą `console.error()`
   - W przyszłości można dodać integrację z systemem monitoringu błędów (np. Sentry)

## 11. Kroki implementacji

### Krok 1: Utworzenie struktury plików

1. Utwórz katalog `astro/src/components/bills/detail/` (opcjonalnie, można też umieścić w `astro/src/components/bills/`)
2. Utwórz pliki:
   - `BillDetailView.tsx` - główny komponent widoku
   - `BillHeader.tsx` - komponent nagłówka z breadcrumbs
   - `BillMetadata.tsx` - komponent metadanych paragonu
   - `BillImageViewer.tsx` - komponent wyświetlający zdjęcie paragonu
   - `BillItemsSection.tsx` - komponent sekcji z pozycjami
   - `BillItemsTable.tsx` - komponent tabeli z pozycjami
   - `ConfidenceIndicator.tsx` - komponent wizualizujący confidence score

### Krok 2: Rozszerzenie service layer

1. Otwórz plik `astro/src/lib/services/bills.ts`
2. Dodaj funkcję `getBillDetail(billId: number): Promise<BillResponse>`
3. Dodaj funkcję `getBillItems(billId: number, params: { skip?: number; limit?: number }): Promise<BillItemListResponse>`
4. Funkcje powinny:
   - Budować query string z parametrami (dla getBillItems)
   - Wykonywać zapytania HTTP GET do odpowiednich endpointów
   - Obsługiwać odpowiedzi (wrapped i unwrapped)
   - Rzucać błędy w przypadku niepowodzenia (403, 404, 500)

### Krok 3: Utworzenie custom hooków

1. Utwórz plik `astro/src/components/hooks/useBillDetail.ts`
2. Zaimplementuj hook `useBillDetail` zgodnie z wzorcem z `useBills`
3. Hook powinien:

   - Zarządzać stanem danych paragonu
   - Pobierać dane z API za pomocą `getBillDetail`
   - Obsługiwać błędy

4. Utwórz plik `astro/src/components/hooks/useBillItems.ts`
5. Zaimplementuj hook `useBillItems` zgodnie z wzorcem z planu bills-view-implementation-plan.md
6. Hook powinien:
   - Zarządzać stanem pozycji paragonu
   - Pobierać dane z API za pomocą `getBillItems`
   - Obsługiwać błędy

### Krok 4: Utworzenie komponentu ConfidenceIndicator

1. Zaimplementuj komponent `ConfidenceIndicator` w `ConfidenceIndicator.tsx`
2. Komponent powinien:
   - Przyjmować prop `score: number | null`
   - Wyświetlać kolorową kropkę (zielony/żółty/czerwony) na podstawie score
   - Wyświetlać tooltip z wartością procentową
   - Obsługiwać przypadek, gdy `score` jest null

### Krok 5: Utworzenie komponentu BillItemsTable

1. Zaimplementuj komponent `BillItemsTable` w `BillItemsTable.tsx`
2. Komponent powinien:
   - Wyświetlać tabelę z kolumnami: Nazwa produktu, Tekst oryginalny, Ilość, Cena jednostkowa, Cena całkowita, Pewność, Status weryfikacji
   - Obsługiwać stan ładowania (skeleton)
   - Obsługiwać stan pustej listy
   - Używać komponentu `ConfidenceIndicator` do wyświetlania confidence score
   - Wyświetlać znormalizowaną nazwę produktu lub oryginalny tekst OCR
   - Być responsywny (ukrywać niektóre kolumny na mobile)

### Krok 6: Utworzenie komponentu BillItemsSection

1. Zaimplementuj komponent `BillItemsSection` w `BillItemsSection.tsx`
2. Komponent powinien:
   - Wyświetlać nagłówek sekcji z liczbą pozycji
   - Renderować `BillItemsTable` z danymi
   - Wyświetlać podsumowanie (suma wszystkich pozycji)
   - Porównywać sumę pozycji z `total_amount` paragonu (opcjonalnie, wyświetlenie ostrzeżenia, jeśli się nie zgadza)

### Krok 7: Utworzenie komponentu BillImageViewer

1. Zaimplementuj komponent `BillImageViewer` w `BillImageViewer.tsx`
2. Komponent powinien:
   - Wyświetlać zdjęcie paragonu z lazy loading
   - Obsługiwać stan ładowania (skeleton)
   - Obsługiwać błąd ładowania obrazu
   - Obsługiwać przypadek, gdy `imageUrl` jest null
   - Opcjonalnie: modal z powiększonym zdjęciem (Dialog z Shadcn/ui)
   - Opcjonalnie: zoom controls

### Krok 8: Utworzenie komponentu BillMetadata

1. Zaimplementuj komponent `BillMetadata` w `BillMetadata.tsx`
2. Komponent powinien:
   - Wyświetlać metadane paragonu w formie czytelnej listy
   - Obsługiwać kliknięcie w nazwę sklepu (nawigacja do `/shops/[id]`)
   - Obsługiwać przypadek, gdy `shop` jest null
   - Obsługiwać przypadek, gdy `total_amount` jest null

### Krok 9: Utworzenie komponentu BillHeader

1. Zaimplementuj komponent `BillHeader` w `BillHeader.tsx`
2. Komponent powinien:
   - Wyświetlać breadcrumbs (Paragony > #123)
   - Wyświetlać tytuł sekcji
   - Wyświetlać status paragonu (BillStatusBadge)
   - Obsługiwać kliknięcie w breadcrumb "Paragony" (nawigacja do `/bills`)

### Krok 10: Utworzenie komponentu BillDetailView

1. Zaimplementuj komponent `BillDetailView` w `BillDetailView.tsx`
2. Komponent powinien:
   - Używać hooków `useBillDetail` i `useBillItems` do zarządzania danymi
   - Renderować `BillHeader` z odpowiednimi propsami
   - Renderować `BillMetadata` z danymi paragonu
   - Renderować `BillImageViewer` z signed URL
   - Renderować `BillItemsSection` z pozycjami
   - Obsługiwać błędy z możliwością ponowienia zapytania
   - Implementować polling statusu (gdy status === "processing")
   - Obsługiwać nawigację do szczegółów sklepu

### Krok 11: Utworzenie strony Astro

1. Utwórz plik `astro/src/pages/bills/[id].astro`
2. Strona powinna:
   - Pobierać parametr `id` z `Astro.params`
   - Walidować, czy `id` jest liczbą
   - Importować `Layout` i `BillDetailView`
   - Renderować `BillDetailView` z dyrektywą `client:load` i propem `billId`

### Krok 12: Utworzenie Astro API endpointów

1. Utwórz plik `astro/src/pages/api/bills/[id].ts` (lub `[bill_id].ts`)
2. Endpoint powinien:

   - Obsługiwać metodę GET
   - Pobierać `bill_id` z parametrów ścieżki
   - Pobierać token JWT z cookies lub headers
   - Wykonywać zapytanie do backendu FastAPI: `/api/v1/bills/{bill_id}` z tokenem
   - Zwracać odpowiedź z backendu (lub błąd)

3. Utwórz plik `astro/src/pages/api/bills/[id]/items.ts` (lub `[bill_id]/items.ts`)
4. Endpoint powinien:
   - Obsługiwać metodę GET
   - Pobierać `bill_id` z parametrów ścieżki
   - Pobierać query parameters z `Astro.url.searchParams` (skip, limit)
   - Pobierać token JWT z cookies lub headers
   - Wykonywać zapytanie do backendu FastAPI: `/api/v1/bills/{bill_id}/items?skip={skip}&limit={limit}` z tokenem
   - Zwracać odpowiedź z backendu (lub błąd)

### Krok 13: Implementacja pollingu statusu

1. W komponencie `BillDetailView`, dodaj `useEffect` do pollingu statusu
2. Polling powinien:
   - Działać tylko, gdy `bill?.status === "processing"`
   - Odświeżać dane co 5 sekund
   - Zatrzymywać się, gdy status zmieni się na "completed" lub "error"
   - Zatrzymywać się, gdy komponent zostanie odmontowany (cleanup)
   - Opcjonalnie: wyświetlać subtelny wskaźnik pollingu

### Krok 14: Testowanie

1. Przetestuj wszystkie scenariusze:
   - Wyświetlanie szczegółów paragonu
   - Wyświetlanie zdjęcia paragonu (z lazy loading)
   - Wyświetlanie listy pozycji paragonu
   - Wyświetlanie confidence score dla każdej pozycji
   - Nawigacja do szczegółów sklepu (kliknięcie w nazwę sklepu)
   - Nawigacja do listy paragonów (breadcrumb)
   - Polling statusu (gdy status === "processing")
   - Obsługa błędów (sieć, autoryzacja, serwer, 403, 404)
   - Obsługa braku zdjęcia
   - Obsługa braku pozycji
   - Responsywność (mobile/desktop)
   - Lazy loading zdjęcia

### Krok 15: Optymalizacja i poprawki

1. Sprawdź wydajność:

   - Lazy loading zdjęcia (upewnij się, że działa poprawnie)
   - Memoizacja komponentów (jeśli potrzebna)
   - Optymalizacja pollingu (nie za często, nie za rzadko)

2. Sprawdź dostępność (a11y):

   - Klawiatura nawigacja
   - ARIA labels dla obrazów
   - ARIA labels dla tooltipów
   - Focus management w modalach

3. Sprawdź zgodność z designem:
   - Kolory i style zgodne z Shadcn/ui
   - Responsywność zgodna z Mobile First
   - Dark mode (jeśli dostępny)
   - Tooltips i modale zgodne z designem systemu
