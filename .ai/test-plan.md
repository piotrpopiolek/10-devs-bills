<analiza_projektu>

1.  **Kluczowe komponenty projektu wynikające z analizy kodu:**
    *   **Backend (FastAPI)**: Centralny punkt logiki biznesowej. Podzielony na moduły: `auth` (uwierzytelnianie), `bills` (zarządzanie paragonami), `bill_items` (pozycje na paragonie), `categories`, `shops`, `users`. Integruje się z Telegramem (`telegram`), AI (`openai`) oraz OCR (`paddleocr`).
    *   **Frontend (Astro + React)**: Warstwa prezentacji danych dla użytkownika (web app). Wykorzystuje komponenty React (`CategoriesTable`, `AppSidebar`) oraz statyczne strony Astro. Komunikuje się z backendem/Supabase.
    *   **Telegram Bot**: Główny interfejs wejściowy dla użytkownika (przesyłanie zdjęć paragonów). Zaimplementowany w backendzie przy użyciu `python-telegram-bot`.
    *   **Baza Danych & Storage (Supabase)**: Przechowywanie danych relacyjnych (PostgreSQL) oraz plików (zdjęcia paragonów).
    *   **AI & OCR Services**: Zewnętrzne/biblioteczne serwisy do przetwarzania obrazu (PaddleOCR) i kategoryzacji (OpenAI).

2.  **Specyfika stosu technologicznego i jego wpływ na strategię testowania:**
    *   **FastAPI & Python**: Umożliwia łatwe testowanie jednostkowe i integracyjne przy użyciu `pytest`. Asynchroniczność (`async`/`await`) wymaga odpowiednich narzędzi testowych (`pytest-asyncio`).
    *   **Astro & React**: Wymaga podejścia hybrydowego – testy komponentów React (np. Vitest/Jest + React Testing Library) oraz testy E2E dla całych stron Astro (Playwright/Cypress).
    *   **Supabase**: Testy integracyjne będą wymagały zarządzania stanem bazy danych (np. kontenery testowe lub dedykowana instancja testowa) oraz mockowania klienta Supabase w testach jednostkowych.
    *   **OCR & AI**: Są to komponenty niedeterministyczne i kosztowne/wolne. W testach automatycznych należy je **bezwzględnie mockować** (podstawiać gotowe odpowiedzi), a ich faktyczne działanie weryfikować w testach manualnych lub na małej próbce testów E2E typu "smoke test".
    *   **Telegram Bot**: Trudny do automatyzacji E2E. Testy powinny skupić się na warstwie obsługi zdarzeń (handlerach) poprzez mockowanie obiektu `Update` i `Context`.

3.  **Priorytety testowe bazujące na strukturze repozytorium:**
    *   **Priorytet 1 (Krytyczny)**: Ścieżka "Happy Path" przesyłania paragonu: Upload (Telegram) -> OCR -> Parsowanie -> Zapis do DB. Jeśli to nie działa, aplikacja jest bezużyteczna.
    *   **Priorytet 2 (Wysoki)**: Bezpieczeństwo i autoryzacja (Auth, RLS w Supabase, dostęp do API).
    *   **Priorytet 3 (Średni)**: Poprawność kategoryzacji produktów i zarządzanie słownikami (Categories/Shops).
    *   **Priorytet 4 (Niski)**: UI dashboardu i wizualizacje (można wyłapać manualnie).

4.  **Potencjalne obszary ryzyka wymagające szczególnej uwagi w testach:**
    *   **Błędy OCR**: Co się stanie, gdy OCR zwróci śmieciowe dane? Czy system się wywali, czy obsłuży błąd?
    *   **Limity API (OpenAI/Telegram)**: Obsługa błędów sieciowych i rate limitów.
    *   **Synchronizacja danych**: Spójność między tym co widzi bot, a tym co jest w bazie/aplikacji webowej.
    *   **Prywatność**: Upewnienie się, że użytkownik X nie widzi paragonów użytkownika Y (RLS i logika backendu).

</analiza_projektu>

<plan_testów>

# Plan Testów dla Projektu "Bills"

## 1. Wprowadzenie i cele testowania
Celem procesu testowania jest zapewnienie stabilności, bezpieczeństwa oraz poprawności funkcjonalnej aplikacji "Bills". Szczególny nacisk kładziony jest na automatyzację procesu przetwarzania paragonów (OCR + AI) oraz integrację z botem Telegram. Testy mają na celu wykrycie błędów regresyjnych przy rozwoju aplikacji oraz weryfikację odporności systemu na błędne dane wejściowe.

## 2. Zakres testów
*   **Backend (API & Services)**: Logika biznesowa, endpointy REST, integracja z usługami zewnętrznymi.
*   **Telegram Bot**: Obsługa komend i przesyłania plików.
*   **Frontend (Web App)**: Wyświetlanie danych, autoryzacja użytkownika.
*   **Baza Danych**: Poprawność schematów i migracji.
*   **Wyłączone z zakresu**: Testy wydajnościowe samego silnika PaddleOCR (zakładamy poprawność biblioteki), testy obciążeniowe infrastruktury Telegrama.

## 3. Typy testów do przeprowadzenia

### 3.1. Testy Jednostkowe (Unit Tests)
*   **Backend**: Testowanie poszczególnych funkcji serwisowych (`services.py`) i modeli Pydantic w izolacji. Mockowanie bazy danych i API zewnętrznych.
*   **Frontend**: Testowanie komponentów React (np. tabel, formularzy) pod kątem renderowania i logiki interakcji.

### 3.2. Testy Integracyjne (Integration Tests)
*   **API**: Testowanie endpointów FastAPI z wykorzystaniem testowej bazy danych (np. SQLite in-memory lub kontener PostgreSQL). Weryfikacja przepływu danych od requestu do bazy.
*   **Telegram Handlers**: Testowanie funkcji obsługujących wiadomości z zamockowanym obiektem `Context` telegrama, ale z prawdziwą (lub testową) logiką biznesową pod spodem.

### 3.3. Testy End-to-End (E2E)
*   Scenariusze przekrojowe realizowane na środowisku stagingowym, symulujące działania prawdziwego użytkownika (np. użycie klienta Telegrama do wysłania zdjęcia i weryfikacja wyniku w Web App).

## 4. Scenariusze testowe dla kluczowych funkcjonalności

### Scenariusz A: Przetwarzanie paragonu (Główny przepływ)
1.  Użytkownik wysyła zdjęcie paragonu do bota Telegram.
2.  System odbiera plik i zapisuje w Storage.
3.  Uruchamiany jest proces OCR (PaddlePaddle).
4.  Tekst z OCR jest przekazywany do LLM (OpenAI) celem ekstrakcji pozycji.
5.  Pozycje są zapisywane w bazie danych z przypisanymi kategoriami.
6.  Bot odsyła podsumowanie do użytkownika.
7.  **Oczekiwany rezultat**: Paragon widoczny w bazie danych, poprawne sumy, użytkownik otrzymuje potwierdzenie.

### Scenariusz B: Obsługa błędów OCR/AI
1.  Użytkownik wysyła niewyraźne zdjęcie lub zdjęcie niebędące paragonem.
2.  OCR zwraca pusty wynik lub AI nie rozpoznaje struktury paragonu.
3.  **Oczekiwany rezultat**: System nie ulega awarii, użytkownik otrzymuje stosowny komunikat błędu (np. "Nie udało się odczytać paragonu, spróbuj ponownie").

### Scenariusz C: Zarządzanie kategoriami (Frontend)
1.  Użytkownik loguje się do aplikacji webowej.
2.  Przechodzi do widoku kategorii.
3.  Edytuje nazwę istniejącej kategorii.
4.  **Oczekiwany rezultat**: Zmiana jest widoczna natychmiast, dane w bazie są zaktualizowane.

### Scenariusz D: Bezpieczeństwo danych (Auth)
1.  Użytkownik A próbuje pobrać szczegóły paragonu należącego do Użytkownika B poprzez API (znając ID).
2.  **Oczekiwany rezultat**: Odmowa dostępu (403 Forbidden / 404 Not Found).

## 5. Środowisko testowe
*   **DEV (Lokalne)**: Uruchamiane przez dewelopera. Baza danych lokalna lub dockerowa.
*   **CI/CD Pipeline**: Automatyczne uruchamianie testów przy każdym Pull Request.
*   **STAGING**: Środowisko wiernie odwzorowujące PROD, podłączone do testowej instancji Supabase i bota Telegram (testowego).

## 6. Narzędzia do testowania
*   **Backend Framework**: `pytest` (główny runner), `pytest-asyncio` (testy asynchroniczne), `pytest-mock` (mockowanie).
*   **Frontend**: `Vitest` (testy jednostkowe), `Playwright` (testy E2E).
*   **API Testing**: `Postman` lub `HTTP Client` w IDE do manualnych testów API.
*   **Mockowanie**: `unittest.mock` (Python).

## 7. Harmonogram testów
*   **Testy jednostkowe**: Pisane na bieżąco wraz z kodem (TDD lub równolegle). Wymagane zaliczenie 100% testów przed merge.
*   **Testy integracyjne**: Uruchamiane w pipeline CI.
*   **Testy E2E/Manualne**: Przeprowadzane przed wydaniem nowej wersji na środowisko produkcyjne (Release).

## 8. Kryteria akceptacji testów
*   Wszystkie testy automatyczne w CI muszą przechodzić (zielone).
*   Pokrycie kodu (Code Coverage) dla kluczowych modułów backendu (`services`, `routes`) > 80%.
*   Brak błędów krytycznych (Critical/High) zgłoszonych w fazie testów manualnych.

## 9. Role i odpowiedzialności
*   **Developer**: Pisanie testów jednostkowych i integracyjnych dla tworzonego kodu. Utrzymanie testów w aktualności.
*   **QA Engineer / Tech Lead**: Weryfikacja planu testów, tworzenie scenariuszy E2E, audyt jakości kodu testowego.

## 10. Procedury raportowania błędów
*   Błędy zgłaszane są w systemie śledzenia zadań (np. GitHub Issues / Jira).
*   Zgłoszenie musi zawierać: Kroki do reprodukcji, Oczekiwany rezultat, Rzeczywisty rezultat, Logi/Screenshoty.
*   Błędy krytyczne blokują wdrożenie na produkcję.

</plan_testów>