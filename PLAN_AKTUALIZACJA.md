# Plan kolejnych kroków — Bills MVP (Zaktualizowany)

**Data aktualizacji:** 2025-12-08 (zaktualizowano: Receipt Processing Pipeline ukończony)  
**Status ogólny:** ~65% ukończone

---

## ✅ Ukończone (Faza 1 - Foundation)

### 1.1. GET /users/me z usage statistics ✅

- **Status:** Ukończone
- **Endpoint:** `GET /api/v1/users/me`
- **Funkcjonalność:** Zwraca profil użytkownika z statystykami użycia (bills_this_month, monthly_limit, remaining_bills)
- **Pliki:** `backend/src/users/routes.py`, `backend/src/users/services.py`

### 1.2. Rate limiting middleware ✅

- **Status:** Ukończone
- **Funkcjonalność:** Middleware sprawdzający limit 100 paragonów/miesiąc
- **Implementacja:** Dependency `check_monthly_bills_limit` w `POST /bills`
- **Pliki:** `backend/src/middleware/rate_limit.py`

### 1.3. User isolation w Bills ✅

- **Status:** Ukończone
- **Zaimplementowane:**
  - ✅ `POST /bills` - wymusza `user_id` z tokena JWT
  - ✅ `GET /bills` - filtruje paragony po `current_user.id`
  - ✅ `GET /bills/{id}` - sprawdza ownership (zwraca 403 jeśli nie należy do użytkownika)
  - ✅ `PATCH /bills/{id}` - sprawdza ownership przed aktualizacją, blokuje zmianę `user_id`
  - ✅ `DELETE /bills/{id}` - sprawdza ownership przed usunięciem
  - ✅ Rate limiting działa per user
  - ✅ `BillService.get_all(user_id)` - filtrowanie na poziomie SQL
  - ✅ `BillService.get_by_id_and_user()` - nowa metoda z weryfikacją ownership
  - ✅ `BillAccessDeniedError` - błąd domenowy z handlerem HTTP 403
- **Pliki:** `backend/src/bills/routes.py`, `backend/src/bills/services.py`, `backend/src/common/exceptions.py`, `backend/src/error_handler.py`

### 3.1. Telegram Webhook endpoint ✅

- **Status:** Ukończone
- **Endpoint:** `POST /api/v1/webhooks/telegram`
- **Funkcjonalność:** Odbiera aktualizacje z Telegrama, weryfikuje secret token
- **Pliki:** `backend/src/telegram/routes.py`, `backend/src/telegram/services.py`

### 3.2. Telegram Bot Service (podstawowe komendy) ✅

- **Status:** Ukończone
- **Zaimplementowane komendy:**
  - ✅ `/start` - powitanie
  - ✅ `/login` - generowanie magic link i auto-rejestracja użytkownika
  - ✅ `/dzis`, `/tydzien`, `/miesiac` - placeholdery (do integracji z Reports)
- **Pliki:** `backend/src/telegram/services.py`

### 3.3. Storage Service ✅

- **Status:** Ukończone
- **Funkcjonalność:** Serwis do uploadu plików do Supabase Storage z fallbackiem do lokalnego storage
- **Zaimplementowane:**
  - ✅ Upload plików (bytes) z walidacją rozmiaru (max 20MB)
  - ✅ Generowanie SHA256 hash dla deduplikacji
  - ✅ Integracja z Supabase Storage
  - ✅ Fallback do lokalnego storage
  - ✅ Generowanie ścieżek plików per user
  - ✅ Obliczanie daty wygaśnięcia (6 miesięcy)
- **Pliki:** `backend/src/storage/service.py`

### 3.4. Telegram Bot - obsługa zdjęć paragonów ✅

- **Status:** Ukończone (częściowo - brak integracji z OCR)
- **Funkcjonalność:** Automatyczne przetwarzanie zdjęć paragonów wysłanych do bota
- **Zaimplementowane:**
  - ✅ `MessageHandler` dla photos i documents
  - ✅ Pobieranie pliku z Telegram API
  - ✅ Upload do Storage Service
  - ✅ Tworzenie rekordu Bill z statusem PENDING
  - ✅ Auto-rejestracja użytkownika przy pierwszym użyciu
- **Brakujące:**
  - 🔴 Integracja z OCR Service (TODO w linii 173 w `handlers.py`)
  - 🔴 Potwierdzenie przetworzenia po zakończeniu OCR/AI
- **Pliki:** `backend/src/telegram/handlers.py` (handle_receipt_image)

### 5.1. OCR Service (LLM-based) ✅

- **Status:** Ukończone
- **Priorytet:** Wysoki
- **Założenia MVP:**
  - Implementacja oparta na modelach LLM (Gemini 1.5 Flash)
  - Szybsze do wdrożenia, wystarczające dla MVP
  - Pełny OCR z PaddlePaddle zostanie zaimplementowany po MVP (patrz sekcja "🟢 Nice to have")
- **Zaimplementowane:**
  - ✅ `backend/src/ocr/services.py` - `OCRService` z metodą `extract_data()`
  - ✅ Integracja z Gemini API (Google Generative AI)
  - ✅ Prompt engineering dla ekstrakcji danych z paragonów polskich
  - ✅ Error handling dla nieczytelnych paragonów (`FileValidationError`, `ExtractionError`, `AIServiceError`)
  - ✅ Zwraca structured data (items, total, date, shop_name) w formacie JSON
  - ✅ Walidacja odpowiedzi LLM za pomocą Pydantic schemas (`LLMReceiptExtraction`, `OCRReceiptData`)
  - ✅ Retry logic z tenacity dla błędów API (ResourceExhausted, ServiceUnavailable, etc.)
  - ✅ Walidacja plików (magic bytes, rozmiar max 10MB, formaty: JPEG, PNG, WEBP)
  - ✅ Walidacja sumy pozycji vs total_amount (±10% tolerancja)
  - ✅ Endpoint `POST /api/v1/ocr/extract` z rate limiting (5 req/min per user)
  - ✅ Zwraca `category_suggestion` dla każdego produktu (podstawowa kategoryzacja)
- **Pliki:** `backend/src/ocr/services.py`, `backend/src/ocr/routes.py`, `backend/src/ocr/schemas.py`, `backend/src/ocr/exceptions.py`
- **Uwaga:** Używa Gemini API zamiast OpenAI Vision API (podobne rozwiązanie LLM-based)

### 8.1. Frontend Auth Verification Page ✅

- **Status:** Ukończone
- **Strona:** `/auth/verify`
- **Funkcjonalność:** Weryfikuje token z URL, zapisuje sesję, przekierowuje na dashboard
- **Pliki:** `astro/src/pages/auth/verify.astro`

### 8.2. Auth Service Frontend ✅

- **Status:** Ukończone
- **Funkcjonalność:** Serwis do zarządzania autentykacją (verify, setSession, clearSession, isAuthenticated)
- **Pliki:** `astro/src/lib/services/auth.ts`

---

## 🔴 Krytyczne (Blokujące MVP)

### 5.2. AI Categorization Service

- **Status:** Częściowo (podstawowa kategoryzacja w OCR Service)
- **Priorytet:** Wysoki
- **Zrobione:**
  - ✅ OCR Service zwraca `category_suggestion` dla każdego produktu (podstawowa kategoryzacja przez LLM)
- **Brakujące:**
  - 🔴 Osobny serwis `backend/src/ai/service.py` dla zaawansowanej kategoryzacji
  - 🔴 Normalizacja nazw produktów (mapowanie wariantów OCR na standardowe nazwy)
  - 🔴 Mapowanie do Product Index (słownik produktów w bazie danych)
  - 🔴 Fallback do kategorii "Inne" dla nieznanych produktów
  - 🔴 Uczenie się na podstawie weryfikacji użytkownika (product aliases)
- **Szacunek:** 8-10h (uproszczone dzięki podstawowej kategoryzacji w OCR)

### 5.3. Receipt Processing Pipeline ✅

- **Status:** Ukończone
- **Priorytet:** Wysoki
- **Zrobione:**
  - ✅ `StorageService.download_file()` - pobieranie plików z Supabase Storage
  - ✅ `ShopService.get_or_create_by_name()` - tworzenie/znajdowanie sklepów (z refaktoryzacją - wspólna metoda `_find_by_name_and_address()`)
  - ✅ `BillsProcessorService` - pełny orchestrator przetwarzania paragonów
  - ✅ Integracja OCR Service → Database (tworzenie BillItems)
  - ✅ Integracja z Telegram Bot (wywołanie OCR po uploadzie zdjęcia)
  - ✅ Walidacja sumy (items total vs receipt total) - w OCR Service
  - ✅ Status tracking (pending → processing → completed/error) w Bill model
  - ✅ Zapis bill_items z danymi z OCR (name, quantity, prices, category_suggestion, confidence_score)
  - ✅ Aktualizacja statusu Bill po zakończeniu przetwarzania
  - ✅ Factory function dla Dependency Injection (`get_bills_processor_service()`)
  - ✅ Obsługa błędów z zapisem error_message
- **Brakujące (opcjonalne, post-MVP):**
  - 🟢 Background task (Dramatiq/Celery) dla async processing (można odłożyć na post-MVP)
  - 🟢 Testy jednostkowe i integracyjne
- **Pliki:** `backend/src/processing/service.py`, `backend/src/processing/dependencies.py`, `backend/src/telegram/handlers.py`

---

## 🟡 Ważne (Dla pełnego MVP)

### 2.1. Reports module

- **Status:** Brak
- **Priorytet:** Średni
- **Zadania:**
  - Utworzyć `backend/src/reports/` module
  - Zaimplementować `GET /api/v1/reports/daily`
  - Zaimplementować `GET /api/v1/reports/weekly`
  - Zaimplementować `GET /api/v1/reports/monthly`
  - Dodać logikę agregacji (top categories, shops breakdown)
  - Filtrować po `current_user.id`
- **Szacunek:** 6-8h

### 3.2. Telegram Bot Service (rozbudowa)

- **Status:** Częściowo (obsługa zdjęć i integracja z OCR ukończone)
- **Priorytet:** Średni
- **Zrobione:**
  - ✅ Obsługa zdjęć paragonów (MessageHandler dla photos/documents)
  - ✅ Upload do Storage i tworzenie Bill record
  - ✅ Integracja OCR Service w `handle_receipt_image()` - **UKOŃCZONE**
  - ✅ `send_receipt_confirmation(bill_id)` - potwierdzenie przetworzenia (po zakończeniu OCR/AI) - **UKOŃCZONE**
  - ✅ Integracja z Receipt Processing Pipeline (trigger OCR task) - **UKOŃCZONE**
- **Brakujące funkcjonalności:**
  - 🟡 `send_verification_request(bill_item_id)` - prośba o weryfikację (dla confidence < 0.8)
  - 🟡 `send_summary(user_id, period)` - podsumowanie wydatków (integracja z Reports)
- **Szacunek:** 2-3h (po zaimplementowaniu Reports module)

### 4.1. Verification workflow

- **Status:** Częściowo (endpoint istnieje, brak integracji)
- **Priorytet:** Średni
- **Zadania:**
  - Ulepszyć `PUT /bill-items/{id}/verify`
  - Dodać `GET /bill-items/pending-verification`
  - Dodać logikę confidence threshold (< 0.8 → weryfikacja)
  - Integracja z Telegram Bot Service
  - Dodać `verification_source` enum (auto/user)
- **Szacunek:** 4-5h

---

## 🟢 Nice to have (Można odłożyć)

### 1.4. File upload dla POST /bills (opcjonalne)

- **Status:** Nie wymagane (wszystkie zdjęcia przesyłane przez Telegram)
- **Priorytet:** Niski (można odłożyć)
- **Uwaga:** Jeśli w przyszłości będzie potrzeba bezpośredniego uploadu przez API (np. dla integracji z innymi aplikacjami), można zaimplementować:
  - Zmienić `POST /bills` na `multipart/form-data` (użyć `File` z FastAPI)
  - Dodać walidację pliku (format: jpg/png/webp, rozmiar: max 20MB)
  - Wykorzystać istniejący `StorageService` do uploadu
- **Szacunek:** 3-4h (jeśli będzie potrzebne)

### 6.1. Admin endpoints

- **Status:** Brak
- **Priorytet:** Niski
- **Zadania:**
  - Dodać `is_admin` field do User model
  - Utworzyć `require_admin()` dependency w `deps.py`
  - Dodać admin-only endpoints dla categories/products
- **Szacunek:** 3-4h

### 7.1. Security & Polish

- **Status:** Częściowo
- **Priorytet:** Niski
- **Zadania:**
  - Zweryfikować CORS dla production
  - Dodać security headers (HSTS, CSP)
  - Dodać walidację dat (nie w przyszłości)
  - Dodać walidację sum (items total = bill total)
- **Szacunek:** 2-3h

### 7.2. PaddlePaddle OCR (Post-MVP)

- **Status:** Zaplanowane po MVP
- **Priorytet:** Niski (ulepszenie po MVP)
- **Założenia:**
  - Zastąpi LLM-based OCR po zakończeniu MVP
  - Lepsza dokładność i kontrola nad procesem OCR
  - Możliwość lokalnego przetwarzania (offline)
- **Zadania:**
  - Integracja z PaddlePaddle-OCR
  - Dodać preprocessing obrazów (deskewing, denoising, contrast enhancement)
  - Dodać post-processing (confidence scoring, text cleaning)
  - Migracja z LLM-based OCR do PaddlePaddle
  - Zachować kompatybilność API (abstrakcja OCR Service)
- **Szacunek:** 8-10h

---

## 📋 Rekomendowany plan działania

### Sprint 1 (Tydzień 1-2): Foundation + User Isolation ✅

- ✅ GET /users/me z usage statistics
- ✅ Rate limiting middleware
- ✅ User isolation w Bills (wszystkie endpointy zabezpieczone)

### Sprint 2 (Tydzień 3-4): Core Features

- 🟡 Reports module (daily/weekly/monthly)
- ✅ Telegram Bot Service - obsługa zdjęć (zrobione, brak integracji z OCR)

### Sprint 3 (Tydzień 5-6): AI & Processing

- ✅ OCR Service (LLM-based - Gemini API) - **UKOŃCZONE**
- 🟡 AI Categorization Service (częściowo - podstawowa kategoryzacja w OCR)
- 🔴 Receipt Processing Pipeline

### Sprint 4 (Tydzień 7-8): Polish & Integration

- 🟡 Verification workflow improvements
- 🟡 Telegram Bot Service - pełna integracja z Reports
- 🟢 Admin endpoints
- 🟢 Security enhancements

---

## 🎯 Priorytetyzacja (według PRD MVP)

### Krytyczne (blokujące MVP):

- ✅ Auth (zrobione)
- ✅ Rate limiting
- ✅ User isolation (wszystkie endpointy zabezpieczone) - **UKOŃCZONE**
- ✅ Telegram webhook
- ✅ Telegram Bot - obsługa zdjęć (upload + Bill creation + OCR integration) - **UKOŃCZONE**
- ✅ Storage Service (Supabase + fallback)
- ✅ OCR Service (LLM-based - Gemini API) - **UKOŃCZONE**
- 🟡 AI Categorization (częściowo - podstawowa kategoryzacja w OCR)
- ✅ Receipt Processing Pipeline - **UKOŃCZONE**

### Ważne (dla pełnego MVP):

- 🟡 Reports
- 🟡 Telegram Bot Service (rozbudowa)
- 🟡 Verification workflow

### Nice to have (można odłożyć):

- 🟢 Admin endpoints
- 🟢 Security polish

---

## 📊 Postęp ogólny

- **Ukończone:** ~65% (+13% od ostatniej aktualizacji)
- **W trakcie:** ~5% (AI Categorization Service - częściowo)
- **Do zrobienia:** ~30%

**Ostatnie osiągnięcia:**

- ✅ Receipt Processing Pipeline - **PEŁNA IMPLEMENTACJA UKOŃCZONA**
  - ✅ `BillsProcessorService` - pełny orchestrator przetwarzania paragonów
  - ✅ Integracja z OCR Service (ekstrakcja danych z paragonów)
  - ✅ Tworzenie BillItems z walidacją Pydantic
  - ✅ Aktualizacja statusu Bill (PENDING → PROCESSING → COMPLETED/ERROR)
  - ✅ Obsługa błędów z zapisem error_message
  - ✅ Factory function dla Dependency Injection
  - ✅ Pełna integracja z Telegram Bot (`handle_receipt_image()`)
- ✅ Telegram Bot - pełna integracja z Receipt Processing Pipeline
  - ✅ Automatyczne przetwarzanie paragonów po uploadzie
  - ✅ Potwierdzenie przetworzenia z informacją o liczbie pozycji i kwocie
  - ✅ Obsługa błędów z komunikatem dla użytkownika
- ✅ Receipt Processing Pipeline - Krok 1: `StorageService.download_file()` - pobieranie plików z Supabase Storage
- ✅ Receipt Processing Pipeline - Krok 2: `ShopService.get_or_create_by_name()` - tworzenie/znajdowanie sklepów (z refaktoryzacją - wspólna metoda `_find_by_name_and_address()`)
- ✅ OCR Service (LLM-based) - pełna implementacja z Gemini API
  - Ekstrakcja danych z paragonów (items, total, date, shop_name)
  - Walidacja plików, error handling, retry logic
  - Endpoint `POST /api/v1/ocr/extract` z rate limiting
  - Podstawowa kategoryzacja produktów (category_suggestion)
- ✅ User isolation w Bills - wszystkie endpointy zabezpieczone (GET/POST/PATCH/DELETE)
- ✅ `BillAccessDeniedError` - błąd domenowy z globalnym handlerem (HTTP 403)
- ✅ Filtrowanie na poziomie SQL (`WHERE user_id = ?`) dla `GET /bills`
- ✅ Sprawdzanie ownership przed każdą operacją modyfikującą
- ✅ Storage Service zintegrowany z Supabase Storage

**Następne kroki (priorytet):**

1. 🟡 AI Categorization Service (rozbudowa - normalizacja, Product Index mapping) - **WAŻNE dla pełnego MVP**
2. 🟡 Reports module (daily/weekly/monthly) - **WAŻNE dla pełnego MVP**
3. 🟡 Verification workflow improvements - **WAŻNE dla pełnego MVP**

**Uwaga:** OCR Service został zaimplementowany z użyciem Gemini API (podobne rozwiązanie LLM-based jak planowane OpenAI Vision API). Pełny OCR z PaddlePaddle zostanie zaimplementowany po MVP jako ulepszenie.

**Uwaga:** File upload dla POST /bills nie jest wymagany - wszystkie zdjęcia paragonów są przesyłane przez Telegram Bot (zaimplementowane w 3.4).
