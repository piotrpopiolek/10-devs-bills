# Plan implementacji widoku: Struktura Kategorii

## 1. Przegląd

Widok "Struktura Kategorii" (`/categories`) służy do wizualizacji hierarchicznej struktury kategorii produktów w systemie. Widok prezentuje drzewo kategorii w formie zagnieżdżonej, gdzie główne kategorie (z `parent_id: null`) są widoczne na najwyższym poziomie, a ich podkategorie są ukryte i mogą być rozwinięte poprzez interakcję użytkownika. Widok jest w trybie "read-only" - użytkownik może jedynie przeglądać strukturę kategorii i zobaczyć liczbę przypisanych produktów oraz pozycji paragonów dla każdej kategorii.

**Główne cele widoku:**

- Prezentacja hierarchicznej struktury kategorii w czytelnej formie
- Wyświetlenie liczby produktów przypisanych do każdej kategorii
- Wyświetlenie liczby pozycji paragonów przypisanych do każdej kategorii
- Umożliwienie eksploracji struktury poprzez rozwinięcie/zwinięcie podkategorii

## 2. Routing widoku

**Ścieżka:** `/categories`

**Plik routingu:** `astro/src/pages/categories.astro`

**Struktura pliku:**

```astro
---
import Layout from '../layouts/Layout.astro';
import { CategoriesView } from '@/components/categories/CategoriesView';
---

<Layout>
  <CategoriesView client:load />
</Layout>
```

**Uwagi:**

- Widok wykorzystuje komponent React `CategoriesView` z dyrektywą `client:load`, co oznacza, że komponent jest hydratowany natychmiast po załadowaniu strony
- Layout zapewnia spójną strukturę strony (Sidebar, TopBar na mobile) oraz autoryzację

## 3. Struktura komponentów

```
CategoriesView (React)
├── CategoriesHeader (React)
│   ├── Title - "Kategorie"
│   └── Description - "Wizualizacja hierarchii wydatków"
├── CategoriesTree (React)
│   ├── CategoryAccordion (React) [rekurencyjnie]
│   │   ├── AccordionItem (Shadcn/ui)
│   │   │   ├── AccordionTrigger (Shadcn/ui)
│   │   │   │   ├── CategoryName
│   │   │   │   ├── CategoryStats (produkty + pozycje)
│   │   │   │   └── ChevronIcon (expand/collapse)
│   │   │   └── AccordionContent (Shadcn/ui)
│   │   │       └── CategoryAccordion (rekurencyjnie dla dzieci)
│   │   └── EmptyState (gdy brak dzieci)
│   └── EmptyState (gdy brak kategorii)
├── LoadingState (React)
│   └── Skeleton (Shadcn/ui)
└── ErrorState (React)
    ├── ErrorMessage
    └── RetryButton
```

**Hierarchia komponentów:**

- **CategoriesView** - główny kontener widoku, zarządza stanem, pobieraniem danych i transformacją płaskiej listy w drzewo
- **CategoriesHeader** - nagłówek widoku z tytułem i opisem
- **CategoriesTree** - komponent wyświetlający drzewo kategorii, wykorzystuje rekurencyjny komponent CategoryAccordion
- **CategoryAccordion** - rekurencyjny komponent wyświetlający pojedynczą kategorię wraz z jej dziećmi w formie Accordion
- **LoadingState** - stan ładowania z skeleton loaderami
- **ErrorState** - stan błędu z możliwością ponowienia próby

## 4. Szczegóły komponentów

### CategoriesView

**Opis komponentu:**
Główny komponent widoku odpowiedzialny za zarządzanie stanem, pobieranie danych z API oraz transformację płaskiej listy kategorii w hierarchiczną strukturę drzewiastą. Komponent wykorzystuje custom hook `useCategories` do pobierania danych i funkcję pomocniczą `buildCategoryTree` do budowania struktury drzewiastej.

**Główne elementy:**

- Kontener główny z klasami Tailwind: `container mx-auto py-10 px-4 md:px-6 space-y-6`
- Warunkowe renderowanie: LoadingState, ErrorState lub CategoriesTree
- Hook `useCategories` do pobierania danych
- Funkcja `buildCategoryTree` do transformacji danych

**Obsługiwane zdarzenia:**

- Brak bezpośrednich zdarzeń użytkownika (komponent tylko koordynuje)

**Obsługiwana walidacja:**

- Sprawdzenie czy dane zostały pobrane poprawnie
- Sprawdzenie czy lista kategorii nie jest pusta przed budowaniem drzewa

**Typy:**

- Props: brak (komponent nie przyjmuje propsów)
- Stan wewnętrzny: zarządzany przez `useCategories` hook
- ViewModel: `CategoryTreeNode[]` - drzewo kategorii

**Propsy:**

- Brak (komponent główny)

### CategoriesHeader

**Opis komponentu:**
Komponent prezentacyjny wyświetlający nagłówek widoku z tytułem i opisem. Zapewnia spójny wygląd nagłówka zgodny z innymi widokami w aplikacji.

**Główne elementy:**

- `h1` z tytułem "Kategorie" (klasy: `text-3xl font-bold tracking-tight`)
- `p` z opisem (klasy: `text-muted-foreground`)
- Kontener z klasami: `flex flex-col gap-2`

**Obsługiwane zdarzenia:**

- Brak

**Obsługiwana walidacja:**

- Brak

**Typy:**

- Props: brak

**Propsy:**

- Brak

### CategoriesTree

**Opis komponentu:**
Komponent odpowiedzialny za renderowanie drzewa kategorii. Przyjmuje tablicę węzłów drzewa (`CategoryTreeNode[]`) i renderuje je rekurencyjnie używając komponentu `CategoryAccordion`. Obsługuje również stan pusty, gdy nie ma kategorii do wyświetlenia.

**Główne elementy:**

- Warunkowe renderowanie: `EmptyState` gdy brak kategorii lub lista `CategoryAccordion` dla każdego węzła głównego
- Rekurencyjne renderowanie podkategorii wewnątrz `CategoryAccordion`

**Obsługiwane zdarzenia:**

- Brak bezpośrednich zdarzeń (przekazuje je do `CategoryAccordion`)

**Obsługiwana walidacja:**

- Sprawdzenie czy `treeData` nie jest pusta
- Sprawdzenie czy `treeData` jest tablicą

**Typy:**

- Props: `CategoriesTreeProps` z polem `treeData: CategoryTreeNode[]`

**Propsy:**

```typescript
interface CategoriesTreeProps {
  treeData: CategoryTreeNode[];
}
```

### CategoryAccordion

**Opis komponentu:**
Rekurencyjny komponent wyświetlający pojedynczą kategorię w formie Accordion. Komponent wykorzystuje `Accordion` z Shadcn/ui do obsługi rozwinięcia/zwinięcia. Gdy kategoria ma dzieci, są one renderowane rekurencyjnie wewnątrz `AccordionContent`. Komponent wyświetla nazwę kategorii oraz statystyki (liczbę produktów i pozycji paragonów).

**Główne elementy:**

- `AccordionItem` (Shadcn/ui) - kontener dla pojedynczej kategorii
- `AccordionTrigger` (Shadcn/ui) - klikalny nagłówek z nazwą kategorii i statystykami
- `AccordionContent` (Shadcn/ui) - zawartość rozwinięta z podkategoriami
- Rekurencyjne wywołanie `CategoryAccordion` dla każdego dziecka
- `EmptyState` gdy kategoria nie ma dzieci

**Obsługiwane zdarzenia:**

- `onClick` na `AccordionTrigger` - rozwija/zwija kategorię (obsługiwane przez Shadcn/ui Accordion)

**Obsługiwana walidacja:**

- Sprawdzenie czy kategoria ma dzieci przed renderowaniem `AccordionContent`
- Sprawdzenie czy `children` jest tablicą

**Typy:**

- Props: `CategoryAccordionProps` z polem `node: CategoryTreeNode`

**Propsy:**

```typescript
interface CategoryAccordionProps {
  node: CategoryTreeNode;
  level?: number; // opcjonalny poziom zagnieżdżenia dla stylowania
}
```

### LoadingState

**Opis komponentu:**
Komponent wyświetlający stan ładowania podczas pobierania danych z API. Wykorzystuje komponenty `Skeleton` z Shadcn/ui do symulacji struktury drzewa podczas ładowania.

**Główne elementy:**

- Kontener z klasami: `rounded-md border p-6 space-y-4`
- Wiele komponentów `Skeleton` symulujących strukturę Accordion
- Skeleton dla nagłówka (klasy: `h-8 w-[200px]`)
- Skeleton dla statystyk (klasy: `h-4 w-[100px]`)
- Skeleton dla zawartości (klasy: `h-4 w-full`)

**Obsługiwane zdarzenia:**

- Brak

**Obsługiwana walidacja:**

- Brak

**Typy:**

- Props: brak

**Propsy:**

- Brak

### ErrorState

**Opis komponentu:**
Komponent wyświetlający komunikat błędu oraz przycisk do ponowienia próby pobrania danych. Wyświetlany jest gdy wystąpi błąd podczas pobierania kategorii z API.

**Główne elementy:**

- Kontener z klasami: `rounded-md border border-destructive/50 p-4 text-destructive`
- Komunikat błędu z `error.message`
- Przycisk "Spróbuj ponownie" (`Button` z Shadcn/ui) wywołujący `refetch`

**Obsługiwane zdarzenia:**

- `onClick` na przycisku "Spróbuj ponownie" - wywołuje `refetch()` z hooka `useCategories`

**Obsługiwana walidacja:**

- Sprawdzenie czy `error` nie jest `null`

**Typy:**

- Props: `ErrorStateProps` z polami `error: Error` i `onRetry: () => void`

**Propsy:**

```typescript
interface ErrorStateProps {
  error: Error;
  onRetry: () => void;
}
```

## 5. Typy

### Typy z API (DTOs)

**CategoryResponse** (z `astro/src/types.ts`):

```typescript
export interface CategoryResponse
  extends Pick<Category, 'id' | 'name' | 'parent_id' | 'created_at'> {
  children: CategoryResponse[]; // UWAGA: Backend nie zwraca tego pola, będzie budowane po stronie frontendu
  products_count: number;
  bill_items_count: number;
}
```

**CategoryListResponse** (z `astro/src/types.ts`):

```typescript
export type CategoryListResponse = PaginatedResponse<CategoryResponse>;
```

**PaginatedResponse** (z `astro/src/types.ts`):

```typescript
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}
```

### ViewModel - Typy dla widoku

**CategoryTreeNode:**
Typ reprezentujący węzeł w drzewie kategorii. Zawiera wszystkie dane kategorii oraz tablicę dzieci (również typu `CategoryTreeNode`), tworząc rekurencyjną strukturę drzewiastą.

```typescript
export interface CategoryTreeNode {
  id: number;
  name: string;
  parent_id: number | null;
  created_at: string;
  products_count: number;
  bill_items_count: number;
  children: CategoryTreeNode[];
}
```

**Szczegółowy opis pól:**

- `id: number` - unikalny identyfikator kategorii (z bazy danych)
- `name: string` - nazwa kategorii (np. "Jedzenie i Napoje", "Nabiał i Jaja")
- `parent_id: number | null` - ID kategorii nadrzędnej, `null` dla kategorii głównych (root)
- `created_at: string` - data utworzenia kategorii w formacie ISO 8601
- `products_count: number` - liczba produktów przypisanych do kategorii (z tabeli `indexes`)
- `bill_items_count: number` - liczba pozycji paragonów przypisanych do kategorii (z tabeli `bill_items`)
- `children: CategoryTreeNode[]` - tablica podkategorii (rekurencyjna struktura)

**Funkcja transformująca:**
Funkcja `buildCategoryTree` przekształca płaską listę `CategoryResponse[]` (z `parent_id`) w strukturę drzewiastą `CategoryTreeNode[]`:

```typescript
function buildCategoryTree(categories: CategoryResponse[]): CategoryTreeNode[] {
  // 1. Utworzenie mapy kategorii po ID dla szybkiego dostępu
  const categoryMap = new Map<number, CategoryTreeNode>();
  const rootCategories: CategoryTreeNode[] = [];

  // 2. Konwersja wszystkich kategorii na CategoryTreeNode z pustą tablicą children
  categories.forEach((cat) => {
    categoryMap.set(cat.id, {
      id: cat.id,
      name: cat.name,
      parent_id: cat.parent_id,
      created_at: cat.created_at,
      products_count: cat.products_count,
      bill_items_count: cat.bill_items_count,
      children: [],
    });
  });

  // 3. Budowanie relacji parent-child
  categories.forEach((cat) => {
    const node = categoryMap.get(cat.id)!;
    if (cat.parent_id === null) {
      rootCategories.push(node);
    } else {
      const parent = categoryMap.get(cat.parent_id);
      if (parent) {
        parent.children.push(node);
      }
    }
  });

  // 4. Sortowanie dzieci alfabetycznie (opcjonalne)
  const sortChildren = (node: CategoryTreeNode) => {
    node.children.sort((a, b) => a.name.localeCompare(b.name));
    node.children.forEach(sortChildren);
  };
  rootCategories.forEach(sortChildren);

  return rootCategories;
}
```

## 6. Zarządzanie stanem

Widok wykorzystuje custom hook `useCategories` do zarządzania stanem pobierania danych z API. Hook zarządza następującymi stanami:

**Stany zarządzane przez `useCategories`:**

- `data: CategoryResponse[]` - płaska lista kategorii z API
- `total: number` - całkowita liczba kategorii
- `isLoading: boolean` - stan ładowania
- `error: Error | null` - błąd pobierania danych
- `skip: number` - offset dla paginacji (domyślnie 0)
- `limit: number` - limit wyników (domyślnie 100)

**Transformacja danych:**
Komponent `CategoriesView` wykorzystuje funkcję `buildCategoryTree` do transformacji płaskiej listy `data` w strukturę drzewiastą `CategoryTreeNode[]`. Transformacja odbywa się w `useMemo` dla optymalizacji wydajności:

```typescript
const treeData = useMemo(() => {
  if (!data || data.length === 0) return [];
  return buildCategoryTree(data);
}, [data]);
```

**Stan lokalny komponentu:**

- Brak dodatkowego stanu lokalnego - wszystkie dane pochodzą z hooka `useCategories`

**Custom hook:**
Nie jest wymagany nowy custom hook, istniejący `useCategories` jest wystarczający. Można rozważyć stworzenie hooka `useCategoryTree` w przyszłości, jeśli logika transformacji będzie używana w innych miejscach aplikacji.

## 7. Integracja API

**Endpoint:** `GET /api/categories`

**Typ żądania:** `CategoriesQueryParams` (z `astro/src/types.ts`):

```typescript
export interface CategoriesQueryParams {
  skip?: number;
  limit?: number;
  parent_id?: number; // opcjonalne, nieużywane w tym widoku
  include_children?: boolean; // opcjonalne, nieużywane w tym widoku
}
```

**Typ odpowiedzi:** `CategoryListResponse` (z `astro/src/types.ts`):

```typescript
export type CategoryListResponse = PaginatedResponse<CategoryResponse>;
```

**Struktura odpowiedzi z backendu:**
Backend zwraca płaską listę kategorii z następującymi polami dla każdej kategorii:

- `id: number` - ID kategorii
- `name: string` - nazwa kategorii
- `parent_id: number | null` - ID kategorii nadrzędnej (null dla root)
- `created_at: string` - data utworzenia
- `products_count: number` - liczba produktów
- `bill_items_count: number` - liczba pozycji paragonów

**Przykładowa odpowiedź:**

```json
{
  "items": [
    {
      "id": 4,
      "name": "Jedzenie i Napoje",
      "parent_id": null,
      "created_at": "2025-12-10T18:59:54.770642Z",
      "products_count": 0,
      "bill_items_count": 2
    },
    {
      "id": 17,
      "name": "Nabiał i Jaja",
      "parent_id": 4,
      "created_at": "2025-12-10T18:59:54.770642Z",
      "products_count": 1,
      "bill_items_count": 16
    }
  ],
  "total": 72,
  "skip": 0,
  "limit": 100
}
```

**Funkcja API:**
Funkcja `getCategories` z `astro/src/lib/services/categories.ts` jest używana do pobierania danych. Funkcja przyjmuje `CategoriesQueryParams` i zwraca `Promise<CategoryListResponse>`.

**Autoryzacja:**
Endpoint wymaga JWT tokenu w headerze `Authorization: Bearer <token>`. Token jest automatycznie dodawany przez funkcję `apiFetch` w `astro/src/lib/api-client.ts`.

## 8. Interakcje użytkownika

### Rozwinięcie/zwinięcie kategorii

**Akcja:** Użytkownik klika na nagłówek kategorii w Accordion

**Oczekiwany wynik:**

- Kategoria rozwija się, ukazując swoje podkategorie (jeśli istnieją)
- Ikona chevron obraca się, wskazując stan rozwinięcia
- Animacja płynnego rozwinięcia/zwinięcia (obsługiwana przez Shadcn/ui Accordion)

**Implementacja:**

- Użycie komponentu `Accordion` z Shadcn/ui z typem `"single"` lub `"multiple"`
- Dla lepszego UX, zalecane jest `type="multiple"`, aby użytkownik mógł rozwijać wiele kategorii jednocześnie

### Przeglądanie hierarchii

**Akcja:** Użytkownik przewija stronę i rozwija różne kategorie

**Oczekiwany wynik:**

- Użytkownik może swobodnie przeglądać strukturę kategorii
- Stan rozwinięcia kategorii jest zachowywany podczas przewijania (nie resetuje się)
- Widok jest responsywny i działa poprawnie na urządzeniach mobilnych

### Obsługa pustego stanu

**Akcja:** Użytkownik otwiera widok, gdy nie ma żadnych kategorii w systemie

**Oczekiwany wynik:**

- Wyświetlany jest komunikat "Nie znaleziono kategorii" zamiast pustego widoku
- Komunikat jest wyśrodkowany i czytelny

## 9. Warunki i walidacja

### Warunki weryfikowane przez interfejs

**1. Walidacja danych z API:**

- **Komponent:** `CategoriesView`
- **Warunek:** Sprawdzenie czy `data` nie jest `null` lub `undefined`
- **Wpływ na stan:** Jeśli dane są nieprawidłowe, wyświetlany jest `ErrorState`

**2. Walidacja pustej listy:**

- **Komponent:** `CategoriesTree`
- **Warunek:** Sprawdzenie czy `treeData.length === 0`
- **Wpływ na stan:** Wyświetlany jest `EmptyState` zamiast drzewa

**3. Walidacja struktury drzewa:**

- **Komponent:** `buildCategoryTree` (funkcja pomocnicza)
- **Warunek:** Sprawdzenie czy wszystkie `parent_id` wskazują na istniejące kategorie
- **Wpływ na stan:** Jeśli kategoria ma nieprawidłowy `parent_id`, jest traktowana jako root (zostaje dodana do `rootCategories`)

**4. Walidacja stanu ładowania:**

- **Komponent:** `CategoriesView`
- **Warunek:** Sprawdzenie `isLoading === true`
- **Wpływ na stan:** Wyświetlany jest `LoadingState` zamiast drzewa

**5. Walidacja błędu:**

- **Komponent:** `CategoriesView`
- **Warunek:** Sprawdzenie czy `error !== null`
- **Wpływ na stan:** Wyświetlany jest `ErrorState` z możliwością ponowienia próby

### Warunki API (weryfikowane przez backend)

**1. Autoryzacja:**

- **Warunek:** Wymagany ważny JWT token
- **Błąd:** 401 Unauthorized
- **Obsługa frontendu:** Przekierowanie do strony logowania (obsługiwane przez middleware)

**2. Walidacja parametrów:**

- **Warunek:** `skip >= 0`, `limit >= 1 && limit <= 100`
- **Błąd:** 400 Bad Request
- **Obsługa frontendu:** Wyświetlenie `ErrorState` z komunikatem błędu

**3. Błąd serwera:**

- **Warunek:** Błąd bazy danych lub inny błąd serwera
- **Błąd:** 500 Internal Server Error
- **Obsługa frontendu:** Wyświetlenie `ErrorState` z możliwością ponowienia próby

## 10. Obsługa błędów

### Scenariusze błędów i ich obsługa

**1. Błąd sieci (Network Error):**

- **Przyczyna:** Brak połączenia z internetem, timeout, błąd CORS
- **Obsługa:**
  - Wyświetlenie `ErrorState` z komunikatem "Błąd połączenia z serwerem"
  - Przycisk "Spróbuj ponownie" wywołuje `refetch()`
- **Komponent:** `ErrorState`

**2. Błąd autoryzacji (401 Unauthorized):**

- **Przyczyna:** Wygasły lub nieprawidłowy JWT token
- **Obsługa:**
  - Przekierowanie do strony logowania (obsługiwane przez middleware)
  - Jeśli przekierowanie nie działa, wyświetlenie `ErrorState` z komunikatem "Sesja wygasła"
- **Komponent:** Middleware + `ErrorState` (fallback)

**3. Błąd walidacji (400 Bad Request):**

- **Przyczyna:** Nieprawidłowe parametry zapytania
- **Obsługa:**
  - Wyświetlenie `ErrorState` z komunikatem błędu z API
  - Logowanie błędu do konsoli dla debugowania
- **Komponent:** `ErrorState`

**4. Błąd serwera (500 Internal Server Error):**

- **Przyczyna:** Błąd bazy danych, błąd aplikacji backendowej
- **Obsługa:**
  - Wyświetlenie `ErrorState` z komunikatem "Błąd serwera. Spróbuj ponownie później"
  - Przycisk "Spróbuj ponownie" wywołuje `refetch()`
- **Komponent:** `ErrorState`

**5. Pusta odpowiedź:**

- **Przyczyna:** API zwraca pustą listę kategorii
- **Obsługa:**
  - Wyświetlenie `EmptyState` z komunikatem "Nie znaleziono kategorii"
  - Nie jest to błąd, ale normalny stan aplikacji
- **Komponent:** `CategoriesTree` -> `EmptyState`

**6. Nieprawidłowa struktura danych:**

- **Przyczyna:** API zwraca dane w nieoczekiwanym formacie
- **Obsługa:**
  - Walidacja struktury danych przed budowaniem drzewa
  - Wyświetlenie `ErrorState` z komunikatem "Nieprawidłowy format danych"
  - Logowanie szczegółów błędu do konsoli
- **Komponent:** `CategoriesView` -> `ErrorState`

**7. Błąd transformacji drzewa:**

- **Przyczyna:** Błąd w funkcji `buildCategoryTree` (np. cykliczne referencje)
- **Obsługa:**
  - Try-catch wokół `buildCategoryTree`
  - Wyświetlenie `ErrorState` z komunikatem "Błąd przetwarzania danych"
  - Logowanie szczegółów błędu do konsoli
- **Komponent:** `CategoriesView` -> `ErrorState`

### Logowanie błędów

Wszystkie błędy powinny być logowane do konsoli przeglądarki dla celów debugowania:

```typescript
console.error('CategoriesView error:', error);
```

W produkcji można rozważyć integrację z systemem monitoringu błędów (np. Sentry).

## 11. Kroki implementacji

### Krok 1: Instalacja komponentu Accordion z Shadcn/ui

```bash
cd astro
npx shadcn@latest add accordion
```

**Weryfikacja:** Sprawdzenie czy plik `astro/src/components/ui/accordion.tsx` został utworzony.

### Krok 2: Utworzenie typu ViewModel CategoryTreeNode

**Plik:** `astro/src/types.ts`

**Akcja:** Dodanie interfejsu `CategoryTreeNode` do pliku typów:

```typescript
export interface CategoryTreeNode {
  id: number;
  name: string;
  parent_id: number | null;
  created_at: string;
  products_count: number;
  bill_items_count: number;
  children: CategoryTreeNode[];
}
```

**Weryfikacja:** Sprawdzenie czy typ jest dostępny w innych plikach poprzez import.

### Krok 3: Utworzenie funkcji pomocniczej buildCategoryTree

**Plik:** `astro/src/lib/utils/category-tree.ts` (nowy plik)

**Akcja:** Utworzenie funkcji `buildCategoryTree` transformującej płaską listę w drzewo:

```typescript
import type { CategoryResponse, CategoryTreeNode } from '@/types';

export function buildCategoryTree(
  categories: CategoryResponse[]
): CategoryTreeNode[] {
  // Implementacja zgodna z sekcją 5. Typy
}
```

**Weryfikacja:**

- Utworzenie testu jednostkowego dla funkcji
- Sprawdzenie czy funkcja poprawnie buduje drzewo dla przykładowych danych

### Krok 4: Utworzenie komponentu CategoryAccordion

**Plik:** `astro/src/components/categories/CategoryAccordion.tsx` (nowy plik)

**Akcja:**

- Utworzenie rekurencyjnego komponentu `CategoryAccordion`
- Implementacja interfejsu zgodnie z sekcją 4
- Użycie komponentu `Accordion` z Shadcn/ui
- Wyświetlenie nazwy kategorii, statystyk (produkty + pozycje) i ikony chevron
- Rekurencyjne renderowanie dzieci

**Weryfikacja:**

- Sprawdzenie czy komponent poprawnie renderuje kategorię z dziećmi
- Sprawdzenie czy rekurencja działa dla głębszych poziomów zagnieżdżenia
- Sprawdzenie czy stan rozwinięcia/zwinięcia działa poprawnie

### Krok 5: Utworzenie komponentu CategoriesTree

**Plik:** `astro/src/components/categories/CategoriesTree.tsx` (nowy plik)

**Akcja:**

- Utworzenie komponentu `CategoriesTree` przyjmującego `treeData: CategoryTreeNode[]`
- Renderowanie listy `CategoryAccordion` dla każdego węzła głównego
- Obsługa stanu pustego (EmptyState)

**Weryfikacja:**

- Sprawdzenie czy komponent poprawnie renderuje drzewo kategorii
- Sprawdzenie czy EmptyState jest wyświetlany gdy `treeData` jest pusta

### Krok 6: Utworzenie komponentu CategoriesHeader

**Plik:** `astro/src/components/categories/CategoriesHeader.tsx` (nowy plik)

**Akcja:**

- Utworzenie komponentu prezentacyjnego z tytułem i opisem
- Stylowanie zgodne z innymi widokami w aplikacji

**Weryfikacja:**

- Sprawdzenie czy nagłówek jest poprawnie wyświetlany

### Krok 7: Utworzenie komponentu LoadingState

**Plik:** `astro/src/components/categories/CategoriesLoadingState.tsx` (nowy plik)

**Akcja:**

- Utworzenie komponentu wyświetlającego skeleton loadery
- Symulacja struktury Accordion podczas ładowania
- Użycie komponentu `Skeleton` z Shadcn/ui

**Weryfikacja:**

- Sprawdzenie czy skeleton loadery są poprawnie wyświetlane podczas ładowania

### Krok 8: Utworzenie komponentu ErrorState

**Plik:** `astro/src/components/categories/CategoriesErrorState.tsx` (nowy plik)

**Akcja:**

- Utworzenie komponentu wyświetlającego komunikat błędu
- Dodanie przycisku "Spróbuj ponownie" wywołującego `onRetry`
- Stylowanie zgodne z systemem designu (destructive colors)

**Weryfikacja:**

- Sprawdzenie czy komunikat błędu jest poprawnie wyświetlany
- Sprawdzenie czy przycisk "Spróbuj ponownie" wywołuje callback

### Krok 9: Aktualizacja komponentu CategoriesView

**Plik:** `astro/src/components/categories/CategoriesView.tsx`

**Akcja:**

- Import nowych komponentów i funkcji pomocniczych
- Dodanie `useMemo` do transformacji danych w drzewo
- Warunkowe renderowanie: LoadingState, ErrorState lub CategoriesTree
- Integracja z `useCategories` hook

**Weryfikacja:**

- Sprawdzenie czy widok poprawnie wyświetla drzewo kategorii
- Sprawdzenie czy stany ładowania i błędu są poprawnie obsługiwane
- Sprawdzenie czy transformacja danych działa poprawnie

### Krok 10: Usunięcie starego komponentu CategoriesTable (opcjonalne)

**Plik:** `astro/src/components/categories/CategoriesTable.tsx`

**Akcja:**

- Usunięcie komponentu, jeśli nie jest używany w innych miejscach
- Lub zachowanie go jako alternatywnego widoku (płaska tabela vs drzewo)

**Weryfikacja:**

- Sprawdzenie czy żadne inne komponenty nie używają `CategoriesTable`

### Krok 11: Testy i weryfikacja

**Akcje:**

- Testowanie widoku z różnymi danymi (puste, z jedną kategorią, z głęboką hierarchią)
- Testowanie responsywności na różnych rozdzielczościach
- Testowanie obsługi błędów (symulacja błędów API)
- Testowanie wydajności dla dużej liczby kategorii (72+ kategorii)

**Weryfikacja:**

- Widok działa poprawnie na desktop i mobile
- Wszystkie stany (loading, error, empty, success) są poprawnie obsługiwane
- Wydajność jest akceptowalna (brak lagów podczas renderowania)

### Krok 12: Optymalizacje (opcjonalne)

**Akcje:**

- Rozważenie użycia `React.memo` dla `CategoryAccordion` jeśli wydajność jest problemem
- Rozważenie wirtualizacji dla bardzo głębokich drzew (react-window)
- Rozważenie cache'owania drzewa kategorii w localStorage (kategorie rzadko się zmieniają)

**Weryfikacja:**

- Pomiar wydajności przed i po optymalizacjach
- Sprawdzenie czy optymalizacje nie psują funkcjonalności
