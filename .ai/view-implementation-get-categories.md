# API Endpoint Implementation Plan: GET /categories

## 1. Przegląd punktu końcowego

Endpoint `/categories` służy do pobierania hierarchicznej listy wszystkich kategorii produktów w systemie. Umożliwia filtrowanie kategorii według kategorii nadrzędnej oraz opcjonalne włączenie podkategorii w odpowiedzi. Jest to endpoint tylko do odczytu, który zwraca strukturę drzewiastą kategorii wraz z liczbą przypisanych produktów.

## 2. Szczegóły żądania

- **Metoda HTTP:** GET
- **Struktura URL:** `/categories`
- **Parametry:**
  - **Wymagane:** brak
  - **Opcjonalne:**
    - `parent_id` (integer, optional) - ID kategorii nadrzędnej do filtrowania
    - `include_children` (boolean, optional) - czy włączyć podkategorie w odpowiedzi
- **Request Body:** brak
- **Headers:**
  - `Authorization: Bearer <jwt_token>` (wymagane)

## 3. Wykorzystywane typy

### DTOs:

- `CategoryResponse` - podstawowa struktura kategorii z dziećmi i liczbą produktów
- `CategoryListResponse` - wrapper z listą kategorii
- `CategoriesQueryParams` - parametry zapytania

### Command Modele:

- Brak (endpoint tylko do odczytu)

### Typy bazy danych:

- `Category` - tabela categories z polami: id, name, parent_id, created_at
- `Product` - tabela indexes z polem category_id do liczenia produktów

## 4. Szczegóły odpowiedzi

### Sukces (200 OK):

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

### Błędy:

- **401 Unauthorized** - brak lub nieprawidłowy token autoryzacji
- **400 Bad Request** - nieprawidłowe parametry (np. parent_id nie istnieje)
- **500 Internal Server Error** - błędy bazy danych

## 5. Przepływ danych

1. **Walidacja autoryzacji** - sprawdzenie JWT tokenu
2. **Walidacja parametrów** - walidacja parent_id i include_children
3. **Pobranie danych z bazy** - zapytanie do tabeli categories z opcjonalnym filtrowaniem
4. **Liczenie produktów** - agregacja liczby produktów dla każdej kategorii
5. **Budowanie hierarchii** - rekurencyjne budowanie struktury drzewiastej
6. **Zwrócenie odpowiedzi** - serializacja do JSON

## 6. Względy bezpieczeństwa

### Autoryzacja:

- Wymagany JWT token w headerze Authorization
- Sprawdzenie ważności tokenu i powiązania z użytkownikiem
- Wszystkie operacje filtrowane po user_id (izolacja danych)

### Walidacja danych:

- Walidacja `parent_id` - sprawdzenie czy kategoria istnieje w bazie
- Walidacja `include_children` - sprawdzenie typu boolean
- Sanityzacja parametrów zapytania

### Ochrona przed atakami:

- SQL injection - użycie ORM SQLAlchemy z parametrami
- Rate limiting - standardowe ograniczenia na endpoint
- CORS - konfiguracja dla domeny web app

## 7. Obsługa błędów

### Scenariusze błędów:

1. **401 Unauthorized:**

   - Brak tokenu autoryzacji
   - Nieprawidłowy format tokenu
   - Wygasły token
   - Nieprawidłowy podpis tokenu

2. **400 Bad Request:**

   - `parent_id` nie istnieje w bazie danych
   - Nieprawidłowy format `parent_id` (nie jest liczbą)
   - Nieprawidłowy format `include_children` (nie jest boolean)

3. **500 Internal Server Error:**
   - Błąd połączenia z bazą danych
   - Błąd wykonania zapytania SQL
   - Błąd serializacji odpowiedzi

### Logowanie błędów:

- Logowanie wszystkich błędów autoryzacji
- Logowanie błędów walidacji z parametrami
- Logowanie błędów bazy danych z kontekstem

## 8. Rozważania dotyczące wydajności

### Optymalizacje:

- **Indeksy bazy danych:** wykorzystanie istniejących indeksów na `categories.name` i `categories.parent_id`
- **Lazy loading:** ładowanie podkategorii tylko gdy `include_children=true`
- **Caching:** rozważenie cache'owania hierarchii kategorii (rzadko się zmienia)
- **Paginacja:** dla dużych ilości kategorii (obecnie nie wymagana)

### Potencjalne wąskie gardła:

- Rekurencyjne budowanie hierarchii dla głębokich struktur
- Liczenie produktów dla każdej kategorii (może wymagać optymalizacji)

### Monitoring:

- Czas odpowiedzi endpointu
- Liczba zapytań do bazy danych
- Wykorzystanie pamięci podczas budowania hierarchii

## 9. Etapy wdrożenia

1. **Utworzenie serwisu kategorii**

   - Stworzenie `CategoryService` w `src/lib/services/category_service.py`
   - Implementacja metody `get_categories()` z obsługą parametrów
   - Implementacja metody `get_category_hierarchy()` dla budowania drzewa

2. **Implementacja endpointu**

   - Stworzenie endpointu `GET /categories` w `src/api/categories.py`
   - Implementacja dependency injection dla autoryzacji
   - Implementacja walidacji parametrów z Pydantic

3. **Walidacja i obsługa błędów**

   - Implementacja custom validators dla `parent_id`
   - Implementacja exception handlers dla różnych scenariuszy błędów
   - Dodanie logowania błędów

4. **Testy jednostkowe**

   - Testy dla `CategoryService` z różnymi scenariuszami
   - Testy endpointu z różnymi parametrami
   - Testy obsługi błędów

5. **Testy integracyjne**

   - Testy z rzeczywistą bazą danych
   - Testy autoryzacji z JWT tokenami
   - Testy wydajności dla dużych hierarchii

6. **Dokumentacja**

   - Aktualizacja dokumentacji API
   - Dodanie przykładów użycia
   - Dokumentacja parametrów i odpowiedzi

7. **Deployment i monitoring**
   - Wdrożenie na środowisko testowe
   - Konfiguracja monitoringu wydajności
   - Testy obciążeniowe
   - Wdrożenie na produkcję
