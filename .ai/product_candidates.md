# Plan implementacji modułu Product Candidates i Uczenia się
**Data aktualizacji:** 2025-12-12
**Status:** W trakcie implementacji
**Priorytet:** Wysoki (kluczowe dla budowania Product Index)

---

## 1. Cel modułu

Celem tego planu jest zaimplementowanie mechanizmu, który pozwoli użytkownikom na wspólne budowanie "złotego standardu" (`ProductIndex`) dla produktów, bazując na weryfikacji pozycji paragonów (`BillItem`). System będzie grupował edytowane przez użytkowników nazwy produktów, zliczał potwierdzenia, a po przekroczeniu konfigurowalnego progu, automatycznie tworzył nowe wpisy w `ProductIndex`.

---

## 2. Założenia i istniejący stan

*   Model `BillItem` został rozszerzony o kolumnę `category_id` (FK do `categories`).
*   Moduł `backend/src/product_candidates` (modele, schematy, serwisy, być może trasy API) już istnieje i jest przygotowany.
*   Tabela `product_candidates` posiada kolumny: `id`, `representative_name`, `user_confirmations`, `category_id`, `product_index_id`, `status`, `created_at`, `updated_at`.
*   Tabela `product_candidates` posiada indeks `idx_product_candidates_name_trgm` i `idx_product_candidates_status`.
*   Konfigurowalne parametry:
    *   `PRODUCT_INDEX_ACCEPTANCE_THRESHOLD: int = 10` (liczba wymaganych potwierdzeń)
    *   `FUZZY_MATCH_GROUPING_THRESHOLD: float = 0.85` (próg podobieństwa dla grupowania nazw w `product_candidates`)

---

## 3. Zaktualizowane diagramy

### 3.1. Architektura modułu (z uwzględnieniem `product_candidates`)

┌─────────────────────────────────────────────────────────────┐
│ Bills Processing Pipeline │
│ │
│ OCR Service → Pre-processing → AI Categorization → BillItems│
│ ↓ ↓ ↓ ↓ │
│ OCRItem CleanedText NormalizedProduct BillItem │
│ (raw text) (no noise) (index_id) (DB row) │
└─────────────────────────────────────────────────────────────┘
│
↓
┌──────────────────┐
│ Product Index │
│ (słownik) │
└──────────────────┘
│
↓
┌──────────────────┐
│ Product Aliases │
│ (uczenie się) │
└──────────────────┘
│
↓
┌──────────────────┐
│ Product Candidates│ <-- NOWY ELEMENT
│ (poczekalnia) │
└──────────────────┘


### 3.2. Workflow weryfikacji i tworzenia ProductIndex

┌──────────────────────────────────────────────────────────────────┐
│ Input: Weryfikacja BillItem przez użytkownika │
│ - bill_item_id, user_id │
│ - edited_original_text (zaktualizowane BillItem.original_text) │
│ - edited_category_id (zaktualizowane BillItem.category_id) │
└──────────────────────────────────────────────────────────────────┘
│
↓
┌───────────────────────────────────────────────┐
│ Step 1: Aktualizacja BillItem │
│ - Ustaw BillItem.original_text = edited_original_text │
│ - Ustaw BillItem.category_id = edited_category_id │
│ - Ustaw BillItem.is_verified = True │
│ - Ustaw BillItem.verification_source = 'user' │
└───────────────────────────────────────────────┘
│
↓
┌───────────────────────────────────────────────┐
│ Step 2: Sprawdź istniejący ProductIndex │
│ - Wykonaj fuzzy search w product_indexes (AI_SIMILARITY_THRESHOLD)│
└───────────────────────────────────────────────┘
│
┌───────────────┴───────────────┐
│ │
ZNALEZIONO (ProductIndex) NIE ZNALEZIONO
│ │
↓ ↓
┌─────────────────────┐ ┌───────────────────────────────────────────────┐
│ Zaktualizuj BillItem.index_id │ Step 3: Zarządzanie Product Candidate │
│ Utwórz/zaktualizuj alias │ - Normalizuj edited_original_text │
│ ZAKOŃCZ │ - Znajdź lub utwórz ProductCandidate │
│ │ (fuzzy search w product_candidates, │
│ │ FUZZY_MATCH_GROUPING_THRESHOLD) │
└─────────────────────┘ └───────────────────────────────────────────────┘
│
↓
┌───────────────────────────────────────────────┐
│ Step 4: Zwiększ licznik potwierdzeń │
│ - Zwiększ product_candidate.user_confirmations │
│ - Zapisz BillItem.id do listy powiązanych BillItemów │
│ (jeśli taka lista będzie utrzymywana, np. JSONB w product_candidates, │
│ lub dynamicznie odpytujemy BillItems) │
└───────────────────────────────────────────────┘
│
↓
┌───────────────────────────────────────────────┐
│ Step 5: Sprawdź próg akceptacji │
│ - Czy product_candidate.user_confirmations >= PRODUCT_INDEX_ACCEPTANCE_THRESHOLD? │
└───────────────────────────────────────────────┘
│
┌─────────────┴─────────────┐
│ │
TAK (≥THRESHOLD) NIE (<THRESHOLD)
│ │
↓ ↓
┌─────────────────────────────────┐ ┌──────────────────┐
│ Step 6: Utwórz ProductIndex │ │ Czekaj na więcej │
│ - Wyznacz nazwę (najczęściej występująca oryginalna nazwa z powiązanych BillItems) │
│ - Wyznacz kategorię (najczęściej występująca kategoria z powiązanych BillItems) │
│ - Utwórz nowy ProductIndex (lub użyj istniejącego jeśli duplikat) │
└─────────────────────────────────┘ └──────────────────┘
│
↓
┌─────────────────────────────────┐
│ Step 7: Zaktualizuj BillItems │
│ - Ustaw BillItem.index_id dla wszystkich powiązanych BillItems │
└─────────────────────────────────┘
│
↓
┌─────────────────────────────────┐
│ Step 8: Utwórz Aliacy │
│ - Utwórz aliasy dla wszystkich unikalnych original_text powiązanych BillItems │
└─────────────────────────────────┘
│
↓
┌─────────────────────────────────┐
│ Step 9: Zaktualizuj Product Candidate │
│ - Ustaw product_candidate.status = 'approved' │
│ - Ustaw product_candidate.product_index_id = ProductIndex.id │
└─────────────────────────────────┘

---

## 4. Zadania implementacyjne (dla programistów)

### 4.1. Konfiguracja

*   **Zadanie:** Dodać `PRODUCT_INDEX_ACCEPTANCE_THRESHOLD` i `FUZZY_MATCH_GROUPING_THRESHOLD` do `config.py`.

### 4.2. Rozszerzenia modelu `BillItem` (Ukończone)

*   **Status:** Ukończone. `BillItem` posiada kolumnę `category_id`.

### 4.3. Moduł `product_candidates` (Ukończone)

*   **Status:** Ukończone. Model, schematy, serwisy są przygotowane.

### 4.4. `AICategorizationService` lub nowy `ProductLearningService` (Główna logika)

*   **Zadanie:** Utworzyć lub rozszerzyć serwis (np. `ProductLearningService`) odpowiedzialny za całą logikę weryfikacji i zarządzania kandydatami.

#### 4.4.1. Metoda `handle_user_bill_item_verification`

*   **Zadanie:** Zaimplementować metodę `handle_user_bill_item_verification` (zgodnie z diagramem i kodem z poprzedniej komunikacji).
*   **Odpowiedzialność:**
    *   Aktualizacja `BillItem` (`original_text`, `category_id`, `is_verified`, `verification_source`).
    *   Fuzzy search w `product_indexes`.
    *   Zarządzanie `product_candidates`: wyszukiwanie, tworzenie, aktualizacja liczników.
    *   Wyzwalanie tworzenia `ProductIndex`.

#### 4.4.2. Metoda `_find_or_create_product_candidate`

*   **Zadanie:** Zaimplementować metodę `_find_or_create_product_candidate`.
*   **Odpowiedzialność:**
    *   Normalizacja `edited_original_text` do `normalized_grouped_name`.
    *   Fuzzy search w `product_candidates` na `representative_name`.
    *   Tworzenie nowego `ProductCandidate` jeśli nie znaleziono pasującego.
    *   Zwiększanie `product_candidate.user_confirmations`.
    *   Aktualizacja `product_candidate.category_id` (np. na podstawie ostatniej zaakceptowanej kategorii lub pierwszej).

#### 4.4.3. Metoda `_create_product_index_from_candidate`

*   **Zadanie:** Zaimplementować metodę `_create_product_index_from_candidate`.
*   **Odpowiedzialność:**
    *   **Agregacja danych:**
        *   **KRYTYCZNE:** Bezpośrednie odpytywanie `BillItems` w celu znalezienia *wszystkich* zweryfikowanych `BillItems` powiązanych z danym `ProductCandidate` (przez fuzzy match na `original_text` i `category_id`).
        *   Wyznaczenie **najczęściej występującej `original_text`** spośród tych `BillItems` jako `ProductIndex.name`.
        *   Wyznaczenie **najczęściej występującej `category_id`** spośród tych `BillItems` jako `ProductIndex.category_id`.
        *   **SQL (do zaimplementowania w `BillItemService`):**
            -- Przykład SQL do pobrania najczęściej występującej nazwy i kategorii dla kandydata
            SELECT 
                bi.original_text, 
                bi.category_id, 
                COUNT(*) as count
            FROM bill_items bi
            WHERE bi.is_verified = TRUE 
              AND bi.verification_source = 'user'
              AND bi.index_id IS NULL -- Tylko BillItems, które jeszcze nie mają ProductIndex
              AND similarity(LOWER(bi.original_text), LOWER(:candidate_representative_name)) >= :fuzzy_threshold
              -- Opcjonalnie: AND bi.category_id = :candidate_category_id -- Jeśli chcemy bardzo ścisłego grupowania
            GROUP BY bi.original_text, bi.category_id
            ORDER BY count DESC
            LIMIT 1;
                *   Tworzenie nowego `ProductIndex` (lub pobranie istniejącego, jeśli nazwa już istnieje w słowniku).
    *   Utworzenie aliasów w `product_index_aliases` dla *wszystkich unikalnych `original_text`* znalezionych w zgrupowanych `BillItems`.

#### 4.4.4. Metoda `_update_bill_items_with_new_product_index`

*   **Zadanie:** Zaimplementować metodę `_update_bill_items_with_new_product_index`.
*   **Odpowiedzialność:**
    *   **KRYTYCZNE:** Znalezienie *wszystkich* `BillItems`, które fuzzy matchują zatwierdzonego `ProductCandidate` (i nie mają jeszcze `index_id`).
    *   Zaktualizowanie ich `BillItem.index_id` na `new_product_index_id`.
    *   **SQL (do zaimplementowania w `BillItemService`):**
        -- Przykład SQL do pobrania BillItems do aktualizacji
        SELECT id, original_text, bill_id, user_id, shop_id -- Dodaj potrzebne pola do aliasów
        FROM bill_items
        WHERE is_verified = TRUE 
          AND verification_source = 'user' 
          AND index_id IS NULL
          AND similarity(LOWER(original_text), LOWER(:candidate_representative_name)) >= :fuzzy_threshold
          -- Opcjonalnie: AND category_id = :candidate_category_id
        ;
            *   Tworzenie aliasów w `product_index_aliases` dla każdego zaktualizowanego `BillItem`.

#### 4.4.5. Metoda `_preprocess_text_for_grouping`

*   **Zadanie:** Zaimplementować metodę `_preprocess_text_for_grouping` (jak w kodzie z poprzedniej komunikacji).
*   **Odpowiedzialność:** Czyszczenie i standaryzacja tekstu dla potrzeb grupowania.

### 4.5. `BillItemService`

*   **Zadanie:** Dodać metody do `BillItemService` do:
    *   `update(bill_item_id, update_data, user_id)`: Metoda do aktualizacji `BillItem`, sprawdzająca uprawnienia `user_id`.
    *   `find_unindexed_verified_items_for_candidate(candidate_representative_name, candidate_category_id, fuzzy_threshold)`: Nowa metoda do pobierania `BillItems` na podstawie fuzzy match do kandydata (jak w SQL powyżej).
    *   `bulk_update_index_id(bill_item_ids: List[int], new_product_index_id: int)`: Metoda do masowej aktualizacji `index_id` dla listy `BillItem.id`.

### 4.6. `ProductIndexService`

*   **Zadanie:** Upewnić się, że `fuzzy_search` jest zaimplementowany poprawnie.
*   **Zadanie:** Zaimplementować `create_or_get_existing(product_index_create_data)`: Metoda, która tworzy nowy `ProductIndex` lub zwraca istniejący, jeśli nazwa już istnieje (case-insensitive).

### 4.7. `ProductIndexAliasService`

*   **Zadanie:** Upewnić się, że `upsert_alias` jest zaimplementowany poprawnie (zgodnie z sekcją 5.2 planu `.ai/plan-ai.md`).

---

## 5. Testowanie

*   **Testy jednostkowe:** Dla każdej nowej metody w `ProductLearningService` i zmienionych metod w innych serwisach.
*   **Testy integracyjne:** Cały przepływ weryfikacji użytkownika, grupowania, osiągania progu i tworzenia `ProductIndex`.
*   **Testy wydajnościowe:** Fuzzy matching na dużych zbiorach danych (`product_indexes`, `product_candidates`, `bill_items`).

---

## 6. Ulepszenia Post-MVP

*   **Mechanizm głosowania na kategorię:** Bardziej zaawansowana logika wyboru `category_id` dla `ProductIndex` (np. ważone głosy).
*   **Warianty nazwy:** Utrzymywanie listy wariantów `original_text` dla każdego `ProductIndex`, aby poprawić fuzzy matching.
*   **Administracyjny panel:** Możliwość ręcznej weryfikacji/akceptacji/odrzucania kandydatów przez administratora.
*   **Rozwiązywanie konfliktów:** Logika do radzenia sobie z kandydatami, którzy osiągnęli próg, ale ich `representative_name` jest bardzo zbliżona do już istniejącego `ProductIndex`.

---

Ten plan powinien dostarczyć programistom jasny obraz zadań i odpowiedzialności, a także wskazać kluczowe punkty decyzyjne i potencjalne wyzwania.
