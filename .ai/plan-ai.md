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
                  │ Zwróć index_id│      │ Step 3: AI        │
                  │ z fuzzy match │      │ Categorization   │
                  │ + zapisz alias│      │ (Gemini API)     │
                  └───────────────┘      └──────────────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                            KATEGORIA ZNALEZIONA      BRAK KATEGORII
                            (confidence >= 0.8)       (confidence < 0.8)
                                    │                       │
                                    ↓                       ↓
                            ┌───────────────┐      ┌──────────────┐
                            │ Zwróć category│      │ Fallback do  │
                            │ z AI          │      │ "Inne"       │
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

#### Step 3: AI Categorization (Gemini API) [MVP]

**Priorytet:** Wysoki (część MVP).
**Status:** Implementacja w MVP z użyciem Gemini API.

**Strategia:**

Jeśli ani alias, ani fuzzy search nie zwróciły produktu, używamy Gemini API do zaproponowania kategorii na podstawie:

- Nazwy produktu (cleaned_text)
- Sugestii kategorii z OCR (category_suggestion)
- Kontekstu sklepu (shop_name)
- Listy dostępnych kategorii z bazy danych

**Implementacja:**

````python
async def _ai_categorize_product(
    self,
    cleaned_text: str,
    category_suggestion: Optional[str] = None,
    shop_name: Optional[str] = None,
    available_categories: List[Category] = None
) -> Optional[int]:
    """
    Używa Gemini API do zaproponowania kategorii dla nieznanego produktu.

    KRYTYCZNE: Ta metoda NIE może być wywołana wewnątrz transakcji DB!
    - Wywołania zewnętrznych API (Gemini) mogą trwać sekundy
    - Trzymanie otwartej transakcji DB blokuje połączenie i może spowodować deadlock
    - Wywołaj TĘ METODĘ PRZED otwarciem transakcji session.begin()

    Most Koncepcyjny (PHP -> Python):
    - W Symfony/Laravel używalibyście HTTP Client (Guzzle, Symfony HttpClient) do wywołań API.
    - W Pythonie używamy google.generativeai (oficjalna biblioteka Google) z async support.
    - Podobnie jak w OCRService, używamy retry pattern (tenacity) dla odporności na błędy.

    Uwaga: AICategorizationService musi mieć zainicjalizowany self.gemini_model
    (podobnie jak OCRService ma self.model). Inicjalizacja w __init__:

    ```python
    def __init__(self, session, product_index_service, alias_service, category_service):
        # ... istniejące zależności ...
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
    ```

    Input:
    - cleaned_text: "Mleko 3.2%" (wyczyszczony tekst produktu)
    - category_suggestion: "Nabiał" (sugestia z OCR/LLM)
    - shop_name: "Biedronka" (kontekst sklepu)
    - available_categories: Lista wszystkich kategorii z DB (do wyboru przez AI)

    Output:
    - category_id jeśli AI znalazło dopasowanie do istniejącej kategorii (confidence > threshold)
    - None jeśli AI nie jest pewne (wtedy użyj fallback)

    Proces:
    1. Przygotuj prompt z kontekstem (nazwa produktu, sugestia kategorii, shop, lista kategorii)
    2. Wywołaj Gemini API z structured output (JSON schema)
    3. Waliduj odpowiedź (czy zaproponowana kategoria istnieje w DB)
    4. Sprawdź confidence score (threshold: 0.8)
    5. Zwróć category_id lub None
    """
    if not available_categories:
        return None

    # Przygotowanie promptu
    categories_list = "\n".join([f"- {cat.name}" for cat in available_categories])

    prompt = f"""
    Jesteś ekspertem w kategoryzacji produktów.

    Produkt: {cleaned_text}
    Sugerowana kategoria (z OCR): {category_suggestion or "brak"}
    Sklep: {shop_name or "nieznany"}

    Dostępne kategorie:
    {categories_list}

    Zadanie:
    1. Wybierz NAJLEPSZĄ kategorię z listy dostępnych kategorii dla tego produktu.
    2. Jeśli żadna kategoria nie pasuje idealnie, zwróć null (nie wymyślaj nowych kategorii).
    3. Oceń swoją pewność (confidence) w przedziale 0.0-1.0.

    Zwróć odpowiedź w formacie JSON:
    {{
        "category_name": "Nazwa kategorii z listy lub null",
        "confidence": 0.95,
        "reasoning": "Krótkie uzasadnienie wyboru"
    }}
    """

    try:
        # Wywołanie Gemini API (podobnie jak w OCRService)
        response = await self.gemini_model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.3,  # Niższa temperatura = bardziej deterministyczne odpowiedzi
            )
        )

        if not response.text:
            logger.warning("Gemini zwróciło pustą odpowiedź dla kategoryzacji")
            return None

        # Parsowanie JSON response
        parsed_data = json.loads(response.text)
        category_name = parsed_data.get("category_name")
        confidence = parsed_data.get("confidence", 0.0)

        # Walidacja confidence threshold
        if confidence < 0.8:
            logger.info(f"AI confidence za niska ({confidence}) dla produktu: {cleaned_text}")
            return None

        # Znajdź kategorię w dostępnych kategoriach (case-insensitive)
        for cat in available_categories:
            if cat.name.lower() == category_name.lower():
                logger.info(f"AI zaproponowało kategorię: {category_name} (confidence: {confidence})")
                return cat.id

        # Kategoria nie znaleziona w liście (AI zaproponowało coś spoza listy)
        logger.warning(f"AI zaproponowało nieistniejącą kategorię: {category_name}")
        return None

    except json.JSONDecodeError as e:
        logger.error(f"Nieprawidłowa odpowiedź JSON z Gemini: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Błąd wywołania Gemini API: {str(e)}", exc_info=True)
        return None  # Fallback do kategorii "Inne"
````

**Fallback do kategorii "Inne":**

Jeśli AI nie zwróciło pewnego wyniku (confidence < 0.8) lub wystąpił błąd, używamy kategorii fallback:

```python
# Już zaimplementowane w CategoryService
fallback_category = await category_service.get_fallback_category()
# Zwraca kategorię "Inne" (lub tworzy ją jeśli nie istnieje)
```

**Uwagi implementacyjne:**

- **Transakcyjność:** AI Categorization MUSI być wywołana PRZED `session.begin()`, gdyż wywołania API mogą trwać sekundy i blokować połączenie DB.
- **Retry Pattern:** Użyj tenacity (jak w OCRService) dla automatycznego retry przy błędach sieciowych.
- **Confidence Threshold:** AI zwraca wynik tylko jeśli `confidence >= 0.8`, w przeciwnym razie fallback.
- **Rate Limiting:** Uwzględnij limity API Gemini (requests per minute) - rozważ queue/batching w Post-MVP.
- **Caching:** W Post-MVP rozważ cache dla częstych zapytań AI (np. Redis) - "Mleko" zawsze będzie "Nabiał".

**Integracja w normalize_item():**

```python
# W normalize_item() - zaktualizowana implementacja
# Uwaga: Metoda normalize_item() musi przyjmować shop_name jako parametr

async def normalize_item(
    self,
    ocr_item: OCRItem,
    shop_id: Optional[int] = None,
    shop_name: Optional[str] = None,  # NOWY PARAMETR dla AI Categorization
    user_id: Optional[int] = None,
    save_alias: bool = True
) -> NormalizedItem:
    # ... (Step 0, 1, 2 jak wcześniej) ...

    if not product_from_fuzzy:
        # Step 3: AI Categorization (Gemini API)
        available_categories = await self.category_service.get_all_categories()
        ai_category_id = await self._ai_categorize_product(
            cleaned_text=cleaned_text,
            category_suggestion=ocr_item.category_suggestion,
            shop_name=shop_name,  # Kontekst sklepu dla AI
            available_categories=available_categories
        )

        if ai_category_id:
            return NormalizedItem(
                original_text=ocr_item.name,
                normalized_name=None,  # Produkt nieznany, tylko kategoria
                quantity=ocr_item.quantity,
                unit_price=ocr_item.unit_price or Decimal("0.0"),
                total_price=ocr_item.total_price,
                category_id=ai_category_id,
                product_index_id=None,
                confidence_score=ocr_item.confidence_score * 0.7,  # AI match penalty
                is_confident=True
            )

        # Fallback: produkt nieznany systemowi (AI nie znalazło kategorii)
        fallback_category = await self.category_service.get_fallback_category()
        return NormalizedItem(
            original_text=ocr_item.name,
            normalized_name=None,
            quantity=ocr_item.quantity,
            unit_price=ocr_item.unit_price or Decimal("0.0"),
            total_price=ocr_item.total_price,
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

    # 2. AI Categorization & Normalization (poza transakcją zapisu BillItems)
    #    KRYTYCZNE: Wywołania Gemini API (w Step 3) muszą być PRZED session.begin()
    #    Serwis AI może używać własnych krótkich transakcji do odczytu (read-only),
    #    ale nie powinien blokować połączenia czekając na Gemini.
    normalized_items = await self._normalize_items(
        ocr_data.items,
        shop_id=shop_id,
        shop_name=ocr_data.shop_name,  # Kontekst dla AI Categorization
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
    # Już zaimplementowane

async def get_all_categories(self) -> List[Category]:
    """
    Zwraca listę wszystkich kategorii z bazy danych.
    Używane przez AI Categorization do wyboru kategorii przez Gemini API.

    Returns:
        List[Category]: Lista wszystkich kategorii (posortowana alfabetycznie)
    """
    stmt = select(Category).order_by(Category.name)
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

---

## 7. Strategie wyszukiwania i Konfiguracja

### 7.1. Parametry [MVP]

```python
# W config.py (już zaimplementowane)
AI_SIMILARITY_THRESHOLD: float = 0.75  # Threshold dla fuzzy search (zwiększony z 0.6)
AI_MIN_WORD_LENGTH_STRICT: int = 5     # Dla słów krótszych niż 5, wymagany wyższy threshold
AI_STRICT_THRESHOLD: float = 0.9       # Threshold dla krótkich słów
AI_FALLBACK_CATEGORY_NAME: str = "Inne"  # Nazwa kategorii fallback

# Parametry dla AI Categorization (Gemini API)
AI_CATEGORIZATION_CONFIDENCE_THRESHOLD: float = 0.8  # Minimalna pewność AI (0.0-1.0)
AI_CATEGORIZATION_TEMPERATURE: float = 0.3  # Temperatura dla Gemini (niższa = bardziej deterministyczne)
GEMINI_MODEL: str = "gemini-2.5-flash"  # Model Gemini (już w config)
GEMINI_TIMEOUT: int = 30  # Timeout w sekundach (już w config)
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

### Krok 5: AI Categorization (Gemini API) [MVP]

- [ ] Dodać metodę `_get_all_categories()` do CategoryService (pobranie listy kategorii)
- [ ] Zaimplementować `_ai_categorize_product()` w AICategorizationService
  - Przygotowanie promptu z kontekstem (produkt, sugestia, sklep, lista kategorii)
  - Wywołanie Gemini API z structured output (JSON)
  - Walidacja odpowiedzi (confidence threshold, istnienie kategorii)
  - Retry pattern (tenacity) dla odporności na błędy
- [ ] Zintegrować AI Categorization w `normalize_item()` (Step 3)
- [ ] Dodać fallback do kategorii "Inne" jeśli AI nie zwróciło wyniku
- [ ] `CategoryService.get_fallback_category()` (już zaimplementowane)

### Krok 6: Refaktoryzacja Processing Pipeline [MVP]

- [ ] Zmiana `_create_bill_items` na `List[NormalizedItem]`
- [ ] Przeniesienie logiki wyliczania cen do mappera/AI serwisu
- [ ] Zarządzanie transakcjami (AI przed `session.begin()`)

---
