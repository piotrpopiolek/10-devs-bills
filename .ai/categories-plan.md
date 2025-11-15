# API Endpoint Implementation Plan: GET /categories

## 1. Przegląd punktu końcowego

Endpoint `GET /categories` służy do pobierania hierarchicznej listy wszystkich kategorii produktów w systemie. Umożliwia filtrowanie kategorii według kategorii nadrzędnej oraz opcjonalne włączenie podkategorii w odpowiedzi. Jest to endpoint tylko do odczytu, który zwraca strukturę drzewiastą kategorii wraz z liczbą przypisanych produktów dla każdej kategorii.

**Główne funkcjonalności:**

- Pobieranie wszystkich kategorii z hierarchią rodzic-dziecko
- Filtrowanie kategorii według kategorii nadrzędnej (`parent_id`)
- Opcjonalne włączenie podkategorii w odpowiedzi (`include_children`)
- Liczenie produktów przypisanych do każdej kategorii
- Obsługa pustych wyników (pusta lista kategorii)

**Kontekst biznesowy:**
Kategorie są używane do organizacji produktów w słowniku (`indexes` table). Hierarchiczna struktura umożliwia tworzenie głównych kategorii (np. "Food & Beverages") z podkategoriami (np. "Dairy Products"). Endpoint jest używany przez aplikację webową do wyświetlania i filtrowania produktów oraz przez system AI do kategoryzacji produktów z paragonów.

## 2. Szczegóły żądania

### Metoda HTTP

`GET`

### Struktura URL

```
/api/v1/categories
```

### Parametry zapytania

#### Wymagane

Brak

#### Opcjonalne

1. **`parent_id`** (integer, optional)

   - **Typ:** `integer`
   - **Opis:** ID kategorii nadrzędnej do filtrowania. Zwraca tylko kategorie, które są bezpośrednimi dziećmi kategorii o podanym ID.
   - **Przykład:** `?parent_id=1`
   - **Walidacja:**
     - Musi być dodatnią liczbą całkowitą
     - Jeśli podane, kategoria o tym ID musi istnieć w bazie danych
     - W przeciwnym razie zwracany jest błąd 400 Bad Request

2. **`include_children`** (boolean, optional)
   - **Typ:** `boolean`
   - **Opis:** Określa, czy w odpowiedzi mają być uwzględnione podkategorie (dzieci) każdej kategorii. Domyślnie `false`.
   - **Przykład:** `?include_children=true`
   - **Walidacja:**
     - Akceptowane wartości: `true`, `false`, `1`, `0`, `yes`, `no`
     - Domyślna wartość: `false`
     - Jeśli `true`, odpowiedź zawiera rekurencyjną strukturę z wszystkimi podkategoriami

### Request Body

Brak

### Headers

#### Wymagane

- **`Authorization`**: `Bearer <jwt_token>`
  - **Opis:** JWT token autoryzacyjny uzyskany z endpointu `/auth/verify`
  - **Format:** `Bearer <token>`
  - **Walidacja:** Token musi być ważny i nie wygasły

#### Opcjonalne

- **`Accept`**: `application/json` (domyślne)
- **`Content-Type`**: Nie dotyczy (GET request)

### Przykłady żądań

```http
GET /api/v1/categories HTTP/1.1
Host: api.bills.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```http
GET /api/v1/categories?parent_id=1&include_children=true HTTP/1.1
Host: api.bills.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 3. Wykorzystywane typy

### DTOs (Data Transfer Objects)

#### `CategoryResponse`

```typescript
interface CategoryResponse {
  id: number;
  name: string;
  parent_id: number | null;
  children: CategoryResponse[];
  products_count: number;
  created_at: string;
}
```

**Użycie:** Główna struktura odpowiedzi dla pojedynczej kategorii. Zawiera wszystkie wymagane pola z hierarchią dzieci.

#### `CategoryListResponse`

```typescript
interface CategoryListResponse {
  categories: CategoryResponse[];
}
```

**Użycie:** Wrapper dla listy kategorii. Zawiera tablicę kategorii bez paginacji (kategorie są zwykle nieliczne).

#### `CategoriesQueryParams`

```typescript
interface CategoriesQueryParams {
  parent_id?: number;
  include_children?: boolean;
}
```

**Użycie:** Pydantic model do walidacji parametrów zapytania w FastAPI.

### Command Modele

Brak - endpoint tylko do odczytu.

### Typy bazy danych

#### `Category` (SQLAlchemy Model)

- **Tabela:** `categories`
- **Kolumny:**
  - `id`: `SERIAL PRIMARY KEY`
  - `name`: `VARCHAR(255) NOT NULL UNIQUE`
  - `parent_id`: `INTEGER REFERENCES categories(id) ON DELETE RESTRICT`
  - `created_at`: `TIMESTAMPTZ NOT NULL DEFAULT NOW()`
  - `updated_at`: `TIMESTAMPTZ NOT NULL DEFAULT NOW()`
- **Relacje:**
  - `parent`: `Optional[Category]` - kategoria nadrzędna
  - `children`: `List[Category]` - lista podkategorii
  - `indexes`: `List[Index]` - lista produktów w kategorii

#### `Index` (SQLAlchemy Model)

- **Tabela:** `indexes`
- **Kolumny:**
  - `id`: `SERIAL PRIMARY KEY`
  - `name`: `VARCHAR(255) NOT NULL UNIQUE`
  - `category_id`: `INTEGER REFERENCES categories(id) ON DELETE RESTRICT`
- **Użycie:** Do liczenia produktów w kategorii (`products_count`)

### Pydantic Modele (Request/Response)

#### `CategoriesQueryParams` (Request)

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CategoriesQueryParams(BaseModel):
    parent_id: Optional[int] = Field(None, gt=0, description="Filter by parent category ID")
    include_children: Optional[bool] = Field(False, description="Include subcategories in response")

    @field_validator('parent_id')
    @classmethod
    def validate_parent_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('parent_id must be a positive integer')
        return v
```

#### `CategoryResponse` (Response)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CategoryResponse(BaseModel):
    id: int
    name: str
    parent_id: Optional[int]
    children: List['CategoryResponse'] = Field(default_factory=list)
    products_count: int = Field(ge=0, description="Number of products in this category")
    created_at: datetime

    class Config:
        from_attributes = True
```

#### `CategoryListResponse` (Response)

```python
class CategoryListResponse(BaseModel):
    categories: List[CategoryResponse]
```

## 4. Szczegóły odpowiedzi

### Sukces (200 OK)

#### Struktura odpowiedzi

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Beverages",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Dairy Products",
          "parent_id": 1,
          "children": [],
          "products_count": 150,
          "created_at": "2024-01-01T00:00:00Z"
        }
      ],
      "products_count": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### Opis pól

- **`categories`** (array, required): Lista kategorii. Jeśli `include_children=false`, zawiera tylko kategorie główne (bez podkategorii w polu `children`).
- **`id`** (integer, required): Unikalny identyfikator kategorii.
- **`name`** (string, required): Nazwa kategorii.
- **`parent_id`** (integer | null, required): ID kategorii nadrzędnej. `null` dla kategorii głównych.
- **`children`** (array, required): Lista podkategorii. Pusta tablica, jeśli kategoria nie ma dzieci lub `include_children=false`.
- **`products_count`** (integer, required): Liczba produktów przypisanych do kategorii (łącznie z produktami w podkategoriach, jeśli `include_children=true`).
- **`created_at`** (string, required): Data utworzenia kategorii w formacie ISO 8601.

#### Przykłady odpowiedzi

**Bez parametrów (tylko kategorie główne):**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Beverages",
      "parent_id": null,
      "children": [],
      "products_count": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Z `include_children=true`:**

```json
{
  "categories": [
    {
      "id": 1,
      "name": "Food & Beverages",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Dairy Products",
          "parent_id": 1,
          "children": [],
          "products_count": 150,
          "created_at": "2024-01-01T00:00:00Z"
        }
      ],
      "products_count": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Z `parent_id=1`:**

```json
{
  "categories": [
    {
      "id": 2,
      "name": "Dairy Products",
      "parent_id": 1,
      "children": [],
      "products_count": 150,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Pusta lista (brak kategorii):**

```json
{
  "categories": []
}
```

### Błędy

#### 401 Unauthorized

**Przyczyna:** Brak lub nieprawidłowy token autoryzacji.

**Struktura odpowiedzi:**

```json
{
  "detail": "Not authenticated"
}
```

**Scenariusze:**

- Brak nagłówka `Authorization`
- Nieprawidłowy format tokenu (nie zaczyna się od "Bearer ")
- Wygasły token JWT
- Nieprawidłowy podpis tokenu
- Token nie powiązany z aktywnym użytkownikiem

#### 400 Bad Request

**Przyczyna:** Nieprawidłowe parametry zapytania.

**Struktura odpowiedzi:**

```json
{
  "detail": [
    {
      "loc": ["query", "parent_id"],
      "msg": "parent_id must be a positive integer",
      "type": "value_error"
    }
  ]
}
```

**Scenariusze:**

- `parent_id` nie jest liczbą całkowitą
- `parent_id` jest ujemne lub zero
- `parent_id` wskazuje na nieistniejącą kategorię
- `include_children` nie jest wartością boolean

**Przykład błędu dla nieistniejącego `parent_id`:**

```json
{
  "detail": "Parent category with ID 999 does not exist"
}
```

#### 500 Internal Server Error

**Przyczyna:** Błąd po stronie serwera.

**Struktura odpowiedzi:**

```json
{
  "detail": "Internal server error"
}
```

**Scenariusze:**

- Błąd połączenia z bazą danych
- Błąd wykonania zapytania SQL
- Błąd serializacji odpowiedzi
- Nieoczekiwany wyjątek w kodzie

**Uwaga:** Szczegóły błędu nie powinny być ujawniane użytkownikowi w środowisku produkcyjnym.

## 5. Przepływ danych

### Krok 1: Walidacja autoryzacji

1. **Middleware autoryzacji** przechwytuje żądanie
2. **Ekstrakcja tokenu** z nagłówka `Authorization: Bearer <token>`
3. **Weryfikacja tokenu JWT:**
   - Sprawdzenie podpisu
   - Sprawdzenie ważności (expiration)
   - Pobranie `user_id` z payload tokenu
4. **Sprawdzenie użytkownika w bazie:**
   - Weryfikacja, że użytkownik istnieje
   - Weryfikacja, że użytkownik jest aktywny (`is_active = true`)
5. **Przekazanie `user_id`** do endpointu jako dependency

**Błędy:**

- 401 Unauthorized - jeśli token nieprawidłowy lub użytkownik nieaktywny

### Krok 2: Walidacja parametrów zapytania

1. **Parsowanie parametrów** z query string
2. **Walidacja przez Pydantic:**
   - `parent_id`: sprawdzenie typu i zakresu (jeśli podane)
   - `include_children`: konwersja do boolean (jeśli podane)
3. **Weryfikacja `parent_id` w bazie** (jeśli podane):
   - Zapytanie do tabeli `categories` z warunkiem `id = parent_id`
   - Jeśli kategoria nie istnieje, zwróć 400 Bad Request

**Błędy:**

- 400 Bad Request - jeśli parametry nieprawidłowe

### Krok 3: Pobranie kategorii z bazy danych

1. **Budowanie zapytania SQLAlchemy:**

   ```python
   query = select(Category)

   # Filtrowanie po parent_id
   if parent_id:
       query = query.where(Category.parent_id == parent_id)
   else:
       query = query.where(Category.parent_id.is_(None))
   ```

2. **Wykonanie zapytania:**
   - Użycie async session z dependency injection
   - Pobranie wszystkich pasujących kategorii
3. **Pobranie relacji:**
   - Jeśli `include_children=True`, załadowanie relacji `children` (eager loading)
   - Użycie `joinedload` lub `selectinload` dla optymalizacji

**Błędy:**

- 500 Internal Server Error - jeśli błąd bazy danych

### Krok 4: Liczenie produktów

1. **Dla każdej kategorii:**
   - Zapytanie COUNT do tabeli `indexes` z warunkiem `category_id = category.id`
   - Jeśli `include_children=True`, rekurencyjne zliczanie produktów w podkategoriach
2. **Optymalizacja:**
   - Użycie subquery lub JOIN z GROUP BY dla wszystkich kategorii jednocześnie
   - Unikanie N+1 queries przez agregację w jednym zapytaniu

**Przykład zapytania SQL:**

```sql
SELECT
    c.id,
    c.name,
    c.parent_id,
    COUNT(i.id) as products_count
FROM categories c
LEFT JOIN indexes i ON i.category_id = c.id
WHERE c.parent_id IS NULL  -- lub = :parent_id
GROUP BY c.id, c.name, c.parent_id
```

### Krok 5: Budowanie hierarchii (jeśli `include_children=True`)

1. **Rekurencyjne budowanie struktury:**
   - Dla każdej kategorii głównej, znajdź wszystkie dzieci
   - Dla każdego dziecka, znajdź jego dzieci (rekurencyjnie)
   - Maksymalna głębokość: zapobieganie nieskończonym pętlom (cykle w hierarchii)
2. **Algorytm:**
   - Mapowanie kategorii po ID dla szybkiego dostępu
   - Budowanie drzewa od korzenia do liści
   - Rekurencyjne zliczanie produktów w podkategoriach

**Ochrona przed cyklami:**

- Sprawdzenie maksymalnej głębokości (np. 10 poziomów)
- Wykrywanie cykli w relacji parent-child

### Krok 6: Serializacja odpowiedzi

1. **Konwersja modeli SQLAlchemy do Pydantic:**
   - Użycie `from_attributes=True` w Pydantic model
   - Konwersja dat do ISO 8601 format
2. **Budowanie `CategoryListResponse`:**
   - Opakowanie listy kategorii w odpowiedź
3. **Zwrócenie odpowiedzi:**
   - Status code: 200 OK
   - Content-Type: application/json
   - Body: JSON z listą kategorii

### Diagram przepływu

```
[Client Request]
    ↓
[Auth Middleware] → [401] Invalid token
    ↓
[Validate Query Params] → [400] Invalid params
    ↓
[Database Query] → [500] DB error
    ↓
[Count Products]
    ↓
[Build Hierarchy] (if include_children=true)
    ↓
[Serialize Response]
    ↓
[200 OK Response]
```

## 6. Względy bezpieczeństwa

### Uwierzytelnianie i autoryzacja

#### Wymagania autoryzacji

- **JWT Token:** Wszystkie żądania wymagają ważnego tokenu JWT w nagłówku `Authorization`
- **Weryfikacja tokenu:**
  - Sprawdzenie podpisu tokenu (secret key)
  - Sprawdzenie ważności (expiration time)
  - Sprawdzenie, że użytkownik istnieje i jest aktywny
- **Dependency Injection:** Użycie FastAPI dependency dla `get_current_user`:

  ```python
  from fastapi import Depends, HTTPException, status
  from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

  security = HTTPBearer()

  async def get_current_user(
      credentials: HTTPAuthorizationCredentials = Depends(security)
  ) -> User:
      token = credentials.credentials
      # Weryfikacja tokenu i zwrócenie użytkownika
      ...
  ```

#### Izolacja danych

- **Uwaga:** Endpoint `/categories` zwraca **wszystkie** kategorie w systemie (nie filtrowane po `user_id`)
- **Uzasadnienie:** Kategorie są globalne i współdzielone przez wszystkich użytkowników
- **Bezpieczeństwo:** Kategorie są tylko do odczytu i nie zawierają danych osobowych
- **Produkty:** Produkty (`indexes`) są również globalne, ale filtrowane po `user_id` w innych endpointach

### Walidacja danych wejściowych

#### Walidacja parametrów zapytania

1. **`parent_id`:**

   - Typ: integer
   - Zakres: > 0
   - Istnienie: kategoria o podanym ID musi istnieć w bazie
   - Sanityzacja: konwersja z string do integer

2. **`include_children`:**
   - Typ: boolean
   - Akceptowane wartości: `true`, `false`, `1`, `0`, `yes`, `no`
   - Domyślna wartość: `false`
   - Sanityzacja: konwersja do boolean

#### Ochrona przed atakami

1. **SQL Injection:**

   - **Ochrona:** Użycie ORM SQLAlchemy z parametrami
   - **Przykład:** `query.where(Category.parent_id == parent_id)` zamiast string concatenation
   - **Weryfikacja:** Wszystkie zapytania używają prepared statements

2. **Rate Limiting:**

   - **Implementacja:** Middleware rate limiting na poziomie FastAPI
   - **Limit:** Standardowe limity dla endpointów autoryzowanych (np. 100 requests/minute per user)
   - **Odpowiedź:** 429 Too Many Requests z nagłówkiem `Retry-After`

3. **CORS (Cross-Origin Resource Sharing):**

   - **Konfiguracja:** CORS middleware w FastAPI
   - **Dozwolone origins:** Tylko domena aplikacji webowej
   - **Nagłówki:** `Access-Control-Allow-Origin`, `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`

4. **Input Sanitization:**
   - **Parametry zapytania:** Walidacja i sanityzacja przez Pydantic
   - **Typy danych:** Automatyczna konwersja i walidacja typów
   - **Zakresy wartości:** Sprawdzenie zakresów (np. `parent_id > 0`)

### Logowanie i monitoring

#### Logowanie zdarzeń bezpieczeństwa

- **Nieudane próby autoryzacji:** Logowanie z IP, user_id (jeśli dostępne), timestamp
- **Nieprawidłowe parametry:** Logowanie z parametrami i user_id
- **Błędy bazy danych:** Logowanie z kontekstem (query, params) bez ujawniania szczegółów

#### Monitoring

- **Metryki:** Liczba żądań, czas odpowiedzi, błędy
- **Alerty:** Nieprawidłowe wzorce (np. wiele nieudanych autoryzacji z jednego IP)

## 7. Obsługa błędów

### Scenariusze błędów i kody statusu

#### 401 Unauthorized

**Przyczyny:**

1. Brak nagłówka `Authorization`
2. Nieprawidłowy format tokenu (nie zaczyna się od "Bearer ")
3. Wygasły token JWT (expired)
4. Nieprawidłowy podpis tokenu (invalid signature)
5. Token nie powiązany z aktywnym użytkownikiem
6. Użytkownik nieaktywny (`is_active = false`)

**Obsługa:**

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
```

**Logowanie:**

- Logowanie nieudanej próby autoryzacji z IP i timestamp
- Nie logowanie tokenu (ze względów bezpieczeństwa)

#### 400 Bad Request

**Przyczyny:**

1. `parent_id` nie jest liczbą całkowitą
2. `parent_id` jest ujemne lub zero
3. `parent_id` wskazuje na nieistniejącą kategorię
4. `include_children` nie jest wartością boolean

**Obsługa:**

```python
# Walidacja przez Pydantic
class CategoriesQueryParams(BaseModel):
    parent_id: Optional[int] = Field(None, gt=0)
    include_children: Optional[bool] = Field(False)

    @field_validator('parent_id')
    @classmethod
    def validate_parent_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError('parent_id must be a positive integer')
        return v

# Weryfikacja istnienia kategorii
if parent_id:
    parent_category = await session.get(Category, parent_id)
    if not parent_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent category with ID {parent_id} does not exist"
        )
```

**Logowanie:**

- Logowanie nieprawidłowych parametrów z user_id i parametrami

#### 404 Not Found

**Uwaga:** Ten endpoint nie zwraca 404, ponieważ zawsze zwraca listę (może być pusta). Jeśli `parent_id` nie istnieje, zwracany jest 400 Bad Request.

#### 500 Internal Server Error

**Przyczyny:**

1. Błąd połączenia z bazą danych
2. Błąd wykonania zapytania SQL
3. Błąd serializacji odpowiedzi
4. Nieoczekiwany wyjątek w kodzie

**Obsługa:**

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

try:
    # Operacje bazy danych
    categories = await session.execute(query)
except Exception as e:
    logger.error(f"Database error in GET /categories: {str(e)}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error"
    )
```

**Logowanie:**

- Logowanie pełnego stack trace w środowisku development
- Logowanie tylko ogólnego komunikatu w środowisku production
- Nie ujawnianie szczegółów błędu użytkownikowi

### Strategia obsługi błędów

#### Zasady ogólne

1. **Early Returns:** Sprawdzanie warunków błędów na początku funkcji
2. **Guard Clauses:** Użycie guard clauses zamiast zagnieżdżonych if-else
3. **Custom Exceptions:** Użycie custom exception classes dla różnych typów błędów
4. **Error Logging:** Logowanie wszystkich błędów z kontekstem
5. **User-Friendly Messages:** Komunikaty błędów zrozumiałe dla użytkownika (bez szczegółów technicznych)

#### Przykład implementacji

```python
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

router = APIRouter()

@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    parent_id: Optional[int] = Query(None, gt=0, description="Filter by parent category ID"),
    include_children: bool = Query(False, description="Include subcategories"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    # Guard clause: walidacja parent_id
    if parent_id is not None:
        parent_category = await session.get(Category, parent_id)
        if not parent_category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent category with ID {parent_id} does not exist"
            )

    try:
        # Happy path
        categories = await fetch_categories(session, parent_id, include_children)
        return CategoryListResponse(categories=categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## 8. Rozważania dotyczące wydajności

### Optymalizacje bazy danych

#### Wykorzystanie indeksów

1. **Indeks na `categories.parent_id`:**

   - **Nazwa:** `idx_categories_parent_id`
   - **Użycie:** Szybkie filtrowanie kategorii po kategorii nadrzędnej
   - **Typ:** B-tree index

2. **Indeks na `categories.name`:**

   - **Nazwa:** `idx_categories_name`
   - **Użycie:** Szybkie wyszukiwanie po nazwie (jeśli potrzebne w przyszłości)
   - **Typ:** B-tree index

3. **Indeks na `indexes.category_id`:**
   - **Nazwa:** `idx_indexes_category_id`
   - **Użycie:** Szybkie liczenie produktów w kategorii
   - **Typ:** B-tree index

#### Optymalizacja zapytań

1. **Eager Loading dla relacji:**

   ```python
   from sqlalchemy.orm import selectinload

   query = select(Category).options(
       selectinload(Category.children)
   )
   ```

   - **Korzyść:** Unikanie N+1 queries przy ładowaniu podkategorii
   - **Metoda:** `selectinload` dla optymalnej wydajności

2. **Agregacja produktów w jednym zapytaniu:**

   ```python
   from sqlalchemy import func, select

   # Subquery dla liczenia produktów
   products_count_subquery = (
       select(
           Index.category_id,
           func.count(Index.id).label('count')
       )
       .group_by(Index.category_id)
       .subquery()
   )

   # JOIN z subquery
   query = (
       select(Category, products_count_subquery.c.count.label('products_count'))
       .outerjoin(products_count_subquery, Category.id == products_count_subquery.c.category_id)
   )
   ```

   - **Korzyść:** Jedno zapytanie zamiast N zapytań dla każdej kategorii
   - **Wydajność:** Znacznie szybsze dla dużej liczby kategorii

3. **Rekurencyjne CTE dla hierarchii:**
   ```sql
   WITH RECURSIVE category_tree AS (
       SELECT id, name, parent_id, 0 as level
       FROM categories
       WHERE parent_id IS NULL  -- lub = :parent_id

       UNION ALL

       SELECT c.id, c.name, c.parent_id, ct.level + 1
       FROM categories c
       INNER JOIN category_tree ct ON c.parent_id = ct.id
       WHERE ct.level < 10  -- Ochrona przed cyklami
   )
   SELECT * FROM category_tree;
   ```
   - **Użycie:** Jeśli `include_children=true` i głęboka hierarchia
   - **Korzyść:** Jedno zapytanie zamiast rekurencyjnych zapytań w Pythonie

### Optymalizacje aplikacji

1. **Caching:**

   - **Strategia:** Cache odpowiedzi dla endpointu (kategorie rzadko się zmieniają)
   - **Czas życia cache:** 5-10 minut
   - **Implementacja:** Redis lub in-memory cache
   - **Invalidacja:** Przy tworzeniu/aktualizacji/usuwaniu kategorii

2. **Async/Await:**

   - **Użycie:** Wszystkie operacje I/O (baza danych) są asynchroniczne
   - **Korzyść:** Lepsza wydajność przy wielu równoczesnych żądaniach
   - **Implementacja:** SQLAlchemy async session, async endpoints w FastAPI

3. **Pagination (opcjonalna):**
   - **Uwaga:** Endpoint nie używa paginacji, ponieważ kategorie są zwykle nieliczne (< 100)
   - **Jeśli potrzebne:** Dodać paginację dla bardzo dużej liczby kategorii

### Metryki wydajności

#### Cele wydajnościowe

- **Czas odpowiedzi:** < 200ms dla typowego żądania (bez cache)
- **Czas odpowiedzi z cache:** < 50ms
- **Throughput:** > 100 requests/second per instance

#### Monitoring

- **Metryki:** Czas odpowiedzi, liczba zapytań do bazy, wykorzystanie cache
- **Alerty:** Czas odpowiedzi > 1s, błędy bazy danych > 1%

### Potencjalne wąskie gardła

1. **Rekurencyjne budowanie hierarchii:**

   - **Problem:** Jeśli `include_children=true` i głęboka hierarchia, rekurencyjne zapytania mogą być wolne
   - **Rozwiązanie:** Użycie CTE (Common Table Expression) w SQL dla rekurencyjnego zapytania

2. **Liczenie produktów:**

   - **Problem:** COUNT dla każdej kategorii osobno (N+1 queries)
   - **Rozwiązanie:** Agregacja w jednym zapytaniu z GROUP BY

3. **Brak cache:**
   - **Problem:** Każde żądanie wykonuje zapytanie do bazy
   - **Rozwiązanie:** Implementacja cache z odpowiednim TTL

## 9. Etapy wdrożenia

### Krok 1: Przygotowanie struktury projektu

1. **Utworzenie modułu kategorii:**

   ```
   backend/src/categories/
   ├── __init__.py
   ├── models.py          # SQLAlchemy models
   ├── schemas.py         # Pydantic schemas
   ├── service.py         # Business logic
   ├── routes.py          # FastAPI routes
   └── dependencies.py   # Dependencies (jeśli potrzebne)
   ```

2. **Rejestracja routera w `main.py`:**

   ```python
   from src.categories.routes import router as categories_router

   app.include_router(
       categories_router,
       prefix="/api/v1/categories",
       tags=["categories"]
   )
   ```

### Krok 2: Implementacja modeli SQLAlchemy

1. **Definicja modelu `Category`:**

   ```python
   # backend/src/categories/models.py
   from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
   from sqlalchemy.orm import relationship
   from sqlalchemy.sql import func
   from src.db.base import Base

   class Category(Base):
       __tablename__ = "categories"

       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(255), unique=True, nullable=False, index=True)
       parent_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True, index=True)
       created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
       updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

       # Relacje
       parent = relationship("Category", remote_side=[id], back_populates="children")
       children = relationship("Category", back_populates="parent")
       indexes = relationship("Index", back_populates="category")
   ```

2. **Weryfikacja relacji z modelem `Index`:**
   - Sprawdzenie, że model `Index` ma relację `category`

### Krok 3: Implementacja schematów Pydantic

1. **Definicja `CategoriesQueryParams`:**

   ```python
   # backend/src/categories/schemas.py
   from pydantic import BaseModel, Field, field_validator
   from typing import Optional, List
   from datetime import datetime

   class CategoriesQueryParams(BaseModel):
       parent_id: Optional[int] = Field(None, gt=0, description="Filter by parent category ID")
       include_children: Optional[bool] = Field(False, description="Include subcategories in response")

       @field_validator('parent_id')
       @classmethod
       def validate_parent_id(cls, v):
           if v is not None and v <= 0:
               raise ValueError('parent_id must be a positive integer')
           return v
   ```

2. **Definicja `CategoryResponse`:**

   ```python
   class CategoryResponse(BaseModel):
       id: int
       name: str
       parent_id: Optional[int]
       children: List['CategoryResponse'] = Field(default_factory=list)
       products_count: int = Field(ge=0, description="Number of products in this category")
       created_at: datetime

       class Config:
           from_attributes = True
   ```

3. **Definicja `CategoryListResponse`:**
   ```python
   class CategoryListResponse(BaseModel):
       categories: List[CategoryResponse]
   ```

### Krok 4: Implementacja logiki biznesowej (Service Layer)

1. **Utworzenie funkcji do pobierania kategorii:**

   ```python
   # backend/src/categories/service.py
   from sqlalchemy.ext.asyncio import AsyncSession
   from sqlalchemy import select, func
   from sqlalchemy.orm import selectinload
   from typing import Optional, List
   from src.categories.models import Category
   from src.indexes.models import Index

   async def get_categories(
       session: AsyncSession,
       parent_id: Optional[int] = None,
       include_children: bool = False
   ) -> List[Category]:
       # Budowanie zapytania
       query = select(Category)

       # Filtrowanie po parent_id
       if parent_id is not None:
           query = query.where(Category.parent_id == parent_id)
       else:
           query = query.where(Category.parent_id.is_(None))

       # Eager loading dla dzieci (jeśli potrzebne)
       if include_children:
           query = query.options(selectinload(Category.children))

       # Wykonanie zapytania
       result = await session.execute(query)
       categories = result.scalars().all()

       return categories
   ```

2. **Implementacja liczenia produktów:**

   ```python
   async def count_products_per_category(
       session: AsyncSession,
       category_ids: List[int]
   ) -> dict[int, int]:
       """Zwraca słownik {category_id: products_count}"""
       query = (
           select(Index.category_id, func.count(Index.id).label('count'))
           .where(Index.category_id.in_(category_ids))
           .group_by(Index.category_id)
       )
       result = await session.execute(query)
       return {row.category_id: row.count for row in result}
   ```

3. **Implementacja budowania hierarchii:**
   ```python
   def build_category_hierarchy(
       categories: List[Category],
       products_count_map: dict[int, int],
       max_depth: int = 10
   ) -> List[CategoryResponse]:
       """Rekurencyjne budowanie hierarchii kategorii"""
       # Mapowanie kategorii po ID
       category_map = {cat.id: cat for cat in categories}

       # Funkcja pomocnicza do budowania drzewa
       def build_tree(category: Category, depth: int = 0) -> CategoryResponse:
           if depth > max_depth:
               raise ValueError("Maximum category depth exceeded")

           children = []
           if include_children:
               for child in category.children:
                   children.append(build_tree(child, depth + 1))

           products_count = products_count_map.get(category.id, 0)

           return CategoryResponse(
               id=category.id,
               name=category.name,
               parent_id=category.parent_id,
               children=children,
               products_count=products_count,
               created_at=category.created_at
           )

       # Budowanie drzewa dla kategorii głównych
       root_categories = [cat for cat in categories if cat.parent_id is None]
       return [build_tree(cat) for cat in root_categories]
   ```

### Krok 5: Implementacja endpointu FastAPI

1. **Definicja route handler:**

   ```python
   # backend/src/categories/routes.py
   from fastapi import APIRouter, Depends, HTTPException, Query, status
   from sqlalchemy.ext.asyncio import AsyncSession
   from typing import Optional
   from src.categories.schemas import CategoryListResponse, CategoryResponse
   from src.categories.service import get_categories, count_products_per_category, build_category_hierarchy
   from src.categories.models import Category
   from src.db.dependencies import get_db_session
   from src.auth.dependencies import get_current_user
   from src.users.models import User
   import logging

   logger = logging.getLogger(__name__)
   router = APIRouter()

   @router.get("/", response_model=CategoryListResponse)
   async def get_categories_endpoint(
       parent_id: Optional[int] = Query(None, gt=0, description="Filter by parent category ID"),
       include_children: bool = Query(False, description="Include subcategories"),
       current_user: User = Depends(get_current_user),
       session: AsyncSession = Depends(get_db_session)
   ):
       # Walidacja parent_id (jeśli podane)
       if parent_id is not None:
           parent_category = await session.get(Category, parent_id)
           if not parent_category:
               raise HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail=f"Parent category with ID {parent_id} does not exist"
               )

       try:
           # Pobranie kategorii
           categories = await get_categories(session, parent_id, include_children)

           # Liczenie produktów
           category_ids = [cat.id for cat in categories]
           products_count_map = await count_products_per_category(session, category_ids)

           # Budowanie odpowiedzi
           if include_children:
               category_responses = build_category_hierarchy(categories, products_count_map)
           else:
               category_responses = [
                   CategoryResponse(
                       id=cat.id,
                       name=cat.name,
                       parent_id=cat.parent_id,
                       children=[],
                       products_count=products_count_map.get(cat.id, 0),
                       created_at=cat.created_at
                   )
                   for cat in categories
               ]

           return CategoryListResponse(categories=category_responses)

       except Exception as e:
           logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail="Internal server error"
           )
   ```

### Krok 6: Implementacja autoryzacji

1. **Sprawdzenie dependency `get_current_user`:**

   - Weryfikacja, że dependency istnieje i działa poprawnie
   - Test z nieprawidłowym tokenem (powinien zwrócić 401)

2. **Dodanie dependency do endpointu:**
   - Użycie `Depends(get_current_user)` w parametrach funkcji

### Krok 7: Testy jednostkowe

1. **Test pobierania wszystkich kategorii:**

   ```python
   # tests/test_categories.py
   import pytest
   from fastapi.testclient import TestClient

   def test_get_categories_success(client: TestClient, auth_headers: dict):
       response = client.get("/api/v1/categories", headers=auth_headers)
       assert response.status_code == 200
       data = response.json()
       assert "categories" in data
       assert isinstance(data["categories"], list)
   ```

2. **Test filtrowania po parent_id:**

   ```python
   def test_get_categories_with_parent_id(client: TestClient, auth_headers: dict):
       response = client.get("/api/v1/categories?parent_id=1", headers=auth_headers)
       assert response.status_code == 200
   ```

3. **Test nieprawidłowego parent_id:**

   ```python
   def test_get_categories_invalid_parent_id(client: TestClient, auth_headers: dict):
       response = client.get("/api/v1/categories?parent_id=999", headers=auth_headers)
       assert response.status_code == 400
   ```

4. **Test bez autoryzacji:**
   ```python
   def test_get_categories_unauthorized(client: TestClient):
       response = client.get("/api/v1/categories")
       assert response.status_code == 401
   ```

### Krok 8: Testy integracyjne

1. **Test z rzeczywistą bazą danych:**

   - Utworzenie testowych kategorii w bazie
   - Weryfikacja odpowiedzi z rzeczywistymi danymi

2. **Test wydajności:**
   - Test z dużą liczbą kategorii (> 100)
   - Pomiar czasu odpowiedzi

### Krok 9: Dokumentacja API

1. **Dodanie opisu endpointu w FastAPI:**

   ```python
   @router.get(
       "/",
       response_model=CategoryListResponse,
       summary="List all product categories",
       description="Get a hierarchical list of all product categories with optional filtering by parent category",
       responses={
           200: {"description": "Success"},
           400: {"description": "Bad request - invalid parameters"},
           401: {"description": "Unauthorized"},
           500: {"description": "Internal server error"}
       }
   )
   ```

2. **Aktualizacja dokumentacji OpenAPI:**
   - Automatyczna generacja przez FastAPI
   - Dostępna pod `/docs` (w środowisku development)

### Krok 10: Code Review i optymalizacja

1. **Przegląd kodu:**

   - Sprawdzenie zgodności z zasadami clean code
   - Weryfikacja obsługi błędów
   - Sprawdzenie bezpieczeństwa

2. **Optymalizacja:**
   - Analiza zapytań SQL (sprawdzenie EXPLAIN)
   - Optymalizacja N+1 queries
   - Implementacja cache (jeśli potrzebne)

### Krok 11: Deployment

1. **Przygotowanie do wdrożenia:**

   - Weryfikacja zmiennych środowiskowych
   - Sprawdzenie migracji bazy danych

2. **Wdrożenie:**

   - Deployment na środowisko testowe
   - Weryfikacja działania endpointu
   - Deployment na środowisko produkcyjne

3. **Monitoring:**
   - Konfiguracja alertów dla błędów
   - Monitoring metryk wydajności

## 10. Dodatkowe uwagi

### Rozszerzenia w przyszłości

1. **Paginacja:**

   - Jeśli liczba kategorii znacznie wzrośnie, dodać paginację
   - Użycie `page` i `limit` parametrów

2. **Sortowanie:**

   - Parametr `sort_by` (np. `name`, `products_count`)
   - Parametr `order` (asc/desc)

3. **Wyszukiwanie:**

   - Parametr `search` do wyszukiwania kategorii po nazwie

4. **Filtrowanie:**
   - Filtrowanie po minimalnej liczbie produktów
   - Filtrowanie tylko kategorii z produktami

### Wsparcie dla różnych języków

- Jeśli w przyszłości dodane zostanie wsparcie dla wielu języków, rozważyć dodanie pola `locale` do odpowiedzi
- Filtrowanie kategorii po języku użytkownika

### Wersjonowanie API

- Endpoint jest częścią API v1 (`/api/v1/categories`)
- W przypadku zmian breaking changes, utworzyć nową wersję (`/api/v2/categories`)
