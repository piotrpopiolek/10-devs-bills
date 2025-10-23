# API Endpoint Implementation Plan: POST /bills

## 1. Przegląd punktu końcowego

Endpoint `POST /bills` umożliwia użytkownikom przesyłanie zdjęć paragonów w celu automatycznego przetworzenia przez system OCR i AI. Po przesłaniu obrazu, system rozpoczyna asynchroniczny proces ekstrakcji tekstu, kategoryzacji produktów i zapisywania danych do bazy. Użytkownik otrzymuje natychmiastową odpowiedź z podstawowymi informacjami o rachunku, podczas gdy pełne przetwarzanie odbywa się w tle.

## 2. Szczegóły żądania

- **Metoda HTTP:** POST
- **Struktura URL:** `/bills`
- **Content-Type:** `multipart/form-data`
- **Parametry:**
  - **Wymagane:**
    - `image` (File) - Zdjęcie paragonu w formacie JPG/PNG/WebP
    - `bill_date` (string) - Data paragonu w formacie ISO 8601
  - **Opcjonalne:**
    - `shop_name` (string) - Nazwa sklepu
    - `shop_address` (string) - Adres sklepu
- **Request Body:** Multipart form data z plikiem obrazu i metadanymi

## 3. Wykorzystywane typy

### DTOs:

- `BillCreateRequest` - Request DTO z walidacją
- `BillResponse` - Response DTO z podstawowymi informacjami
- `ShopResponse` - Informacje o sklepie

### Command Modele:

- `CreateBillCommand` - Model dla logiki biznesowej
- `ApiResponse<BillResponse>` - Wrapper odpowiedzi API

### Typy bazy danych:

- `Bill` - Główna tabela rachunków
- `Shop` - Tabela sklepów
- `ProcessingStatus` - Enum statusu przetwarzania

## 4. Szczegóły odpowiedzi

### Sukces (201 Created):

```json
{
  "data": {
    "id": 1,
    "status": "processing",
    "bill_date": "2024-01-01T10:30:00Z",
    "total_amount": null,
    "shop": {
      "id": 1,
      "name": "Supermarket ABC",
      "address": "123 Main St",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "items_count": 0,
    "created_at": "2024-01-01T10:30:00Z"
  },
  "success": true,
  "message": "Bill uploaded successfully and processing started"
}
```

### Kody błędów:

- **400 Bad Request** - Nieprawidłowe dane wejściowe
- **401 Unauthorized** - Brak autoryzacji
- **413 Payload Too Large** - Plik za duży (>10MB)
- **429 Too Many Requests** - Przekroczony limit miesięczny
- **500 Internal Server Error** - Błąd serwera

## 5. Przepływ danych

1. **Walidacja żądania:**

   - Sprawdzenie autoryzacji JWT
   - Walidacja pliku (format, rozmiar)
   - Walidacja daty (nie w przyszłości)
   - Sprawdzenie limitu miesięcznego

2. **Przetwarzanie sklepu:**

   - Wyszukanie istniejącego sklepu po nazwie i adresie
   - Utworzenie nowego sklepu jeśli nie istnieje

3. **Zapisanie rachunku:**

   - Utworzenie rekordu w tabeli `bills` ze statusem "pending"
   - Generowanie unikalnego hash obrazu
   - Ustawienie daty wygaśnięcia obrazu (6 miesięcy)

4. **Upload obrazu:**

   - Przesłanie do Supabase Storage
   - Generowanie signed URL z wygaśnięciem

5. **Rozpoczęcie przetwarzania:**

   - Dodanie zadania do kolejki Celery
   - Zmiana statusu na "processing"
   - Zwrócenie odpowiedzi użytkownikowi

6. **Asynchroniczne przetwarzanie (w tle):**
   - OCR z PaddlePaddle
   - Kategoryzacja AI z OpenAI
   - Zapisywanie pozycji do `bill_items`
   - Aktualizacja statusu na "completed"

## 6. Względy bezpieczeństwa

### Uwierzytelnianie i autoryzacja:

- Wymagany JWT token w nagłówku Authorization
- Walidacja tokenu przez middleware
- Filtrowanie wszystkich operacji po `user_id`

### Walidacja plików:

- Sprawdzenie typu MIME (tylko image/jpeg, image/png, image/webp)
- Maksymalny rozmiar pliku: 10MB
- Generowanie bezpiecznego hash dla deduplikacji
- Walidacja rozszerzenia pliku

### Rate limiting:

- Limit 100 rachunków miesięcznie na użytkownika
- Sprawdzenie w tabeli `bills` dla bieżącego miesiąca
- Graceful degradation z informacyjnym komunikatem

### Izolacja danych:

- Wszystkie operacje filtrowane po `user_id`
- Brak dostępu do danych innych użytkowników
- Walidacja własności zasobów

## 7. Obsługa błędów

### Błędy walidacji (400):

- Nieprawidłowy format pliku
- Plik za duży
- Nieprawidłowa data (w przyszłości)
- Brak wymaganych pól

### Błędy autoryzacji (401):

- Brak tokenu JWT
- Nieprawidłowy token
- Token wygasły

### Błędy limitu (429):

- Przekroczony limit miesięczny
- Informacyjny komunikat o dostępnych opcjach

### Błędy serwera (500):

- Błąd uploadu do Supabase Storage
- Błąd połączenia z bazą danych
- Błąd dodania zadania do kolejki

### Logowanie błędów:

- Strukturalne logi z kontekstem użytkownika
- Monitoring błędów OCR i AI
- Alerty dla krytycznych błędów

## 8. Rozważania dotyczące wydajności

### Optymalizacja obrazów:

- Kompresja obrazów przed uploadem
- Generowanie thumbnaili dla UI
- Lazy loading w interfejsie

### Asynchroniczne przetwarzanie:

- Background tasks dla OCR i AI
- Kolejka Celery z priorytetami
- Monitoring długości kolejki

### Cache'owanie:

- Cache wyników wyszukiwania sklepów
- Cache limitów użytkowników
- Redis dla sesji i cache

### Indeksy bazy danych:

- Indeks na `(user_id, bill_date)` dla szybkich zapytań
- Indeks na `status` dla monitoringu
- Indeks na `image_expires_at` dla cleanup

## 9. Etapy wdrożenia

### Etap 1: Podstawowa struktura

1. Utworzenie endpointu FastAPI z podstawową walidacją
2. Implementacja middleware autoryzacji JWT
3. Podstawowa walidacja multipart/form-data
4. Testy jednostkowe dla walidacji

### Etap 2: Integracja z bazą danych

1. Implementacja BillService z operacjami CRUD
2. Implementacja ShopService z deduplikacją
3. Migracje bazy danych z indeksami
4. Testy integracyjne z bazą danych

### Etap 3: Upload plików

1. Konfiguracja Supabase Storage
2. Implementacja FileService z walidacją
3. Generowanie signed URLs
4. Testy uploadu plików

### Etap 4: Rate limiting

1. Implementacja RateLimitService
2. Middleware sprawdzający limity miesięczne
3. Cache limitów w Redis
4. Testy rate limiting

### Etap 5: Asynchroniczne przetwarzanie

1. Konfiguracja Celery z RabbitMQ
2. Implementacja OCR task
3. Implementacja AI categorization task
4. Monitoring i alerty

### Etap 6: Obsługa błędów i logowanie

1. Implementacja custom exception handlers
2. Strukturalne logowanie z kontekstem
3. Monitoring błędów i metryki
4. Testy obsługi błędów

### Etap 7: Optymalizacja i monitoring

1. Implementacja cache'owania
2. Optymalizacja zapytań do bazy
3. Monitoring wydajności
4. Load testing

### Etap 8: Dokumentacja i testy

1. Dokumentacja API z przykładami
2. Testy end-to-end
3. Testy bezpieczeństwa
4. Deployment i monitoring produkcyjny
