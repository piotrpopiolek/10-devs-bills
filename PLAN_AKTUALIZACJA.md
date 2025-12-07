# Plan kolejnych kroków — Bills MVP (Zaktualizowany)

**Data aktualizacji:** 2024-12-19  
**Status ogólny:** ~40% ukończone

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

- **Status:** Ukończone
- **Funkcjonalność:** Automatyczne przetwarzanie zdjęć paragonów wysłanych do bota
- **Zaimplementowane:**
  - ✅ `MessageHandler` dla photos i documents
  - ✅ Pobieranie pliku z Telegram API
  - ✅ Upload do Storage Service
  - ✅ Tworzenie rekordu Bill z statusem PENDING
  - ✅ Auto-rejestracja użytkownika przy pierwszym użyciu
- **Brakujące:**
  - 🔴 Integracja z OCR Service (TODO w linii 135)
  - 🔴 Potwierdzenie przetworzenia po zakończeniu OCR/AI
- **Pliki:** `backend/src/telegram/services.py` (handle_receipt_image)

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

### 5.1. OCR Service

- **Status:** Brak
- **Priorytet:** Wysoki
- **Zadania:**
  - Utworzyć `backend/src/ocr/service.py`
  - Integracja z PaddlePaddle-OCR
  - Dodać preprocessing obrazów
  - Dodać error handling dla nieczytelnych paragonów
  - Zwracać structured data (items, total, date)
- **Szacunek:** 8-10h

### 5.2. AI Categorization Service

- **Status:** Brak
- **Priorytet:** Wysoki
- **Zadania:**
  - Utworzyć `backend/src/ai/service.py`
  - Integracja z OpenAI API
  - Dodać prompt engineering dla kategoryzacji
  - Dodać normalizację nazw produktów
  - Mapowanie do Product Index (słownik produktów)
  - Fallback do kategorii "Inne"
- **Szacunek:** 10-12h

### 5.3. Receipt Processing Pipeline

- **Status:** Brak
- **Priorytet:** Wysoki
- **Zadania:**
  - Utworzyć `ReceiptProcessorService`
  - Zintegrować OCR → AI → Database
  - Dodać walidację sumy (items total vs receipt total)
  - Dodać background task (Dramatiq/Celery) dla async processing
  - Dodać status tracking (pending → processing → completed/error)
- **Szacunek:** 12-15h

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

- **Status:** Częściowo (obsługa zdjęć gotowa, brak integracji z OCR/AI)
- **Priorytet:** Średni
- **Zrobione:**
  - ✅ Obsługa zdjęć paragonów (MessageHandler dla photos/documents)
  - ✅ Upload do Storage i tworzenie Bill record
- **Brakujące funkcjonalności:**
  - 🔴 `send_receipt_confirmation(bill_id)` - potwierdzenie przetworzenia (po zakończeniu OCR/AI)
  - 🔴 `send_verification_request(bill_item_id)` - prośba o weryfikację (dla confidence < 0.8)
  - 🔴 `send_summary(user_id, period)` - podsumowanie wydatków (integracja z Reports)
  - 🔴 Integracja z Receipt Processing Pipeline (trigger OCR task)
- **Szacunek:** 4-5h (po zaimplementowaniu OCR/AI)

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

- 🔴 OCR Service
- 🔴 AI Categorization Service
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
- ✅ Telegram Bot - obsługa zdjęć (upload + Bill creation)
- ✅ Storage Service (Supabase + fallback)
- 🔴 OCR Service
- 🔴 AI Categorization
- 🔴 Receipt Processing Pipeline

### Ważne (dla pełnego MVP):

- 🟡 Reports
- 🟡 Telegram Bot Service (rozbudowa)
- 🟡 Verification workflow

### Nice to have (można odłożyć):

- 🟢 Admin endpoints
- 🟢 Security polish

---

## 📊 Postęp ogólny

- **Ukończone:** ~40% (+5% od ostatniej aktualizacji)
- **W trakcie:** ~5%
- **Do zrobienia:** ~55%

**Ostatnie osiągnięcia:**

- ✅ User isolation w Bills - wszystkie endpointy zabezpieczone (GET/POST/PATCH/DELETE)
- ✅ `BillAccessDeniedError` - błąd domenowy z globalnym handlerem (HTTP 403)
- ✅ Filtrowanie na poziomie SQL (`WHERE user_id = ?`) dla `GET /bills`
- ✅ Sprawdzanie ownership przed każdą operacją modyfikującą
- ✅ Storage Service zintegrowany z Supabase Storage
- ✅ Telegram Bot - pełna obsługa zdjęć paragonów (upload + tworzenie Bill)

**Następne kroki (priorytet):**

1. 🔴 OCR Service (początek integracji z PaddlePaddle) - **KRYTYCZNE dla MVP**
2. 🔴 AI Categorization Service (integracja z OpenAI)
3. 🔴 Receipt Processing Pipeline (integracja OCR → AI → Database)

**Uwaga:** File upload dla POST /bills nie jest wymagany - wszystkie zdjęcia paragonów są przesyłane przez Telegram Bot (zaimplementowane w 3.4).
