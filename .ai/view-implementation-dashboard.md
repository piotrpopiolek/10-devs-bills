# Plan implementacji widoku Dashboard

## 1. Przegląd

Widok Dashboard (`/dashboard`) jest głównym ekranem aplikacji Bills, który umożliwia użytkownikom szybki podgląd stanu finansów i aktywności w bieżącym okresie. Widok ma charakter **read-only** i służy do wizualizacji danych zgromadzonych przez bota Telegram podczas przetwarzania paragonów.

Główne funkcjonalności:

- Wyświetlanie wydatków dzisiaj (kwota z raportu dziennego)
- Wyświetlanie wydatków w tym miesiącu (kwota + porównanie do poprzedniego miesiąca)
- Wyświetlanie stanu limitu paragonów (np. 45/100) z paskiem postępu
- Lista 5 ostatnich paragonów z możliwością nawigacji do szczegółów
- Responsywny design (Mobile First)
- Asynchroniczne ładowanie danych z obsługą stanów loading/error dla każdego widgetu niezależnie

## 2. Routing widoku

**Ścieżka:** `/dashboard`

**Plik:** `astro/src/pages/dashboard.astro`

**Struktura:**

- Strona Astro wykorzystuje Layout główny (`Layout.astro`)
- Główny komponent React `DashboardView` jest ładowany z dyrektywą `client:load` (Islands Architecture)
- Strona jest statyczna, ale komponent React zapewnia interaktywność i zarządzanie stanem

**Przykładowa implementacja:**

```astro
---
import Layout from '../layouts/Layout.astro';
import { DashboardView } from '@/components/dashboard/DashboardView';
---

<Layout>
  <DashboardView client:load />
</Layout>
```

## 3. Struktura komponentów

```
DashboardView (React)
├── DashboardHeader (React) - Opcjonalny nagłówek z tytułem
├── DashboardStats (React) - Sekcja ze statystykami
│   ├── StatsCard (React) - Wydatki dzisiaj
│   ├── StatsCard (React) - Wydatki w tym miesiącu (z trendem)
│   └── UsageProgressCard (React) - Stan limitu paragonów
└── RecentBillsSection (React) - Sekcja z ostatnimi paragonami
    └── RecentBillsList (React) - Uproszczona lista/tabela
```

## 4. Szczegóły komponentów

### DashboardView

**Opis komponentu:** Główny komponent widoku Dashboard, który orkiestruje wszystkie sekcje i zarządza stanem ładowania danych z wielu źródeł API. Komponent wykorzystuje custom hook `useDashboard` do pobierania wszystkich potrzebnych danych.

**Główne elementy:**
- Kontener główny z klasami Tailwind (`container mx-auto py-10 px-4 md:px-6 space-y-6`)
- Sekcja `DashboardStats` z komponentami statystyk
- Sekcja `RecentBillsSection` z listą ostatnich paragonów
- Obsługa stanów loading/error dla każdej sekcji niezależnie

**Obsługiwane interakcje:**
- Automatyczne odświeżanie danych przy montowaniu komponentu
- Obsługa błędów na poziomie poszczególnych sekcji (błąd jednej sekcji nie blokuje innych)

**Obsługiwana walidacja:**
- Brak walidacji na poziomie komponentu (walidacja odbywa się w serwisach API)

**Typy:**
- Brak własnych typów, wykorzystuje typy z `@/types`

**Propsy:**
- Brak propsów (komponent nie przyjmuje żadnych propsów)

### StatsCard

**Opis komponentu:** Reużywalny komponent prezentacyjny wyświetlający pojedynczą statystykę (etykietę, wartość główną i opcjonalny wskaźnik trendu). Komponent jest używany do wyświetlania wydatków dzisiaj oraz wydatków w tym miesiącu.

**Główne elementy:**
- Kontener z klasami Tailwind (card-like appearance z border i padding)
- Etykieta tekstowa (np. "Wydatki dzisiaj")
- Wartość główna sformatowana jako kwota (np. "124.50 PLN")
- Opcjonalny wskaźnik trendu (ikona strzałki w górę/dół + procentowa zmiana) dla porównania z poprzednim okresem
- Opcjonalny skeleton loader podczas ładowania

**Obsługiwane interakcje:**
- Brak interakcji (komponent prezentacyjny)

**Obsługiwana walidacja:**
- Walidacja wartości numerycznej (jeśli wartość jest ujemna lub NaN, wyświetl "0.00 PLN")
- Walidacja trendu (jeśli brak danych do porównania, ukryj wskaźnik trendu)

**Typy:**

```typescript
interface StatsCardProps {
  label: string;
  value: number | null;
  isLoading?: boolean;
  trend?: {
    value: number; // procentowa zmiana (np. 15.5 dla +15.5%)
    isPositive: boolean; // true jeśli wzrost, false jeśli spadek
  };
  currency?: string; // domyślnie "PLN"
}
```

**Propsy:**
- `label: string` - Etykieta wyświetlana nad wartością
- `value: number | null` - Wartość do wyświetlenia (null podczas ładowania)
- `isLoading?: boolean` - Flaga wskazująca stan ładowania
- `trend?: { value: number; isPositive: boolean }` - Opcjonalne dane trendu
- `currency?: string` - Waluta (domyślnie "PLN")

### UsageProgressCard

**Opis komponentu:** Komponent wyświetlający stan limitu paragonów w modelu freemium. Zawiera pasek postępu, aktualną liczbę użytych paragonów, limit oraz informację o pozostałych paragonach. Pasek zmienia kolor na czerwony, gdy limit przekracza 90%.

**Główne elementy:**
- Kontener z klasami Tailwind (card-like appearance)
- Nagłówek z tytułem "Limit paragonów"
- Tekst z aktualnym stanem (np. "45 / 100 paragonów")
- Komponent `Progress` z Shadcn/ui do wizualizacji postępu
- Tekst z informacją o pozostałych paragonach (np. "Pozostało: 55 paragonów")
- Opcjonalny skeleton loader podczas ładowania

**Obsługiwane interakcje:**
- Brak interakcji (komponent prezentacyjny)

**Obsługiwana walidacja:**
- Walidacja wartości numerycznych (bills_this_month i monthly_limit muszą być >= 0)
- Obliczenie procentu użycia: `(bills_this_month / monthly_limit) * 100`
- Walidacja koloru paska: czerwony gdy procent >= 90%, żółty gdy >= 75%, zielony w przeciwnym razie
- Walidacja pozostałych paragonów: `remaining_bills = monthly_limit - bills_this_month` (minimum 0)

**Typy:**

```typescript
interface UsageProgressCardProps {
  billsThisMonth: number | null;
  monthlyLimit: number | null;
  isLoading?: boolean;
}
```

**Propsy:**
- `billsThisMonth: number | null` - Liczba przetworzonych paragonów w bieżącym miesiącu
- `monthlyLimit: number | null` - Miesięczny limit paragonów (domyślnie 100)
- `isLoading?: boolean` - Flaga wskazująca stan ładowania

### RecentBillsList

**Opis komponentu:** Komponent wyświetlający uproszczoną listę ostatnich 5 paragonów. Każdy wiersz zawiera podstawowe informacje: data, nazwa sklepu, kwota i status. Kliknięcie w wiersz nawiguje do szczegółów paragonu.

**Główne elementy:**
- Kontener z klasami Tailwind
- Nagłówek sekcji "Ostatnie paragony"
- Tabela lub lista z wierszami paragonów
- Każdy wiersz zawiera:
  - Data paragonu (sformatowana, np. "15.01.2024")
  - Nazwa sklepu (lub "Nieznany sklep" jeśli brak)
  - Kwota (sformatowana, np. "124.50 PLN")
  - Badge ze statusem (używając `BillStatusBadge`)
- Link "Zobacz wszystkie" prowadzący do `/bills`
- Skeleton loader podczas ładowania
- Komunikat "Brak paragonów" gdy lista jest pusta

**Obsługiwane interakcje:**
- Kliknięcie w wiersz tabeli → nawigacja do `/bills/{id}`
- Kliknięcie w link "Zobacz wszystkie" → nawigacja do `/bills`

**Obsługiwana walidacja:**
- Walidacja danych paragonu (jeśli brak shop, wyświetl "Nieznany sklep")
- Walidacja kwoty (jeśli null lub undefined, wyświetl "0.00 PLN")
- Walidacja daty (formatowanie z obsługą błędów parsowania)

**Typy:**

```typescript
interface RecentBillsListProps {
  bills: BillResponse[];
  isLoading: boolean;
  error: Error | null;
  onBillClick: (billId: number) => void;
}
```

**Propsy:**
- `bills: BillResponse[]` - Tablica paragonów do wyświetlenia (maksymalnie 5)
- `isLoading: boolean` - Flaga wskazująca stan ładowania
- `error: Error | null` - Błąd pobierania danych (jeśli wystąpił)
- `onBillClick: (billId: number) => void` - Callback wywoływany przy kliknięciu w wiersz

### DashboardStats

**Opis komponentu:** Komponent kontenerowy grupujący wszystkie karty statystyk w responsywny układ siatki. Na desktopie wyświetla 3 kolumny, na mobile 1 kolumnę.

**Główne elementy:**
- Kontener z klasami Tailwind Grid (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`)
- Trzy instancje komponentów: `StatsCard` (wydatki dzisiaj), `StatsCard` (wydatki miesięczne), `UsageProgressCard`

**Obsługiwane interakcje:**
- Brak interakcji (komponent kontenerowy)

**Obsługiwana walidacja:**
- Brak walidacji (przekazuje dane do komponentów dzieci)

**Typy:**
- Brak własnych typów

**Propsy:**

```typescript
interface DashboardStatsProps {
  dailyExpenses: number | null;
  monthlyExpenses: number | null;
  previousMonthExpenses: number | null;
  usageStats: UsageStats | null;
  isLoadingDaily: boolean;
  isLoadingMonthly: boolean;
  isLoadingUsage: boolean;
}
```

### RecentBillsSection

**Opis komponentu:** Komponent kontenerowy dla sekcji z ostatnimi paragonami. Zawiera nagłówek sekcji i komponent `RecentBillsList`.

**Główne elementy:**
- Kontener z klasami Tailwind
- Nagłówek sekcji "Ostatnie paragony"
- Komponent `RecentBillsList`

**Obsługiwane interakcje:**
- Brak interakcji (komponent kontenerowy)

**Obsługiwana walidacja:**
- Brak walidacji (przekazuje dane do komponentu dziecka)

**Typy:**
- Brak własnych typów

**Propsy:**

```typescript
interface RecentBillsSectionProps {
  bills: BillResponse[];
  isLoading: boolean;
  error: Error | null;
  onBillClick: (billId: number) => void;
}
```

## 5. Typy

### Typy istniejące (z `@/types`)

Widok Dashboard wykorzystuje następujące typy już zdefiniowane w `astro/src/types.ts`:

- `UserProfile` - Profil użytkownika z usage statistics
- `UsageStats` - Statystyki użycia (bills_this_month, monthly_limit, remaining_bills)
- `DailyReportResponse` - Odpowiedź z raportu dziennego
- `MonthlyReportResponse` - Odpowiedź z raportu miesięcznego
- `BillResponse` - Dane paragonu
- `BillListResponse` - Lista paragonów z paginacją
- `ProcessingStatus` - Status przetwarzania paragonu

### Nowe typy ViewModel (opcjonalne)

Jeśli potrzebne są dodatkowe typy ViewModel dla uproszczenia logiki komponentów:

```typescript
// Opcjonalny typ dla danych trendu
interface TrendData {
  value: number; // procentowa zmiana
  isPositive: boolean; // true jeśli wzrost
  previousValue: number; // poprzednia wartość dla kontekstu
}

// Opcjonalny typ dla zunifikowanych danych dashboardu
interface DashboardData {
  dailyExpenses: {
    amount: number | null;
    isLoading: boolean;
    error: Error | null;
  };
  monthlyExpenses: {
    amount: number | null;
    trend: TrendData | null;
    isLoading: boolean;
    error: Error | null;
  };
  usageStats: {
    billsThisMonth: number | null;
    monthlyLimit: number | null;
    remainingBills: number | null;
    isLoading: boolean;
    error: Error | null;
  };
  recentBills: {
    items: BillResponse[];
    isLoading: boolean;
    error: Error | null;
  };
}
```

## 6. Zarządzanie stanem

Widok Dashboard wykorzystuje **custom hook `useDashboard`**, który zarządza stanem wszystkich zapytań API i udostępnia zunifikowany interfejs dla komponentów.

### Custom Hook: useDashboard

**Lokalizacja:** `astro/src/components/hooks/useDashboard.ts`

**Opis:** Hook łączący wszystkie zapytania API potrzebne dla widoku Dashboard. Zarządza stanem ładowania, błędów i danych dla każdego źródła niezależnie.

**Stan zarządzany:**
- Wydatki dzisiaj (z `getDailyReport`)
- Wydatki w tym miesiącu (z `getMonthlyReport`)
- Wydatki z poprzedniego miesiąca (z `getMonthlyReport` dla poprzedniego miesiąca)
- Statystyki użycia (z `getUserProfile`)
- Ostatnie paragony (z `getBills` z limit=5)

**Zwracany interfejs:**

```typescript
interface UseDashboardReturn {
  // Daily expenses
  dailyExpenses: number | null;
  isLoadingDaily: boolean;
  dailyError: Error | null;
  
  // Monthly expenses
  monthlyExpenses: number | null;
  previousMonthExpenses: number | null;
  isLoadingMonthly: boolean;
  monthlyError: Error | null;
  
  // Usage stats
  usageStats: UsageStats | null;
  isLoadingUsage: boolean;
  usageError: Error | null;
  
  // Recent bills
  recentBills: BillResponse[];
  isLoadingBills: boolean;
  billsError: Error | null;
  
  // Refetch functions
  refetchAll: () => Promise<void>;
  refetchDaily: () => Promise<void>;
  refetchMonthly: () => Promise<void>;
  refetchUsage: () => Promise<void>;
  refetchBills: () => Promise<void>;
}
```

**Implementacja:**
- Wykorzystuje `useState` i `useEffect` do zarządzania stanem każdego zapytania
- Każde zapytanie ma własny stan loading i error
- Zapytania są wykonywane równolegle przy montowaniu komponentu
- Funkcje `refetch*` umożliwiają ręczne odświeżanie danych

**Alternatywa (z TanStack Query):**
Jeśli projekt wykorzystuje TanStack Query, hook może być zaimplementowany z użyciem `useQuery` dla każdego źródła danych, co zapewnia automatyczne cache'owanie i retry.

## 7. Integracja API

Widok Dashboard wymaga integracji z następującymi endpointami API:

### 7.1. GET /api/users/me

**Opis:** Pobiera profil użytkownika wraz ze statystykami użycia (limit paragonów).

**Typ żądania:** `GET`

**Query Parameters:** Brak

**Headers:** 
- `Authorization: Bearer {access_token}` (wymagane)

**Typ odpowiedzi:** `UserProfile`

**Struktura odpowiedzi:**

```typescript
{
  id: number;
  external_id: number;
  is_active: boolean;
  created_at: string;
  usage: {
    bills_this_month: number;
    monthly_limit: number;
    remaining_bills: number;
  };
}
```

**Obsługa błędów:**
- `401 Unauthorized` - Brak autoryzacji, przekierowanie do logowania
- `500 Internal Server Error` - Błąd serwera, wyświetlenie komunikatu błędu

**Serwis:** `getUserProfile()` w `astro/src/lib/services/auth.ts` (do utworzenia jeśli nie istnieje)

### 7.2. GET /api/reports/daily

**Opis:** Pobiera raport wydatków dziennych dla dzisiaj.

**Typ żądania:** `GET`

**Query Parameters:**
- `date` (opcjonalny, string ISO 8601, domyślnie dzisiaj) - Data raportu

**Headers:** 
- `Authorization: Bearer {access_token}` (wymagane)

**Typ odpowiedzi:** `DailyReportResponse`

**Struktura odpowiedzi:**

```typescript
{
  date: string; // "2024-01-15"
  total_amount: number; // 125.50
  bills_count: number; // 3
  top_categories: CategorySummary[];
  shops: ShopSummary[];
}
```

**Obsługa błędów:**
- `400 Bad Request` - Nieprawidłowy format daty
- `401 Unauthorized` - Brak autoryzacji
- `500 Internal Server Error` - Błąd serwera

**Serwis:** `getDailyReport(date?: string)` w `astro/src/lib/services/reports.ts` (do utworzenia)

### 7.3. GET /api/reports/monthly

**Opis:** Pobiera raport wydatków miesięcznych dla bieżącego i poprzedniego miesiąca.

**Typ żądania:** `GET`

**Query Parameters:**
- `month` (opcjonalny, string YYYY-MM, domyślnie bieżący miesiąc) - Miesiąc raportu

**Headers:** 
- `Authorization: Bearer {access_token}` (wymagane)

**Typ odpowiedzi:** `MonthlyReportResponse`

**Struktura odpowiedzi:**

```typescript
{
  month: string; // "2024-01"
  total_amount: number; // 3200.75
  bills_count: number; // 45
  daily_average: number; // 103.25
  top_categories: CategorySummary[];
  top_shops: ShopSummary[];
  weekly_breakdown: WeeklyBreakdown[];
}
```

**Obsługa błędów:**
- `400 Bad Request` - Nieprawidłowy format miesiąca
- `401 Unauthorized` - Brak autoryzacji
- `500 Internal Server Error` - Błąd serwera

**Serwis:** `getMonthlyReport(month?: string)` w `astro/src/lib/services/reports.ts` (do utworzenia)

**Uwaga:** Aby uzyskać porównanie z poprzednim miesiącem, należy wykonać dwa zapytania:
1. Dla bieżącego miesiąca: `getMonthlyReport()` (bez parametru)
2. Dla poprzedniego miesiąca: `getMonthlyReport(previousMonth)` (np. "2023-12")

### 7.4. GET /api/bills

**Opis:** Pobiera listę ostatnich 5 paragonów.

**Typ żądania:** `GET`

**Query Parameters:**
- `limit` (wymagany, number, wartość: 5) - Liczba paragonów do pobrania
- `skip` (opcjonalny, number, domyślnie 0) - Liczba paragonów do pominięcia

**Headers:** 
- `Authorization: Bearer {access_token}` (wymagane)

**Typ odpowiedzi:** `BillListResponse`

**Struktura odpowiedzi:**

```typescript
{
  items: BillResponse[];
  total: number;
  skip: number;
  limit: number;
}
```

**Obsługa błędów:**
- `401 Unauthorized` - Brak autoryzacji
- `500 Internal Server Error` - Błąd serwera

**Serwis:** `getBills(params: BillsQueryParams)` w `astro/src/lib/services/bills.ts` (już istnieje)

**Użycie:** `getBills({ limit: 5, skip: 0 })`

## 8. Interakcje użytkownika

### 8.1. Ładowanie widoku

**Akcja:** Użytkownik otwiera stronę `/dashboard`

**Oczekiwany wynik:**
1. Wyświetlenie skeleton loaders dla wszystkich sekcji
2. Równoległe wykonanie wszystkich zapytań API
3. Stopniowe zastępowanie skeleton loaders rzeczywistymi danymi w miarę otrzymywania odpowiedzi
4. Jeśli wszystkie dane załadowane pomyślnie, wyświetlenie pełnego widoku

### 8.2. Kliknięcie w wiersz paragonu

**Akcja:** Użytkownik klika w wiersz w liście ostatnich paragonów

**Oczekiwany wynik:**
1. Nawigacja do `/bills/{id}` (szczegóły paragonu)
2. Przejście płynne (jeśli użyty ClientRouter z Astro)

### 8.3. Kliknięcie w "Zobacz wszystkie"

**Akcja:** Użytkownik klika w link "Zobacz wszystkie" w sekcji ostatnich paragonów

**Oczekiwany wynik:**
1. Nawigacja do `/bills` (lista wszystkich paragonów)

### 8.4. Obsługa błędów ładowania

**Akcja:** Jedno z zapytań API zwraca błąd

**Oczekiwany wynik:**
1. Wyświetlenie komunikatu błędu w odpowiedniej sekcji (np. "Nie udało się pobrać wydatków dzisiaj")
2. Pozostałe sekcje działają normalnie (błąd jednej sekcji nie blokuje innych)
3. Opcjonalnie przycisk "Spróbuj ponownie" do ręcznego odświeżenia

### 8.4. Odświeżanie danych

**Akcja:** Użytkownik odświeża stronę (F5) lub wraca do widoku

**Oczekiwany wynik:**
1. Wykonanie wszystkich zapytań API ponownie
2. Wyświetlenie skeleton loaders podczas ładowania
3. Aktualizacja danych po otrzymaniu odpowiedzi

## 9. Warunki i walidacja

### 9.1. Walidacja danych z API

**Wydatki dzienne:**
- Jeśli `total_amount` jest null lub undefined, wyświetl "0.00 PLN"
- Jeśli `date` jest nieprawidłowa, użyj dzisiejszej daty jako fallback

**Wydatki miesięczne:**
- Jeśli `total_amount` jest null lub undefined, wyświetl "0.00 PLN"
- Jeśli brak danych z poprzedniego miesiąca, ukryj wskaźnik trendu
- Obliczenie trendu: `((current - previous) / previous) * 100`
- Jeśli poprzedni miesiąc miał 0 wydatków, nie wyświetlaj trendu (dzielenie przez zero)

**Statystyki użycia:**
- Jeśli `bills_this_month` jest null, wyświetl "0"
- Jeśli `monthly_limit` jest null, użyj wartości domyślnej 100
- Obliczenie procentu: `(bills_this_month / monthly_limit) * 100` (maksymalnie 100%)
- Obliczenie pozostałych: `Math.max(0, monthly_limit - bills_this_month)`

**Ostatnie paragony:**
- Jeśli lista jest pusta, wyświetl komunikat "Brak paragonów"
- Jeśli `shop` jest null, wyświetl "Nieznany sklep"
- Jeśli `total_amount` jest null, wyświetl "0.00 PLN"
- Formatowanie daty: użyj `Intl.DateTimeFormat` lub biblioteki date-fns

### 9.2. Walidacja stanów ładowania

**Skeleton loaders:**
- Wyświetlaj skeleton loader tylko gdy `isLoading === true`
- Ukryj skeleton loader gdy dane są załadowane (nawet jeśli są puste)

**Obsługa błędów:**
- Jeśli `error !== null`, wyświetl komunikat błędu zamiast danych
- Komunikat błędu powinien być czytelny dla użytkownika (np. "Nie udało się pobrać danych")

### 9.3. Walidacja responsywności

**Desktop (lg+):**
- Statystyki w układzie 3 kolumn
- Pełna szerokość tabeli z ostatnimi paragonami

**Tablet (md):**
- Statystyki w układzie 2 kolumn
- Pełna szerokość tabeli

**Mobile (<md):**
- Statystyki w układzie 1 kolumny
- Tabela z przewijaniem poziomym (jeśli potrzebne)

## 10. Obsługa błędów

### 10.1. Błędy autoryzacji (401)

**Scenariusz:** Token wygasł lub jest nieprawidłowy

**Obsługa:**
1. `apiFetch` automatycznie próbuje odświeżyć token
2. Jeśli odświeżenie się nie powiedzie, przekierowanie do `/` (strona główna)
3. Wyświetlenie komunikatu: "Sesja wygasła. Zaloguj się ponownie."

**Implementacja:** Obsługa w `apiFetch` (już istnieje)

### 10.2. Błędy serwera (500)

**Scenariusz:** Błąd po stronie serwera API

**Obsługa:**
1. Wyświetlenie komunikatu błędu w odpowiedniej sekcji
2. Przycisk "Spróbuj ponownie" do ręcznego odświeżenia
3. Logowanie błędu do konsoli dla debugowania

**Przykład komunikatu:** "Wystąpił błąd podczas pobierania danych. Spróbuj ponownie za chwilę."

### 10.3. Błędy sieci (Network Error)

**Scenariusz:** Brak połączenia z internetem lub timeout

**Obsługa:**
1. Wyświetlenie komunikatu: "Brak połączenia z internetem. Sprawdź swoje połączenie."
2. Przycisk "Spróbuj ponownie" do ponownej próby
3. Automatyczna retry po 5 sekundach (opcjonalnie)

### 10.4. Błędy parsowania danych

**Scenariusz:** API zwróciło nieprawidłowy format danych

**Obsługa:**
1. Walidacja struktury odpowiedzi przed użyciem
2. Jeśli struktura jest nieprawidłowa, wyświetl komunikat błędu
3. Logowanie szczegółów błędu do konsoli

### 10.5. Częściowe błędy

**Scenariusz:** Jedno z zapytań API zwraca błąd, ale pozostałe działają

**Obsługa:**
1. Wyświetlenie błędu tylko w odpowiedniej sekcji
2. Pozostałe sekcje działają normalnie
3. Użytkownik może nadal korzystać z funkcjonalności, które działają

**Przykład:** Jeśli raport dzienny zwraca błąd, ale raport miesięczny działa, wyświetl błąd tylko w karcie "Wydatki dzisiaj", a karta "Wydatki w tym miesiącu" działa normalnie.

### 10.6. Puste dane

**Scenariusz:** Użytkownik nie ma jeszcze żadnych paragonów

**Obsługa:**
1. Wyświetl "0.00 PLN" dla wydatków
2. Wyświetl "0 / 100 paragonów" dla limitu
3. Wyświetl komunikat "Brak paragonów" w sekcji ostatnich paragonów
4. Opcjonalnie link do instrukcji, jak dodać pierwszy paragon

## 11. Kroki implementacji

### Krok 1: Utworzenie serwisów API

1. Utworzyć plik `astro/src/lib/services/reports.ts` z funkcjami:
   - `getDailyReport(date?: string): Promise<DailyReportResponse>`
   - `getMonthlyReport(month?: string): Promise<MonthlyReportResponse>`
2. Sprawdzić czy istnieje `getUserProfile()` w `astro/src/lib/services/auth.ts`, jeśli nie, utworzyć
3. Przetestować serwisy w izolacji (sprawdzenie typów i obsługi błędów)

### Krok 2: Utworzenie custom hooka useDashboard

1. Utworzyć plik `astro/src/components/hooks/useDashboard.ts`
2. Zaimplementować hook z zarządzaniem stanem dla wszystkich zapytań
3. Dodać funkcje refetch dla każdego źródła danych
4. Przetestować hook (sprawdzenie stanów loading, error, data)

### Krok 3: Utworzenie komponentu StatsCard

1. Utworzyć plik `astro/src/components/dashboard/StatsCard.tsx`
2. Zaimplementować komponent z obsługą skeleton loadera
3. Dodać obsługę wskaźnika trendu (opcjonalnie)
4. Dodać formatowanie kwoty (funkcja pomocnicza)
5. Przetestować komponent z różnymi wartościami i stanami

### Krok 4: Utworzenie komponentu UsageProgressCard

1. Utworzyć plik `astro/src/components/dashboard/UsageProgressCard.tsx`
2. Zaimplementować komponent z użyciem `Progress` z Shadcn/ui
3. Dodać logikę zmiany koloru paska (czerwony >= 90%, żółty >= 75%, zielony < 75%)
4. Dodać formatowanie tekstu (np. "45 / 100 paragonów")
5. Przetestować komponent z różnymi wartościami użycia

### Krok 5: Utworzenie komponentu RecentBillsList

1. Utworzyć plik `astro/src/components/dashboard/RecentBillsList.tsx`
2. Zaimplementować listę/tabelę z użyciem komponentów Shadcn/ui (`Table`)
3. Dodać obsługę kliknięcia w wiersz (nawigacja do szczegółów)
4. Dodać link "Zobacz wszystkie" prowadzący do `/bills`
5. Dodać obsługę stanów: loading (skeleton), empty, error
6. Przetestować komponent z różnymi danymi

### Krok 6: Utworzenie komponentów kontenerowych

1. Utworzyć plik `astro/src/components/dashboard/DashboardStats.tsx`
2. Utworzyć plik `astro/src/components/dashboard/RecentBillsSection.tsx`
3. Zaimplementować komponenty z responsywnym układem Grid
4. Połączyć komponenty dzieci (StatsCard, UsageProgressCard, RecentBillsList)

### Krok 7: Utworzenie głównego komponentu DashboardView

1. Utworzyć plik `astro/src/components/dashboard/DashboardView.tsx`
2. Zaimplementować komponent z użyciem hooka `useDashboard`
3. Połączyć wszystkie sekcje (DashboardStats, RecentBillsSection)
4. Dodać obsługę błędów na poziomie sekcji
5. Dodać nagłówek widoku (opcjonalnie)

### Krok 8: Utworzenie strony Astro

1. Utworzyć plik `astro/src/pages/dashboard.astro`
2. Zaimportować Layout i DashboardView
3. Dodać dyrektywę `client:load` do DashboardView
4. Dodać meta tagi (opcjonalnie, dla SEO)

### Krok 9: Utworzenie funkcji pomocniczych

1. Utworzyć plik `astro/src/lib/utils/formatting.ts` (jeśli nie istnieje) z funkcjami:
   - `formatCurrency(amount: number, currency?: string): string`
   - `formatDate(date: string | Date): string`
   - `calculateTrend(current: number, previous: number): TrendData | null`
2. Dodać testy jednostkowe dla funkcji pomocniczych (opcjonalnie)

### Krok 10: Stylowanie i responsywność

1. Sprawdzić responsywność na różnych rozdzielczościach
2. Dostosować układ Grid dla mobile/tablet/desktop
3. Sprawdzić dostępność (a11y) - aria-labels, kontrast kolorów
4. Sprawdzić działanie w trybie ciemnym (dark mode)

### Krok 11: Testowanie

1. Przetestować wszystkie scenariusze:
   - Pomyślne ładowanie wszystkich danych
   - Częściowe błędy (jeden endpoint zwraca błąd)
   - Wszystkie błędy
   - Puste dane (nowy użytkownik)
   - Różne wartości użycia limitu (0%, 50%, 90%, 100%)
2. Przetestować interakcje:
   - Kliknięcie w wiersz paragonu
   - Kliknięcie w "Zobacz wszystkie"
   - Odświeżanie strony
3. Przetestować responsywność na różnych urządzeniach

### Krok 12: Optymalizacja i poprawki

1. Sprawdzić wydajność (czas ładowania, liczba zapytań)
2. Dodać memoization jeśli potrzebne (React.memo, useMemo)
3. Sprawdzić zgodność z linterem
4. Poprawić błędy i ostrzeżenia
5. Dodać komentarze w kodzie (jeśli potrzebne)

### Krok 13: Dokumentacja

1. Zaktualizować dokumentację komponentów (jeśli istnieje)
2. Dodać przykłady użycia w Storybook (jeśli używany)
3. Zaktualizować README z informacją o nowym widoku (opcjonalnie)

