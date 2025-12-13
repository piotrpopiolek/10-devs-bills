# API Endpoint Implementation Plan: Expense Reports (Dashboard)

## 1. Przegląd punktu końcowego

Ten plan obejmuje implementację trzech endpointów REST API do generowania podsumowań wydatków dla aplikacji webowej (US-008). Endpointy umożliwiają zalogowanym użytkownikom przeglądanie podsumowań dziennych, tygodniowych i miesięcznych w formacie "read-only". Dane są agregowane z tabel `bills` i `bill_items` z filtrowaniem po `user_id` dla zapewnienia izolacji użytkowników.

**Endpointy:**

- `GET /api/v1/reports/daily` - Podsumowanie wydatków dziennych
- `GET /api/v1/reports/weekly` - Podsumowanie wydatków tygodniowych
- `GET /api/v1/reports/monthly` - Podsumowanie wydatków miesięcznych

**Funkcjonalność:**

- Agregacja wydatków z rachunków (`bills`) i pozycji rachunków (`bill_items`)
- Top 3 kategorie wydatków z kwotami i procentami
- Podział wydatków według sklepów (dla raportów dziennych i miesięcznych)
- Filtrowanie po `user_id` dla izolacji danych użytkowników
- Obsługa opcjonalnych parametrów daty/okresu (domyślnie: dzisiaj/aktualny tydzień/aktualny miesiąc)

## 2. Szczegóły żądania

### 2.1. GET /api/v1/reports/daily

**Metoda HTTP:** `GET`

**Struktura URL:** `/api/v1/reports/daily`

**Query Parameters:**

- `date` (opcjonalny, string ISO 8601, format: `YYYY-MM-DD`, domyślnie: dzisiaj) - Data raportu

**Request Body:** Brak

**Headers:**

- `Authorization: Bearer {access_token}` (wymagane)

**Przykład żądania:**

```
GET /api/v1/reports/daily?date=2024-01-15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.2. GET /api/v1/reports/weekly

**Metoda HTTP:** `GET`

**Struktura URL:** `/api/v1/reports/weekly`

**Query Parameters:**

- `week_start` (opcjonalny, string ISO 8601, format: `YYYY-MM-DD`, domyślnie: początek aktualnego tygodnia) - Data rozpoczęcia tygodnia (poniedziałek)

**Request Body:** Brak

**Headers:**

- `Authorization: Bearer {access_token}` (wymagane)

**Przykład żądania:**

```
GET /api/v1/reports/weekly?week_start=2024-01-01
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.3. GET /api/v1/reports/monthly

**Metoda HTTP:** `GET`

**Struktura URL:** `/api/v1/reports/monthly`

**Query Parameters:**

- `month` (opcjonalny, string, format: `YYYY-MM`, domyślnie: aktualny miesiąc) - Miesiąc raportu

**Request Body:** Brak

**Headers:**

- `Authorization: Bearer {access_token}` (wymagane)

**Przykład żądania:**

```
GET /api/v1/reports/monthly?month=2024-01
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. Wykorzystywane typy

### 3.1. Schematy Pydantic (Response Models)

**DailyReportResponse:**

```python
class CategorySummary(AppBaseModel):
    category: CategoryInfo  # {id: int, name: str}
    amount: Decimal
    percentage: Decimal

class ShopSummary(AppBaseModel):
    shop: ShopInfo  # {id: int, name: str}
    amount: Decimal
    bills_count: int

class DailyReportResponse(AppBaseModel):
    date: date
    total_amount: Decimal
    bills_count: int
    top_categories: List[CategorySummary]  # Top 3
    shops: List[ShopSummary]
```

**WeeklyReportResponse:**

```python
class DailyBreakdown(AppBaseModel):
    date: date
    amount: Decimal
    bills_count: int

class WeeklyReportResponse(AppBaseModel):
    week_start: date
    week_end: date
    total_amount: Decimal
    bills_count: int
    daily_breakdown: List[DailyBreakdown]  # 7 dni
    top_categories: List[CategorySummary]  # Top 3
```

**MonthlyReportResponse:**

```python
class WeeklyBreakdown(AppBaseModel):
    week_start: date
    amount: Decimal

class MonthlyReportResponse(AppBaseModel):
    month: str  # "YYYY-MM"
    total_amount: Decimal
    bills_count: int
    daily_average: Decimal
    top_categories: List[CategorySummary]  # Top 3
    top_shops: List[ShopSummary]  # Top 3
    weekly_breakdown: List[WeeklyBreakdown]
```

### 3.2. Query Parameters Schemas

**ReportsQueryParams:**

```python
class ReportsQueryParams(AppBaseModel):
    date: Optional[date] = None  # Dla daily
    week_start: Optional[date] = None  # Dla weekly
    month: Optional[str] = None  # Dla monthly, format: "YYYY-MM"
```

### 3.3. Command Models

Brak - endpointy są "read-only", nie wymagają Command Models.

## 4. Szczegóły odpowiedzi

### 4.1. GET /api/v1/reports/daily

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "date": "2024-01-15",
  "total_amount": 125.5,
  "bills_count": 3,
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 45.67,
      "percentage": 36.4
    },
    {
      "category": {
        "id": 5,
        "name": "Beverages"
      },
      "amount": 30.25,
      "percentage": 24.1
    },
    {
      "category": {
        "id": 8,
        "name": "Bakery"
      },
      "amount": 25.1,
      "percentage": 20.0
    }
  ],
  "shops": [
    {
      "shop": {
        "id": 1,
        "name": "Supermarket ABC"
      },
      "amount": 89.3,
      "bills_count": 2
    },
    {
      "shop": {
        "id": 3,
        "name": "Convenience Store XYZ"
      },
      "amount": 36.2,
      "bills_count": 1
    }
  ]
}
```

### 4.2. GET /api/v1/reports/weekly

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "week_start": "2024-01-01",
  "week_end": "2024-01-07",
  "total_amount": 850.25,
  "bills_count": 15,
  "daily_breakdown": [
    {
      "date": "2024-01-01",
      "amount": 125.5,
      "bills_count": 3
    },
    {
      "date": "2024-01-02",
      "amount": 89.3,
      "bills_count": 2
    }
    // ... pozostałe dni tygodnia
  ],
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 320.15,
      "percentage": 37.7
    }
    // ... top 3 kategorie
  ]
}
```

### 4.3. GET /api/v1/reports/monthly

**Status Code:** `200 OK`

**Response Body:**

```json
{
  "month": "2024-01",
  "total_amount": 3200.75,
  "bills_count": 45,
  "daily_average": 103.25,
  "top_categories": [
    {
      "category": {
        "id": 2,
        "name": "Dairy Products"
      },
      "amount": 1200.3,
      "percentage": 37.5
    }
    // ... top 3 kategorie
  ],
  "top_shops": [
    {
      "shop": {
        "id": 1,
        "name": "Supermarket ABC"
      },
      "amount": 1800.5,
      "bills_count": 25
    }
    // ... top 3 sklepy
  ],
  "weekly_breakdown": [
    {
      "week_start": "2024-01-01",
      "amount": 850.25
    },
    {
      "week_start": "2024-01-08",
      "amount": 920.1
    }
    // ... pozostałe tygodnie miesiąca
  ]
}
```

### 4.4. Kody błędów

- `400 Bad Request` - Nieprawidłowy format daty/miesiąca lub data poza zakresem
- `401 Unauthorized` - Brak tokena autoryzacyjnego lub nieprawidłowy token
- `500 Internal Server Error` - Błąd serwera podczas przetwarzania zapytania

## 5. Przepływ danych

### 5.1. Ogólny przepływ

1. **Autoryzacja:** Endpoint wymaga JWT access token w nagłówku `Authorization: Bearer {token}`
2. **Walidacja parametrów:** FastAPI waliduje query parameters za pomocą Pydantic schemas
3. **Pobranie użytkownika:** Dependency `CurrentUser` pobiera użytkownika z tokena JWT
4. **Obliczenie zakresu dat:** Service oblicza zakres dat na podstawie parametrów (domyślnie: dzisiaj/aktualny tydzień/aktualny miesiąc)
5. **Agregacja danych:** Service wykonuje zapytania SQL z agregacją do bazy danych:
   - Filtrowanie po `user_id` (izolacja użytkowników)
   - Filtrowanie po zakresie dat (`bill_date`)
   - Filtrowanie tylko zakończonych rachunków (`status = 'completed'`)
   - Agregacja sum wydatków z `bill_items.total_price`
   - Grupowanie po kategoriach (`bill_items.category_id`)
   - Grupowanie po sklepach (`bills.shop_id`)
6. **Obliczenie procentów:** Service oblicza procenty dla top kategorii względem `total_amount`
7. **Sortowanie i limitowanie:** Service sortuje kategorie/sklepy po kwocie i zwraca top 3
8. **Mapowanie do schematów:** Service mapuje wyniki SQL do Pydantic response schemas
9. **Zwrócenie odpowiedzi:** FastAPI serializuje response schema do JSON

### 5.2. Szczegóły zapytań SQL

**Daily Report:**

```sql
-- Agregacja wydatków dziennych
SELECT
    DATE(b.bill_date) as date,
    COALESCE(SUM(bi.total_price), 0) as total_amount,
    COUNT(DISTINCT b.id) as bills_count
FROM bills b
LEFT JOIN bill_items bi ON bi.bill_id = b.id
WHERE b.user_id = :user_id
  AND DATE(b.bill_date) = :date
  AND b.status = 'completed'
GROUP BY DATE(b.bill_date);

-- Top 3 kategorie
SELECT
    c.id,
    c.name,
    SUM(bi.total_price) as amount
FROM bill_items bi
JOIN bills b ON b.id = bi.bill_id
LEFT JOIN categories c ON c.id = bi.category_id
WHERE b.user_id = :user_id
  AND DATE(b.bill_date) = :date
  AND b.status = 'completed'
  AND bi.category_id IS NOT NULL
GROUP BY c.id, c.name
ORDER BY amount DESC
LIMIT 3;

-- Wydatki według sklepów
SELECT
    s.id,
    s.name,
    SUM(bi.total_price) as amount,
    COUNT(DISTINCT b.id) as bills_count
FROM bills b
JOIN bill_items bi ON bi.bill_id = b.id
LEFT JOIN shops s ON s.id = b.shop_id
WHERE b.user_id = :user_id
  AND DATE(b.bill_date) = :date
  AND b.status = 'completed'
  AND b.shop_id IS NOT NULL
GROUP BY s.id, s.name
ORDER BY amount DESC;
```

**Weekly Report:**

```sql
-- Agregacja wydatków tygodniowych z podziałem dziennym
SELECT
    DATE(b.bill_date) as date,
    COALESCE(SUM(bi.total_price), 0) as amount,
    COUNT(DISTINCT b.id) as bills_count
FROM bills b
LEFT JOIN bill_items bi ON bi.bill_id = b.id
WHERE b.user_id = :user_id
  AND DATE(b.bill_date) >= :week_start
  AND DATE(b.bill_date) < :week_end
  AND b.status = 'completed'
GROUP BY DATE(b.bill_date)
ORDER BY date;
```

**Monthly Report:**

```sql
-- Agregacja wydatków miesięcznych
SELECT
    COALESCE(SUM(bi.total_price), 0) as total_amount,
    COUNT(DISTINCT b.id) as bills_count
FROM bills b
LEFT JOIN bill_items bi ON bi.bill_id = b.id
WHERE b.user_id = :user_id
  AND DATE_TRUNC('month', b.bill_date) = DATE_TRUNC('month', :month_date::date)
  AND b.status = 'completed';
```

### 5.3. Interakcje z zewnętrznymi usługami

Brak - endpointy są "read-only" i nie wymagają interakcji z zewnętrznymi usługami (OCR, AI, Storage).

## 6. Względy bezpieczeństwa

### 6.1. Autoryzacja

- **Wymagany JWT access token:** Wszystkie endpointy wymagają autoryzacji przez dependency `CurrentUser`
- **Weryfikacja tokena:** Token jest weryfikowany przez `get_current_user()` dependency, które:
  - Dekoduje token JWT i wyodrębnia `user_id`
  - Sprawdza, czy użytkownik istnieje w bazie danych
  - Weryfikuje, czy konto użytkownika jest aktywne (`is_active = true`)
- **Izolacja danych:** Wszystkie zapytania SQL filtrują po `user_id` z tokena JWT, zapewniając, że użytkownik widzi tylko swoje dane

### 6.2. Walidacja danych wejściowych

- **Format daty:** Query parameters `date` i `week_start` są walidowane przez Pydantic jako `date` (ISO 8601, format: `YYYY-MM-DD`)
- **Format miesiąca:** Query parameter `month` jest walidowany jako string w formacie `YYYY-MM` (regex: `^\d{4}-\d{2}$`)
- **Zakres dat:** Service sprawdza, czy data nie jest w przyszłości (dla `date` i `week_start`)
- **Strict mode:** Wszystkie Pydantic schemas używają `strict=True` dla zapobieżenia niejawnej koercji typów

### 6.3. Ochrona przed atakami

- **SQL Injection:** Wszystkie zapytania SQL używają parametrów nazwanych (`:user_id`, `:date`) zamiast string concatenation
- **Rate Limiting:** Endpointy mogą być objęte rate limitingiem na poziomie aplikacji (opcjonalnie)
- **CORS:** CORS jest konfigurowany na poziomie aplikacji FastAPI dla kontroli dostępu z frontendu

### 6.4. Logowanie i audyt

- **Logowanie błędów:** Wszystkie błędy są logowane z kontekstem (user_id, endpoint, parametry)
- **Audyt dostępu:** Dostęp do endpointów może być logowany dla celów audytu (opcjonalnie)

## 7. Obsługa błędów

### 7.1. Błędy walidacji (400 Bad Request)

**Nieprawidłowy format daty:**

```json
{
  "detail": "Nieprawidłowy format daty. Oczekiwany format: YYYY-MM-DD"
}
```

**Nieprawidłowy format miesiąca:**

```json
{
  "detail": "Nieprawidłowy format miesiąca. Oczekiwany format: YYYY-MM"
}
```

**Data w przyszłości:**

```json
{
  "detail": "Data nie może być w przyszłości"
}
```

**Implementacja:** Błędy walidacji są obsługiwane przez Pydantic validators w schemas lub przez custom validators w service layer.

### 7.2. Błędy autoryzacji (401 Unauthorized)

**Brak tokena:**

```json
{
  "detail": "Nie podano tokena autoryzacyjnego"
}
```

**Nieprawidłowy token:**

```json
{
  "detail": "Nieprawidłowy token"
}
```

**Nieaktywne konto:**

```json
{
  "detail": "Konto użytkownika jest nieaktywne"
}
```

**Implementacja:** Błędy autoryzacji są obsługiwane przez dependency `get_current_user()` w `src/deps.py`.

### 7.3. Błędy serwera (500 Internal Server Error)

**Błąd bazy danych:**

```json
{
  "detail": "Wystąpił błąd podczas przetwarzania żądania"
}
```

**Implementacja:** Błędy serwera są obsługiwane przez globalny exception handler w `src/error_handler.py`. Wszystkie nieobsłużone wyjątki są logowane i zwracane jako 500 z ogólnym komunikatem (bez ujawniania szczegółów implementacji).

### 7.4. Strategia obsługi błędów

**Warstwa Prezentacji (routes.py):**

- Może zgłaszać tylko `HTTPException` z odpowiednimi kodami statusu
- Nie loguje błędów (logowanie w service layer)

**Warstwa Domeny/Serwisu (services.py):**

- Zgłasza niestandardowe błędy domenowe (np. `InvalidDateRangeError`)
- Loguje błędy z kontekstem (user_id, endpoint, parametry)
- Tłumaczy błędy domenowe na `HTTPException` w routes lub globalnym handlerze

**Poziom Globalny (error_handler.py):**

- Przechwytuje wszystkie nieobsłużone wyjątki
- Tłumaczy błędy domenowe na odpowiednie odpowiedzi HTTP
- Loguje wszystkie błędy dla celów debugowania

## 8. Rozważania dotyczące wydajności

### 8.1. Potencjalne wąskie gardła

**Agregacja danych:**

- Zapytania SQL z agregacją (`SUM`, `COUNT`, `GROUP BY`) mogą być wolne przy dużej liczbie rachunków
- Brak indeksów na `bill_date` i `user_id` może spowolnić zapytania

**N+1 queries:**

- Jeśli service pobiera kategorie/sklepy osobno dla każdego wyniku agregacji, może wystąpić problem N+1 queries

**Duże zakresy dat:**

- Raporty miesięczne mogą agregować duże ilości danych (setki rachunków i tysięcy pozycji)

### 8.2. Strategie optymalizacji

**Indeksy bazy danych:**

- Istniejący indeks `idx_bills_user_id_bill_date` na `(user_id, bill_date)` jest optymalny dla zapytań raportowych
- Indeks `idx_bill_items_bill_id` na `bill_items.bill_id` wspiera JOIN z `bills`
- Indeks `idx_bill_items_index_id` na `bill_items.index_id` wspiera grupowanie po kategoriach (jeśli `category_id` jest w `product_indexes`)

**Optymalizacja zapytań SQL:**

- Użycie `LEFT JOIN` zamiast wielu zapytań dla agregacji
- Użycie `COALESCE` dla obsługi NULL values w agregacji
- Użycie `DATE_TRUNC` dla efektywnego filtrowania po miesiącach
- Użycie `LIMIT` dla top kategorii/sklepów bez pobierania wszystkich wyników

**Caching (opcjonalnie, post-MVP):**

- Cache raportów dziennych/tygodniowych/miesięcznych w Redis z TTL 1 godzina
- Cache key: `report:{user_id}:{type}:{date}` (np. `report:123:daily:2024-01-15`)
- Inwalidacja cache przy dodaniu/aktualizacji rachunku użytkownika

**Paginacja (nie dotyczy):**

- Raporty nie wymagają paginacji, ponieważ zwracają tylko agregowane podsumowania (top 3 kategorie, top 3 sklepy)

### 8.3. Monitoring wydajności

- **Metryki:** Monitorowanie czasu odpowiedzi endpointów (p50, p95, p99) za pomocą OpenTelemetry
- **Logi:** Logowanie wolnych zapytań SQL (> 1 sekunda) dla identyfikacji problemów wydajnościowych
- **Alerty:** Alerty przy czasie odpowiedzi > 2 sekundy (p95)

## 9. Etapy wdrożenia

### Krok 1: Utworzenie struktury modułu reports

**Pliki do utworzenia:**

- `backend/src/reports/__init__.py`
- `backend/src/reports/models.py` (jeśli potrzebne modele pomocnicze)
- `backend/src/reports/schemas.py` (response schemas)
- `backend/src/reports/services.py` (logika biznesowa)
- `backend/src/reports/routes.py` (endpointy HTTP)
- `backend/src/reports/exceptions.py` (błędy domenowe, jeśli potrzebne)

**Akcje:**

1. Utworzyć katalog `backend/src/reports/`
2. Utworzyć plik `__init__.py` z eksportem routera
3. Utworzyć podstawową strukturę plików zgodnie z architekturą warstwową

### Krok 2: Definicja schematów Pydantic (schemas.py)

**Akcje:**

1. Zdefiniować `CategorySummary` schema z `category: CategoryInfo`, `amount: Decimal`, `percentage: Decimal`
2. Zdefiniować `ShopSummary` schema z `shop: ShopInfo`, `amount: Decimal`, `bills_count: int`
3. Zdefiniować `DailyBreakdown` schema z `date: date`, `amount: Decimal`, `bills_count: int`
4. Zdefiniować `WeeklyBreakdown` schema z `week_start: date`, `amount: Decimal`
5. Zdefiniować `DailyReportResponse` schema z wszystkimi wymaganymi polami
6. Zdefiniować `WeeklyReportResponse` schema z wszystkimi wymaganymi polami
7. Zdefiniować `MonthlyReportResponse` schema z wszystkimi wymaganymi polami
8. Zdefiniować `ReportsQueryParams` schema dla query parameters z walidatorami
9. Użyć `strict=True` dla wszystkich schemas zgodnie z regułami implementacji
10. Dodać field validators dla formatów daty i miesiąca

**Walidatory:**

- `date`: Format ISO 8601 (`YYYY-MM-DD`), nie może być w przyszłości
- `week_start`: Format ISO 8601 (`YYYY-MM-DD`), musi być poniedziałkiem (opcjonalnie)
- `month`: Format `YYYY-MM`, regex validation

### Krok 3: Implementacja logiki biznesowej (services.py)

**Akcje:**

1. Utworzyć klasę `ReportService` (nie dziedziczy z `AppService`, ponieważ nie zarządza pojedynczymi encjami)
2. Zaimplementować metodę `get_daily_report(user_id: int, date: date) -> DailyReportResponse`:
   - Obliczyć zakres dat (cały dzień)
   - Wykonać zapytanie SQL dla agregacji wydatków dziennych
   - Wykonać zapytanie SQL dla top 3 kategorii
   - Wykonać zapytanie SQL dla wydatków według sklepów
   - Obliczyć procenty dla kategorii
   - Zmapować wyniki do `DailyReportResponse`
3. Zaimplementować metodę `get_weekly_report(user_id: int, week_start: date) -> WeeklyReportResponse`:
   - Obliczyć zakres dat tygodnia (poniedziałek-niedziela)
   - Wykonać zapytanie SQL dla agregacji wydatków tygodniowych z podziałem dziennym
   - Wykonać zapytanie SQL dla top 3 kategorii w całym tygodniu
   - Zmapować wyniki do `WeeklyReportResponse`
4. Zaimplementować metodę `get_monthly_report(user_id: int, month: str) -> MonthlyReportResponse`:
   - Parsować `month` string do `date` (pierwszy dzień miesiąca)
   - Obliczyć zakres dat miesiąca
   - Wykonać zapytanie SQL dla agregacji wydatków miesięcznych
   - Obliczyć średnią dzienną (`total_amount / liczba_dni_w_miesiącu`)
   - Wykonać zapytanie SQL dla top 3 kategorii
   - Wykonać zapytanie SQL dla top 3 sklepów
   - Wykonać zapytanie SQL dla podziału tygodniowego
   - Zmapować wyniki do `MonthlyReportResponse`
5. Użyć async SQLAlchemy (`await session.execute()`) dla wszystkich zapytań
6. Użyć `joinedload` lub `selectinload` dla eager loading relacji (kategorie, sklepy) jeśli potrzebne
7. Dodać logowanie błędów z kontekstem (user_id, endpoint, parametry)

**Helper metody:**

- `_calculate_week_range(week_start: date) -> tuple[date, date]` - oblicza zakres tygodnia
- `_calculate_month_range(month: str) -> tuple[date, date]` - oblicza zakres miesiąca
- `_calculate_percentage(amount: Decimal, total: Decimal) -> Decimal` - oblicza procent

### Krok 4: Implementacja endpointów HTTP (routes.py)

**Akcje:**

1. Utworzyć `APIRouter` dla endpointów reports
2. Zaimplementować endpoint `GET /daily`:
   - Dependency: `CurrentUser` dla autoryzacji
   - Dependency: `get_session` dla sesji bazy danych
   - Query parameter: `date: Optional[date] = None` (domyślnie: dzisiaj)
   - Wywołanie: `service.get_daily_report(user.id, date or date.today())`
   - Response: `DailyReportResponse`, status code: `200 OK`
3. Zaimplementować endpoint `GET /weekly`:
   - Dependency: `CurrentUser` dla autoryzacji
   - Dependency: `get_session` dla sesji bazy danych
   - Query parameter: `week_start: Optional[date] = None` (domyślnie: początek aktualnego tygodnia)
   - Wywołanie: `service.get_weekly_report(user.id, week_start or _get_current_week_start())`
   - Response: `WeeklyReportResponse`, status code: `200 OK`
4. Zaimplementować endpoint `GET /monthly`:
   - Dependency: `CurrentUser` dla autoryzacji
   - Dependency: `get_session` dla sesji bazy danych
   - Query parameter: `month: Optional[str] = None` (domyślnie: aktualny miesiąc)
   - Wywołanie: `service.get_monthly_report(user.id, month or _get_current_month())`
   - Response: `MonthlyReportResponse`, status code: `200 OK`
5. Dodać dependency injection dla `ReportService`:
   - Funkcja `get_report_service(session: AsyncSession) -> ReportService`
   - Type alias: `ServiceDependency = Annotated[ReportService, Depends(get_report_service)]`
6. Dodać docstrings dla wszystkich endpointów zgodnie z konwencją projektu
7. Dodać `summary` i `description` do dekoratorów `@router.get()`

**Helper funkcje:**

- `_get_current_week_start() -> date` - zwraca datę początku aktualnego tygodnia (poniedziałek)
- `_get_current_month() -> str` - zwraca aktualny miesiąc w formacie "YYYY-MM"

### Krok 5: Rejestracja routera w aplikacji głównej

**Akcje:**

1. Znaleźć plik główny aplikacji FastAPI (prawdopodobnie `backend/src/main.py` lub podobny)
2. Zaimportować router z `src.reports.routes`
3. Zarejestrować router za pomocą `app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])`
4. Sprawdzić, czy prefix jest zgodny z konwencją projektu (`/api/v1/reports`)

### Krok 6: Implementacja obsługi błędów (exceptions.py, jeśli potrzebne)

**Akcje:**

1. Utworzyć niestandardowe błędy domenowe (jeśli potrzebne):
   - `InvalidDateRangeError` - dla dat w przyszłości lub poza zakresem
   - `InvalidMonthFormatError` - dla nieprawidłowego formatu miesiąca
2. Zarejestrować błędy w globalnym exception handlerze (`src/error_handler.py`):
   - Mapować `InvalidDateRangeError` na `HTTPException(status_code=400)`
   - Mapować `InvalidMonthFormatError` na `HTTPException(status_code=400)`

### Krok 7: Testy (opcjonalnie, post-MVP)

**Akcje:**

1. Utworzyć plik `backend/tests/reports/test_services.py` dla testów jednostkowych serwisu
2. Utworzyć plik `backend/tests/reports/test_routes.py` dla testów integracyjnych endpointów
3. Zaimplementować testy dla:
   - Agregacji wydatków dziennych/tygodniowych/miesięcznych
   - Top 3 kategorii (sortowanie, limitowanie)
   - Obliczania procentów
   - Walidacji parametrów daty/miesiąca
   - Izolacji użytkowników (użytkownik widzi tylko swoje dane)
   - Obsługi pustych wyników (brak rachunków w danym okresie)

### Krok 8: Dokumentacja i code review

**Akcje:**

1. Sprawdzić, czy wszystkie docstrings są kompletne
2. Sprawdzić, czy kod jest zgodny z zasadami DRY (brak duplikacji)
3. Sprawdzić, czy kod jest zgodny z architekturą warstwową (Service Layer)
4. Sprawdzić, czy kod jest zgodny z zasadami SOLID
5. Sprawdzić, czy wszystkie zapytania SQL używają parametrów nazwanych (ochrona przed SQL injection)
6. Sprawdzić, czy wszystkie schemas używają `strict=True`
7. Sprawdzić, czy wszystkie endpointy są async (`async def`)
8. Sprawdzić, czy wszystkie błędy są właściwie logowane

### Krok 9: Integracja z frontendem (opcjonalnie, poza zakresem tego planu)

**Akcje:**

1. Utworzyć serwis `astro/src/lib/services/reports.ts` dla wywołań API
2. Zaimplementować funkcje `getDailyReport()`, `getWeeklyReport()`, `getMonthlyReport()`
3. Zintegrować z komponentami React w aplikacji webowej

## 10. Uwagi dodatkowe

### 10.1. Zgodność z architekturą

- **Warstwa Prezentacji (routes.py):** Tylko HTTP handling, dependency injection, walidacja query parameters
- **Warstwa Domeny/Serwisu (services.py):** Wszystka logika biznesowa, zapytania SQL, agregacja danych
- **Warstwa Infrastruktury (models.py):** Modele SQLAlchemy (używamy istniejących: `Bill`, `BillItem`, `Category`, `Shop`)
- **Warstwa Prezentacji (schemas.py):** Pydantic schemas dla walidacji i serializacji

### 10.2. Zgodność z regułami implementacji

- ✅ Użycie Pydantic z `strict=True` dla wszystkich schemas
- ✅ Użycie async SQLAlchemy dla wszystkich zapytań
- ✅ Użycie dependency injection (FastAPI `Depends`) dla serwisów i sesji
- ✅ Wszystkie endpointy są async (`async def`)
- ✅ Architektura warstwowa (Service Layer)
- ✅ Zasady SOLID (SRP: każda metoda ma jedną odpowiedzialność)
- ✅ Obsługa błędów z separacją odpowiedzialności (routes → HTTPException, services → domain errors)
- ✅ Izolacja użytkowników (filtrowanie po `user_id` w każdym zapytaniu)

### 10.3. Zgodność z PRD

- ✅ US-008: Przeglądanie podsumowań w aplikacji webowej
- ✅ Wyświetlanie podsumowań dziennych, tygodniowych i miesięcznych
- ✅ Dane prezentowane w czytelnej formie (JSON z agregacją)
- ✅ Aplikacja "read-only" (tylko GET endpoints, brak mutacji)

### 10.4. Zgodność z typami TypeScript

- ✅ Response schemas są zgodne z typami zdefiniowanymi w `astro/src/types.ts`:
  - `DailyReportResponse`
  - `WeeklyReportResponse`
  - `MonthlyReportResponse`
  - `CategorySummary`
  - `ShopSummary`
  - `DailyBreakdown`
  - `WeeklyBreakdown`

### 10.5. Potencjalne rozszerzenia (post-MVP)

- **Caching:** Implementacja cache w Redis dla raportów (TTL: 1 godzina)
- **Export:** Endpoint do eksportu raportów do CSV/PDF
- **Filtrowanie:** Dodatkowe filtry (np. kategoria, sklep) w query parameters
- **Porównania:** Porównanie z poprzednim okresem (np. miesiąc vs poprzedni miesiąc)
- **Wykresy:** Endpoint zwracający dane w formacie gotowym do wykresów (Chart.js, D3.js)
