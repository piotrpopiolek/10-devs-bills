# Plan implementacji modułu AI Categorization Service

**Data aktualizacji:** 2025-12-11
**Status:** Plan zaktualizowany (w trakcie implementacji)
**Priorytet:** Wysoki (blokujące MVP)

---

## 1. Przegląd modułu

### 1.1. Cel modułu

Moduł AI Categorization Service odpowiada za:

- **Pre-processing tekstu OCR** - czyszczenie szumu i normalizacja formatu [MVP]
- **Normalizację nazw produktów** - mapowanie wariantów OCR na standardowe nazwy z Product Index
- **Kategoryzację produktów** - przypisanie produktów do predefiniowanych kategorii
- **Uczenie się z weryfikacji** - zapisywanie aliasów produktów na podstawie weryfikacji użytkownika
- **Fallback do kategorii "Inne"** - obsługa produktów nieznanych systemowi

### 1.2. Wymagania z PRD

Zgodnie z `.ai/prd.md`:

- **F-03: Kategoryzacja i Normalizacja AI**
  - Wykorzystanie modeli AI (Gemini) do przypisywania pozycji do kategorii (Uwaga: wywołanie API poza transakcją DB)
  - Normalizacja nazwy produktu w oparciu o Product Index
- **F-04: Weryfikacja przez użytkownika**

  - Prezentacja niepewnych pozycji w Telegramie
  - Nauka systemu na podstawie weryfikacji (product aliases)

- **F-05: Walidacja sumy**

  - Sprawdzenie poprawności odczytu (OCR Service)

- **F-10: Zarządzanie kategoriami (Admin)**
  - Predefiniowane kategorie, fallback do "Inne"

### 1.3. Architektura modułu

```
┌─────────────────────────────────────────────────────────────┐
│                    Bills Processing Pipeline               │
│                                                             │
│  OCR Service → Pre-processing → AI Categorization → BillItems│
│      ↓              ↓                 ↓               ↓      │
│  OCRItem       CleanedText      NormalizedProduct   BillItem │
│  (raw text)    (no noise)       (index_id)         (DB row)  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │  Product Index   │
                    │  (słownik)       │
                    └──────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │ Product Aliases  │
                    │  (uczenie się)   │
                    └──────────────────┘
```

---

## 2. Struktura modułu

### 2.1. Pliki modułu

```
backend/src/ai/
├── __init__.py
├── service.py              # Główny serwis AI Categorization
├── schemas.py              # Pydantic schemas (NormalizedItem, etc.)
├── exceptions.py           # Wyjątki specyficzne dla AI
├── dependencies.py         # Dependency Injection
└── strategies.py           # Strategie wyszukiwania (fuzzy, exact, alias)
```

### 2.2. Zależności

Moduł wymaga:

- `ProductIndexService` - wyszukiwanie produktów
- `ProductIndexAliasService` - zarządzanie aliasami (z obsługą UPSERT)
- `CategoryService` - wyszukiwanie kategorii (metoda `get_fallback_category`)
- `AsyncSession` - dostęp do bazy danych
- `Gemini API` - dla zaawansowanej kategoryzacji (wywoływane ostrożnie, poza transakcją)

---

## 3. Workflow normalizacji produktu

### 3.1. Główny flow normalizacji

```
┌─────────────────────────────────────────────────────────────┐
│  Input: OCRItem                                             │
│  - original_text: "Mleko 3.2% 1L"                           │
│  - category_suggestion: "Nabiał"                           │
│  - confidence_score: 0.95                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
        ┌─────────────────────────────────┐
        │  Step 0: Pre-processing [MVP]   │
        │  - whitespace normalization     │
        │  - symbol removal               │
        │  - decimal normalization (, -> .)│
        └─────────────────────────────────┘
                          │
                          ↓
        ┌─────────────────────────────────┐
        │  Step 1: Sprawdź aliasy         │
        │  (ProductIndexAlias)            │
        └─────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
         ZNALEZIONO                  NIE ZNALEZIONO
            │                           │
            ↓                           ↓
    ┌───────────────┐         ┌──────────────────┐
    │ Zwróć index_id│         │ Step 2: Fuzzy    │
    │ z aliasu      │         │ Search w         │
    │               │         │ ProductIndex     │
    └───────────────┘         └──────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                      ZNALEZIONO              NIE ZNALEZIONO
                          │                       │
                          ↓                       ↓
                  ┌───────────────┐      ┌──────────────────┐
                  │ Zwróć index_id│      │ Step 3: AI       │
                  │ z fuzzy match │      │ Categorization   │
                  └───────────────┘      │                  |
                                         └──────────────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                            KATEGORIA ZNALEZIONA      BRAK KATEGORII
                                    │                       │
                                    ↓                       ↓
                            ┌───────────────┐      ┌──────────────┐
                            │ Zwróć category │      │ Fallback do  │
                            │               │      │ "Inne"       │
                            └───────────────┘      └──────────────┘
```

### 3.2. Szczegółowy algorytm normalizacji

#### Step 0: Pre-processing [MVP]

Przed szukaniem aliasu należy oczyścić tekst, aby zwiększyć szansę na trafienie.

```python
def _preprocess_text(raw_text: str) -> str:
    """
    Czyści tekst z szumu OCR.
    1. Whitespace normalization (usunięcie podwójnych spacji)
    2. Symbol removal (usunięcie dziwnych znaków na końcach, np. _, #)
    3. Decimal normalization (zamiana , na . w liczbach)
    """
```

#### Step 1: Wyszukiwanie w aliasach (ProductIndexAlias)

**Priorytet:** Najwyższy.
**Optymalizacja:** W MVP używamy 3 zapytań (User+Shop -> Shop -> Global).
**Uwaga:** Wymagany indeks funkcyjny `LOWER(raw_name)` [MVP].

Query SQL (koncepcyjne):

```sql
-- Używa indeksu na LOWER(raw_name)
SELECT pi.* FROM product_indexes pi
JOIN product_index_aliases pia ON pi.id = pia.index_id
WHERE LOWER(pia.raw_name) = LOWER(:cleaned_text)
  AND ... (logika priorytetów)
ORDER BY pia.confirmations_count DESC
LIMIT 1;
```

#### Step 2: Fuzzy Search w ProductIndex

**Priorytet:** Średni.
**Zmiana w MVP:** Zwiększony threshold do 0.75-0.8. Dynamiczny threshold dla krótkich słów.

```python
async def _fuzzy_search_product(
    raw_name: str,
    category_suggestion: Optional[str] = None,
    similarity_threshold: float = 0.75  # Zwiększone z 0.6 [MVP]
) -> Optional[ProductIndex]:
    """
    Wyszukuje produkt używając fuzzy search.
    Dla krótkich słów (<5 znaków) threshold powinien być wyższy (np. 0.9).
    """
```

#### Step 3: AI Categorization (opcjonalnie) i Fallback [MVP]

**Priorytet:** Niski (Post-MVP dla pełnej integracji AI).
**Status:** W MVP używamy tylko fallback do kategorii "Inne". Pełna integracja z Gemini API zaplanowana na Post-MVP.

**Strategia:**

Jeśli ani alias, ani fuzzy search nie zwróciły produktu, mamy dwie opcje:

1. **AI Categorization (Post-MVP):** Wywołanie API Gemini do zaproponowania kategorii na podstawie nazwy produktu i kontekstu (shop_name, category_suggestion z OCR).

```python
async def _ai_categorize_product(
    cleaned_text: str,
    category_suggestion: Optional[str] = None,
    shop_context: Optional[str] = None
) -> Optional[int]:
    """
    Używa Gemini API do zaproponowania kategorii dla nieznanego produktu.

    KRYTYCZNE: Ta metoda NIE może być wywołana wewnątrz transakcji DB!
    - Wywołania zewnętrznych API (Gemini) mogą trwać sekundy
    - Trzymanie otwartej transakcji DB blokuje połączenie i może spowodować deadlock
    - Wywołaj TĘ METODĘ PRZED otwarciem transakcji session.begin()

    Input:
    - cleaned_text: "Mleko 3.2%"
    - category_suggestion: "Nabiał" (z OCR)
    - shop_context: "Biedronka"

    Output:
    - category_id jeśli AI znalazło dopasowanie do istniejącej kategorii
    - None jeśli AI nie jest pewne (wtedy użyj fallback)

    Proces:
    1. Przygotuj prompt z kontekstem (nazwa produktu, sugestia kategorii, shop)
    2. Wywołaj Gemini API z listą dostępnych kategorii
    3. Waliduj odpowiedź (czy zaproponowana kategoria istnieje w DB)
    4. Zwróć category_id lub None
    """
    # Post-MVP: Implementacja wywołania Gemini API
    pass
```

2. **Fallback do kategorii "Inne" (MVP):** Jeśli AI nie jest dostępne lub nie zwróciło pewnego wyniku, używamy kategorii fallback.

```python
# Już zaimplementowane w CategoryService
fallback_category = await category_service.get_fallback_category()
# Zwraca kategorię "Inne" (lub tworzy ją jeśli nie istnieje)
```

**Uwagi implementacyjne:**

- **Transakcyjność:** AI Categorization MUSI być wywołana PRZED `session.begin()`, gdyż wywołania API mogą trwać długo i blokować połączenie DB.
- **Cache:** Rozważ cache dla częstych zapytań AI (np. Redis) w Post-MVP.
- **Confidence Threshold:** AI powinno zwrócić wynik tylko jeśli `confidence > 0.8`, w przeciwnym razie fallback.
- **Rate Limiting:** Uwzględnij limity API Gemini (requests per minute).

```python
# W normalize_item() - już zaimplementowane
if not product_from_fuzzy:
    fallback_category = await self.category_service.get_fallback_category()
    return NormalizedItem(
        ...,
        category_id=fallback_category.id,
        product_index_id=None,
        confidence_score=ocr_item.confidence_score * 0.5,
        is_confident=False
    )
```

## 4. Workflow uczenia się (Learning)

### 4.1. Zapis aliasu po weryfikacji użytkownika

Gdy użytkownik weryfikuje BillItem, system zapisuje alias.

### 4.2. Automatyczny zapis aliasu po normalizacji (UPSERT) [MVP]

Zamiast logiki "Check-then-Act" (SELECT potem INSERT), używamy UPSERT, aby zapewnić atomowość w środowisku asynchronicznym.

```sql
-- PostgreSQL UPSERT [MVP]
INSERT INTO product_index_aliases (raw_name, index_id, shop_id, user_id, confirmations_count)
VALUES (:raw_name, :index_id, :shop_id, :user_id, 1)
ON CONFLICT (lower(raw_name), index_id)
DO UPDATE SET
    confirmations_count = product_index_aliases.confirmations_count + 1,
    last_seen_at = NOW();
```

---

## 5. Integracja z Receipt Processing Pipeline

### 5.1. Miejsce w pipeline i Transakcyjność [MVP]

**Krytyczne:** Nie wywoływać zewnętrznych API (Gemini) wewnątrz otwartej transakcji DB.

```python
# backend/src/processing/service.py

async def process_receipt(self, bill_id: int) -> None:
    # 1. Pobranie obrazu i OCR (poza transakcją)
    ocr_data = await self._extract_receipt_data(...)

    # 2. AI Categorization & Normalization (poza transakcją zapisu BillItems, jeśli używa API)
    #    Serwis AI może używać własnych krótkich transakcji do odczytu (read-only),
    #    ale nie powinien blokować połączenia czekając na Gemini.
    normalized_items = await self._normalize_items(
        ocr_data.items,
        shop_id=shop_id,
        user_id=bill.user_id
    )

    # 3. Transakcja zapisu (szybka)
    async with self.session.begin():
         await self._create_bill_items(bill_id, normalized_items)
```

### 5.2. Refaktoryzacja `_create_bill_items` [MVP]

Metoda `_create_bill_items` musi przyjmować listę `NormalizedItem`. Logika biznesowa (wyliczanie cen, walidacja ujemnych cen) powinna zostać przeniesiona do mappera lub serwisu AI.

```python
async def _create_bill_items(self, bill_id: int, items: List[NormalizedItem]) -> None:
    """
    Przyjmuje już znormalizowane i przeliczone obiekty.
    Tylko mapuje na model DB i zapisuje.
    """
```

---

## 6. API i interfejsy

### 6.1. Zmiany w CategoryService [MVP]

```python
async def get_fallback_category(self) -> Category:
    """
    Zwraca kategorię domyślną (np. oznaczoną flagą is_default=True lub po nazwie z configu).
    Jeśli nie istnieje, tworzy ją bezpiecznie.
    """
```

---

## 7. Strategie wyszukiwania i Konfiguracja

### 7.1. Parametry [MVP]

```python
class AIConfig:
    SIMILARITY_THRESHOLD: float = 0.75  # Zwiększone z 0.6
    MIN_WORD_LENGTH_STRICT: int = 5     # Dla słów krótszych niż 5, wymagany wyższy threshold
    STRICT_THRESHOLD: float = 0.9
```

### 7.2. Indeksy Bazy Danych [MVP]

Należy upewnić się, że istnieje indeks funkcyjny dla aliasów:

```sql
CREATE INDEX IF NOT EXISTS idx_product_index_aliases_lower_raw_name
ON product_index_aliases (LOWER(raw_name));
```

---

## 8. Plany Rozwojowe (Post-MVP)

Poniższe elementy zostały przesunięte do fazy po MVP, zgodnie z sugestiami optymalizacyjnymi.

### 8.1. Optymalizacja wyszukiwania aliasów (Single Query) [Post-MVP]

Zastąpienie 3 zapytań (User+Shop, Shop, Global) jednym złożonym zapytaniem z `ORDER BY CASE WHEN ...`. Wymaga to zaawansowanego indeksowania (w tym NULL-i) i dokładnego przetestowania planu zapytania.

### 8.2. Obsługa Niejednoznaczności (Ambiguity) [Post-MVP]

Jeśli fuzzy search zwraca kilka wyników o bardzo zbliżonym score (np. różnica < 0.05), system nie powinien wybierać automatycznie, lecz oznaczyć pozycję do weryfikacji manualnej.

### 8.3. Caching (L1 Cache) [Post-MVP]

Wprowadzenie cache w pamięci (LRU) dla najpopularniejszych aliasów (np. "Mleko", "Chleb"), aby odciążyć bazę danych (zasada Pareto).

### 8.4. Vector Search (Embeddings) [Post-MVP]

Zastąpienie `pg_trgm` wyszukiwaniem wektorowym (`pgvector`) dla lepszego zrozumienia semantycznego i obsługi literówek.

---

## 9. Implementacja krok po kroku (Zaktualizowana)

### Krok 1: Struktura i Pre-processing [MVP]

- [ ] Utworzyć strukturę plików
- [ ] Zaimplementować `_preprocess_text` w `service.py`

### Krok 2: Schemas i Modele [MVP]

- [ ] `NormalizedItem` (z logiką cen i walidacji)

### Krok 3: Aliasy z UPSERT [MVP]

- [ ] Implementacja `_find_by_alias` (3 zapytania, z indeksem funkcyjnym)
- [ ] Implementacja zapisu aliasu z użyciem `ON CONFLICT`

### Krok 4: Fuzzy Search [MVP]

- [ ] Implementacja z nowym thresholdem (0.75) i logiką długości słowa

### Krok 5: Kategoryzacja i Fallback [MVP]

- [ ] `CategoryService.get_fallback_category()`
- [ ] Integracja z logiką AI (poza transakcją)

### Krok 6: Refaktoryzacja Processing Pipeline [MVP]

- [ ] Zmiana `_create_bill_items` na `List[NormalizedItem]`
- [ ] Przeniesienie logiki wyliczania cen do mappera/AI serwisu
- [ ] Zarządzanie transakcjami (AI przed `session.begin()`)

---
