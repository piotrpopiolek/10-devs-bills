# Architektura UI dla Bills

## 1. Przegląd struktury UI

Architektura interfejsu użytkownika aplikacji **Bills** została zaprojektowana zgodnie z podejściem **Mobile First**, kładąc nacisk na czytelność i szybkość działania. System oparty jest na architekturze hybrydowej:
- **Astro 5** odpowiada za szkielet aplikacji (Shell), routing, SEO oraz wstępne renderowanie statycznych części (Layout, Sidebar).
- **React 19** wykorzystywany jest w formie "wysp" (Islands) dla interaktywnych elementów wymagających zarządzania stanem i komunikacji z API (Dashboard, Tabele danych, Filtrowanie).

Aplikacja działa w trybie **"Read-Only"**, służąc do wizualizacji danych zgromadzonych przez bota Telegram. Główny nacisk położony jest na przejrzystą prezentację wydatków, hierarchię informacji oraz monitorowanie limitów konta Freemium.

Stylistyka oparta jest na bibliotece **Shadcn/ui** z wykorzystaniem **Tailwind CSS v4**, co zapewnia spójność, dostępność (a11y) oraz natywne wsparcie dla trybu ciemnego (Dark Mode).

## 2. Lista widoków

### 2.1. Landing Page (Publiczny)
- **Nazwa:** Strona Główna
- **Ścieżka:** `/`
- **Główny cel:** Informacja dla niezalogowanych użytkowników i punkt wejścia.
- **Kluczowe informacje:** Krótki opis aplikacji, instrukcja logowania ("Wejdź na Telegram i wpisz /login").
- **Kluczowe komponenty:** `HeroSection`, `InstructionSteps`, przycisk "Otwórz w Telegramie".
- **UX/Bezpieczeństwo:** Strona statyczna, brak dostępu do danych wrażliwych. Przekierowuje zalogowanych użytkowników bezpośrednio do Dashboardu.

### 2.2. Weryfikacja Autoryzacji
- **Nazwa:** Weryfikacja
- **Ścieżka:** `/auth/verify`
- **Główny cel:** Przetworzenie tokena "Magic Link" z adresu URL i ustanowienie sesji.
- **Kluczowe informacje:** Status weryfikacji (Spinner ładowania -> Sukces lub Błąd).
- **Kluczowe komponenty:** `LoadingSpinner`, `ErrorMessage` (w przypadku wygaśnięcia linku).
- **UX/Bezpieczeństwo:** Widok przejściowy. Token jest walidowany przez API, a po sukcesie następuje "wymiana" na Access/Refresh Token (zapisywane bezpiecznie) i przekierowanie do Dashboardu.

### 2.3. Dashboard (Pulpit)
- **Nazwa:** Dashboard
- **Ścieżka:** `/dashboard`
- **Główny cel:** Szybki podgląd stanu finansów i aktywności w bieżącym okresie.
- **Kluczowe informacje:**
    - Wydatki dzisiaj (kwota).
    - Wydatki w tym miesiącu (kwota + porównanie do poprzedniego).
    - Stan limitu paragonów (np. 45/100).
    - Lista 5 ostatnich paragonów.
- **Kluczowe komponenty:** `StatsCard`, `UsageProgressBar`, `RecentBillsList` (uproszczona tabela).
- **UX/Bezpieczeństwo:** Dane ładowane asynchronicznie (Skeleton loading). Błędy ładowania pojedynczych widgetów nie blokują całego widoku.

### 2.4. Lista Paragonów
- **Nazwa:** Twoje Paragony
- **Ścieżka:** `/bills`
- **Główny cel:** Przeglądanie historii wszystkich zakupów z możliwością filtrowania.
- **Kluczowe informacje:** Data, Sklep, Kwota, Status (Przetworzony/Weryfikacja), Liczba pozycji.
- **Kluczowe komponenty:** `DataTable` (z sortowaniem i paginacją), `DateRangePicker`, `StatusBadge`.
- **UX/Bezpieczeństwo:** Paginacja Server-side dla wydajności przy dużej liczbie rekordów. Filtrowanie odbywa się po stronie API.

### 2.5. Szczegóły Paragonu
- **Nazwa:** Paragon [ID]
- **Ścieżka:** `/bills/[id]`
- **Główny cel:** Weryfikacja poprawności odczytu konkretnego paragonu.
- **Kluczowe informacje:**
    - Zdjęcie paragonu (z możliwością powiększenia).
    - Metadane (Data, Sklep, Suma).
    - Lista pozycji (Nazwa z paragonu, Produkt rozpoznany, Cena, Ilość).
    - Wskaźnik pewności (Confidence Score) dla pozycji.
- **Kluczowe komponenty:** `BillImageViewer` (z zoomem), `BillItemsTable`, `ConfidenceIndicator` (np. kolorowa kropka: zielona/żółta/czerwona).
- **UX/Bezpieczeństwo:** Lazy loading zdjęcia paragonu. Jeśli status paragonu to "Processing", automatyczne odświeżanie (polling) statusu.

### 2.6. Lista Sklepów
- **Nazwa:** Sklepy
- **Ścieżka:** `/shops`
- **Główny cel:** Analiza, gdzie użytkownik najczęściej robi zakupy.
- **Kluczowe informacje:** Nazwa sklepu, Liczba paragonów, Łączna suma wydatków.
- **Kluczowe komponenty:** `ShopCard` lub `ShopsTable`, Wyszukiwarka sklepów.
- **UX/Bezpieczeństwo:** Sortowanie wg wydanej kwoty pozwala szybko zidentyfikować główne miejsca wydatków.

### 2.7. Szczegóły Sklepu
- **Nazwa:** Sklep [Nazwa]
- **Ścieżka:** `/shops/[id]`
- **Główny cel:** Historia interakcji z konkretnym sklepem.
- **Kluczowe informacje:** Łączne wydatki w tym sklepie, średnia wartość paragonu, lista paragonów z tego sklepu.
- **Kluczowe komponenty:** `AggregateStats`, `BillsList` (przefiltrowana dla sklepu).

### 2.8. Katalog Produktów
- **Nazwa:** Produkty
- **Ścieżka:** `/products`
- **Główny cel:** Przegląd bazy wiedzy o produktach i ich kategoryzacji.
- **Kluczowe informacje:** Nazwa znormalizowana, Kategoria, Synonimy (jak OCR odczytywał ten produkt).
- **Kluczowe komponenty:** `ProductsTable`, `SynonymsList` (tagi/badges).
- **UX/Bezpieczeństwo:** Wyszukiwanie "live" (debounced) po nazwie produktu.

### 2.9. Struktura Kategorii
- **Nazwa:** Kategorie
- **Ścieżka:** `/categories`
- **Główny cel:** Wizualizacja hierarchii wydatków.
- **Kluczowe informacje:** Drzewo kategorii (Rodzic -> Dzieci), liczba przypisanych produktów.
- **Kluczowe komponenty:** `CategoryTree` (Accordion lub TreeView).

## 3. Mapa podróży użytkownika

1.  **Inicjacja:** Użytkownik otwiera aplikację poprzez link z Telegrama (`/auth/verify?token=...`).
2.  **Onboarding/Dashboard:** Po sukcesie trafia na `/dashboard`. Widzi, że zużył 80/100 paragonów (User Widget). Sprawdza, ile wydał w tym miesiącu (Stats Card).
3.  **Weryfikacja:** Widzi na liście "Ostatnie paragony", że jeden ma status "Do weryfikacji" (choć edycja jest w Telegramie, tu widzi szczegóły). Klika w wiersz tabeli.
4.  **Szczegóły:** Przechodzi na `/bills/123`. Porównuje zdjęcie paragonu z listą pozycji. Widzi, że "Mleko" zostało rozpoznane z 95% pewnością.
5.  **Eksploracja:** Klika w nazwę sklepu "Biedronka" w nagłówku paragonu.
6.  **Kontekst:** Zostaje przeniesiony do `/shops/5` (Szczegóły sklepu). Widzi, że wydał tu łącznie 1500 PLN.
7.  **Zakończenie:** Użytkownik klika w swój avatar w menu i wybiera "Wyloguj" lub po prostu zamyka kartę (sesja wygaśnie).

## 4. Układ i struktura nawigacji

### Layout Główny (Dashboard Layout)
Aplikacja wykorzystuje responsywny układ z bocznym panelem nawigacyjnym:

*   **Desktop (lg+):**
    *   Stały **Sidebar** po lewej stronie (szerokość ok. 250px).
    *   Logo aplikacji na górze sidebara.
    *   Sekcja nawigacji głównej (Dashboard, Paragony, Sklepy, Produkty, Kategorie).
    *   Sekcja użytkownika na dole (Avatar, Pasek postępu limitu Freemium, Przycisk wylogowania).
    *   Obszar roboczy (Main Content) po prawej.

*   **Mobile (<lg):**
    *   Górny pasek (**TopBar**) z Logo i przyciskiem Hamburger Menu.
    *   **Drawer (Sheet):** Wysuwany z lewej strony panel identyczny z desktopowym Sidebarem, zawierający nawigację i profil użytkownika.
    *   Obszar roboczy pod TopBarem.

### Breadcrumbs
Na górze każdego widoku szczegółowego (np. szczegóły paragonu, sklepu) znajduje się ścieżka okruszków (np. `Paragony > #12345`), ułatwiająca powrót do listy nadrzędnej.

## 5. Kluczowe komponenty

1.  **AppSidebar:** Główny komponent nawigacyjny. Obsługuje stan aktywności linków oraz wyświetlanie widgetu użycia limitu (progress bar).
2.  **StatCard:** Prosty komponent prezentacyjny wyświetlający etykietę (np. "Wydatki dzisiaj"), wartość główną (np. "124.50 PLN") i ewentualnie mały wskaźnik trendu.
3.  **AdvancedDataTable:** Reużywalny wrapper na `TanStack Table` i komponenty UI Shadcn. Zawiera:
    *   Pasek narzędzi (Search, Filter).
    *   Nagłówki z sortowaniem.
    *   Obsługę stanów: Loading (Skeletons), Empty (Brak danych), Error.
    *   Paginację na dole.
4.  **BillStatusBadge:** Komponent wizualizujący status paragonu (Processing - niebieski, Completed - zielony, Attention Needed - żółty, Error - czerwony).
5.  **UsageLimitIndicator:** Pasek postępu (Progress Bar) pokazujący stosunek zużytych paragonów do limitu (np. 45%). Zmienia kolor na czerwony, gdy limit przekracza 90%.
6.  **ThemeToggle:** Przełącznik trybu Jasny/Ciemny/Systemowy.
7.  **QueryBoundary:** Komponent HOC (Higher-Order Component) łączący `Suspense` (dla ładowania) i `ErrorBoundary` (dla błędów) dla zapytań TanStack Query, zapewniający, że błędy API nie psują całego interfejsu.