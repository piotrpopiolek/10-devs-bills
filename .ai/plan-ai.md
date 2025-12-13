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

**UWAGA:** Ten diagram pokazuje tylko proces normalizacji nazwy produktu. Kategoryzacja jest osobnym procesem (patrz sekcja 4).

```
┌─────────────────────────────────────────────────────────────┐
│  Input: OCRItem                                             │
│  - original_text: "Mleko 3.2% 1L"                           │
│  - category_suggestion: "Nabiał" (używane tylko jako      │
│                          opcjonalne filtrowanie)           │
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
        │  - User + Shop specific         │
        │  - Shop specific                │
        │  - Global                        │
        └─────────────────────────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
         ZNALEZIONO                  NIE ZNALEZIONO
            │                           │
            ↓                           ↓
    ┌───────────────┐         ┌──────────────────┐
    │ Zwróć         │         │ Step 2: Fuzzy    │
    │ ProductIndex  │         │ Search w         │
    │               │         │ ProductIndex     │
    │               │         │ (pg_trgm)       │
    └───────────────┘         └──────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                      ZNALEZIONO              NIE ZNALEZIONO
                      (similarity >= 0.6)     (similarity < 0.6)
                          │                       │
                          ↓                       ↓
                  ┌───────────────┐      ┌──────────────┐
                  │ Zwróć         │      │ Zwróć None   │
                  │ ProductIndex  │      │ (produkt     │
                  │ + zapisz alias│      │ nieznany)   │
                  └───────────────┘      └──────────────┘
                          │                       │
                          └───────────┬───────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                    NORMALIZACJA ZAKOŃCZONA      │
                    (zwróć ProductIndex lub None) │
                                                  │
                          ┌───────────────────────┘
                          │
                          ↓
        ┌─────────────────────────────────────────┐
        │  KATEGORYZACJA (osobny proces)          │
        │  Patrz sekcja 4: Workflow kategoryzacji │
        └─────────────────────────────────────────┘
```

### 3.2. Szczegółowy algorytm normalizacji

**WAŻNE:** Normalizacja nazwy produktu jest oddzielona od wyboru kategorii. Algorytm normalizacji skupia się wyłącznie na znalezieniu odpowiedniego `ProductIndex` na podstawie nazwy produktu z OCR. Wybór kategorii następuje osobno (patrz sekcja 4).

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

**Priorytet:** Najwyższy (najszybsze, najbardziej precyzyjne)

```python
async def _find_by_alias(
    raw_name: str,
    shop_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> Optional[ProductIndex]:
    """
    Wyszukuje produkt po aliasie (original_text z OCR).

    Strategia:
    1. Najpierw szuka aliasów dla konkretnego użytkownika i sklepu
    2. Potem szuka aliasów dla sklepu (bez użytkownika)
    3. Na końcu szuka globalnych aliasów (bez shop_id i user_id)

    Używa:
    - Exact match na LOWER(raw_name) (case-insensitive)
    - Indeks: idx_product_index_aliases_raw_name (GIN)
    """
```

**Query SQL:**

```sql
-- Priorytet 1: User + Shop specific
SELECT pi.* FROM product_indexes pi
JOIN product_index_aliases pia ON pi.id = pia.index_id
WHERE LOWER(pia.raw_name) = LOWER(:raw_name)
  AND pia.user_id = :user_id
  AND pia.shop_id = :shop_id
ORDER BY pia.confirmations_count DESC
LIMIT 1;

-- Priorytet 2: Shop specific (bez user_id)
SELECT pi.* FROM product_indexes pi
JOIN product_index_aliases pia ON pi.id = pia.index_id
WHERE LOWER(pia.raw_name) = LOWER(:raw_name)
  AND pia.shop_id = :shop_id
  AND pia.user_id IS NULL
ORDER BY pia.confirmations_count DESC
LIMIT 1;

-- Priorytet 3: Global (bez shop_id i user_id)
SELECT pi.* FROM product_indexes pi
JOIN product_index_aliases pia ON pi.id = pia.index_id
WHERE LOWER(pia.raw_name) = LOWER(:raw_name)
  AND pia.shop_id IS NULL
  AND pia.user_id IS NULL
ORDER BY pia.confirmations_count DESC
LIMIT 1;
```

**Dlaczego ta kolejność?**

- Aliasy użytkownika są najbardziej precyzyjne (uczenie się per-user)
- Aliasy sklepu są drugie (różne sklepy mogą mieć różne nazwy)
- Globalne aliasy są fallbackiem

#### Step 2: Fuzzy Search w ProductIndex

**Priorytet:** Średni (gdy alias nie znaleziony)

```python
async def _fuzzy_search_product(
    raw_name: str,
    category_suggestion: Optional[str] = None,
    similarity_threshold: float = 0.6
) -> Optional[ProductIndex]:
    """
    Wyszukuje produkt używając fuzzy search (pg_trgm).

    Strategia:
    1. Używa pg_trgm similarity (similarity >= threshold)
    2. Jeśli category_suggestion podane, filtruje po kategorii (OPCJONALNIE - tylko jako pomocnicze filtrowanie)
    3. Sortuje po podobieństwie (DESC)
    4. Zwraca najlepszy match (jeśli similarity >= threshold)

    UWAGA: category_suggestion jest tylko opcjonalnym filtrem pomocniczym.
    Głównym celem jest znalezienie produktu po podobieństwie nazwy, nie po kategorii.

    Używa:
    - Indeks: idx_product_indexes_name_trgm (GIN z pg_trgm)
    - Funkcja: similarity() z pg_trgm
    """
```

**Query SQL:**

```sql
-- Wymaga: CREATE EXTENSION pg_trgm;

-- Bez filtrowania po kategorii (PREFEROWANE - normalizacja nazwy bez wpływu kategorii)
SELECT pi.*,
       similarity(LOWER(pi.name), LOWER(:raw_name)) as sim_score
FROM product_indexes pi
WHERE similarity(LOWER(pi.name), LOWER(:raw_name)) >= :threshold
ORDER BY sim_score DESC
LIMIT 1;

-- Z filtrowaniem po kategorii (OPCJONALNE - tylko gdy category_suggestion podane i chcemy zawęzić wyniki)
SELECT pi.*,
       similarity(LOWER(pi.name), LOWER(:raw_name)) as sim_score
FROM product_indexes pi
JOIN categories c ON pi.category_id = c.id
WHERE similarity(LOWER(pi.name), LOWER(:raw_name)) >= :threshold
  AND LOWER(c.name) = LOWER(:category_suggestion)
ORDER BY sim_score DESC
LIMIT 1;
```

**Parametry:**

- `similarity_threshold = 0.6` - minimalne podobieństwo (60%)
- Można dostosować w config (dla MVP: 0.6, dla production: 0.7)
- Dla krótkich słów (<5 znaków) można użyć wyższego threshold (np. 0.9)

**Wynik normalizacji:**

Algorytm normalizacji kończy się na Step 2. Zwraca:

- `ProductIndex` jeśli produkt został znaleziony (przez alias lub fuzzy search)
- `None` jeśli produkt nie został znaleziony w słowniku

**Uwaga:** Wybór kategorii dla produktu jest osobnym procesem (patrz sekcja 4: Workflow kategoryzacji produktu).

## 4. Workflow kategoryzacji produktu

**WAŻNE:** Kategoryzacja produktu jest oddzielona od normalizacji nazwy. Normalizacja (sekcja 3.2) odpowiada za znalezienie `ProductIndex` na podstawie nazwy. Kategoryzacja odpowiada za przypisanie kategorii do produktu.

### 4.1. Przypisanie kategorii do produktu

Kategoria produktu może pochodzić z:

1. **ProductIndex.category_id** - jeśli produkt został znaleziony w słowniku (normalizacja zwróciła `ProductIndex`)
2. **AI Category** - Gemini wybiera kategorię dla produktu z listy kategorii zdefiniowanej w bazie (gdy produkt nieznany)
3. **Fallback "Inne"** - jeśli nic nie pasuje

### 4.2. Strategia przypisania kategorii

```python
async def _assign_category(
    product_index: Optional[ProductIndex],
    cleaned_text: str,
    category_suggestion: Optional[str] = None,
    shop_name: Optional[str] = None
) -> Category:
    """
    Przypisuje kategorię do produktu.

    Priorytety:
    1. Jeśli product_index ma category_id → użyj tej kategorii
    2. Jeśli product_index jest None → użyj AI Categorization (Gemini API)
    3. W przeciwnym razie → użyj "Inne"
    """
    # Priorytet 1: Kategoria z ProductIndex
    if product_index and product_index.category_id:
        return await self.category_service.get_by_id(product_index.category_id)

    # Priorytet 2: AI Categorization (gdy produkt nieznany)
    if not product_index:
        ai_category_id = await self._ai_categorize_product(
            cleaned_text=cleaned_text,
            category_suggestion=category_suggestion,
            shop_name=shop_name,
            available_categories=await self.category_service.get_all_categories()
        )
        if ai_category_id:
            return await self.category_service.get_by_id(ai_category_id)

    # Priorytet 3: Fallback
    return await self.category_service.get_fallback_category()
```

### 4.3. AI Categorization (Gemini API) [MVP]

**Priorytet:** Wysoki (część MVP).  
**Status:** Implementacja w MVP z użyciem Gemini API.

**Strategia:**

Używamy Gemini API do zaproponowania kategorii dla produktu nieznanego systemowi (gdy normalizacja nie znalazła `ProductIndex`). AI wybiera kategorię na podstawie:

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

### 4.4. Integracja normalizacji i kategoryzacji

```python
async def normalize_item(
    self,
    ocr_item: OCRItem,
    shop_id: Optional[int] = None,
    shop_name: Optional[str] = None,
    user_id: Optional[int] = None,
    save_alias: bool = True
) -> NormalizedItem:
    """
    Normalizuje nazwę produktu i przypisuje kategorię.

    Proces:
    1. Pre-processing tekstu (Step 0)
    2. Normalizacja nazwy (Step 1: aliasy, Step 2: fuzzy search)
    3. Przypisanie kategorii (sekcja 4)
    """
    # Step 0: Pre-processing
    cleaned_text = self._preprocess_text(ocr_item.name)

    # Step 1: Wyszukiwanie w aliasach
    product_index = await self._find_by_alias(
        raw_name=cleaned_text,
        shop_id=shop_id,
        user_id=user_id
    )

    # Step 2: Fuzzy Search (jeśli alias nie znaleziony)
    if not product_index:
        product_index = await self._fuzzy_search_product(
            raw_name=cleaned_text,
            category_suggestion=ocr_item.category_suggestion,  # Opcjonalne filtrowanie
            similarity_threshold=0.6
        )

        # Zapis aliasu po znalezieniu przez fuzzy search
        if product_index and save_alias:
            await self._save_alias(
                raw_name=cleaned_text,
                index_id=product_index.id,
                shop_id=shop_id,
                user_id=user_id
            )

    # Kategoryzacja (osobny proces)
    category = await self._assign_category(
        product_index=product_index,
        cleaned_text=cleaned_text,
        category_suggestion=ocr_item.category_suggestion,
        shop_name=shop_name
    )

    return NormalizedItem(
        original_text=ocr_item.name,
        normalized_name=product_index.name if product_index else None,
        quantity=ocr_item.quantity,
        unit_price=ocr_item.unit_price or Decimal("0.0"),
        total_price=ocr_item.total_price,
        category_id=category.id,
        product_index_id=product_index.id if product_index else None,
        confidence_score=ocr_item.confidence_score,
        is_confident=product_index is not None
    )
```

---

## 5. Workflow uczenia się (Learning)

### 5.1. Zapis aliasu po weryfikacji użytkownika

Gdy użytkownik weryfikuje BillItem, system zapisuje alias.

### 5.2. Automatyczny zapis aliasu po normalizacji (UPSERT) [MVP]

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

## 6. Integracja z Receipt Processing Pipeline

### 6.1. Miejsce w pipeline i Transakcyjność [MVP]

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

### 6.2. Refaktoryzacja `_create_bill_items` [MVP]

Metoda `_create_bill_items` musi przyjmować listę `NormalizedItem`. Logika biznesowa (wyliczanie cen, walidacja ujemnych cen) powinna zostać przeniesiona do mappera lub serwisu AI.

```python
async def _create_bill_items(self, bill_id: int, items: List[NormalizedItem]) -> None:
    """
    Przyjmuje już znormalizowane i przeliczone obiekty.
    Tylko mapuje na model DB i zapisuje.
    """
```

---

## 7. API i interfejsy

### 7.1. Zmiany w CategoryService [MVP]

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

**Data ostatniej aktualizacji:** 2025-01-27  
**Status:** Większość kroków ukończona, code review wykonany

### Krok 1: Struktura i Pre-processing [MVP] ✅

- [x] Utworzyć strukturę plików
- [x] Zaimplementować `_preprocess_text` w `service.py`

### Krok 2: Schemas i Modele [MVP] ✅

- [x] `NormalizedItem` (z logiką cen i walidacji)

### Krok 3: Aliasy z UPSERT [MVP] ✅

- [x] Implementacja `_find_by_alias` (3 zapytania, z indeksem funkcyjnym)
- [x] Implementacja zapisu aliasu z użyciem `ON CONFLICT`

### Krok 4: Fuzzy Search [MVP] ✅

- [x] Implementacja z nowym thresholdem (0.75) i logiką długości słowa

### Krok 5: AI Categorization (Gemini API) [MVP] ✅

- [x] Dodać metodę `get_all_categories()` do CategoryService (pobranie listy kategorii)
- [x] Zaimplementować `_ai_categorize_product()` w AICategorizationService
  - [x] Przygotowanie promptu z kontekstem (produkt, sugestia, sklep, lista kategorii)
  - [x] Wywołanie Gemini API z structured output (JSON)
  - [x] Walidacja odpowiedzi (confidence threshold, istnienie kategorii)
  - [x] Retry pattern (tenacity) dla odporności na błędy
- [x] Zintegrować AI Categorization w `_assign_category()` (osobny proces od normalizacji)
- [x] Dodać fallback do kategorii "Inne" jeśli AI nie zwróciło wyniku
- [x] `CategoryService.get_fallback_category()`

### Krok 6: Refaktoryzacja Processing Pipeline [MVP] ✅

- [x] Zmiana `_create_bill_items` na `List[NormalizedItem]`
- [x] Przeniesienie logiki wyliczania cen do mappera/AI serwisu
- [x] Zarządzanie transakcjami (AI przed `session.begin()`)

---

## 10. Code Review i Naprawy (2025-01-27)

### Naprawione błędy krytyczne:

1. ✅ **Brak parametru `ai_service` w konstruktorze `BillsProcessorService`**

   - Dodano parametr `ai_service: AICategorizationService` do `__init__()`
   - Dodano przypisanie `self.ai_service = ai_service`

2. ✅ **`CategoryService.get_fallback_category()` może zwrócić `None`**
   - Dodano logikę automatycznego tworzenia kategorii fallback jeśli nie istnieje
   - Używa `CategoryCreate` schema do bezpiecznego utworzenia

### Dodane ulepszenia:

1. ✅ **Retry pattern dla wywołań Gemini API**

   - Dodano dekorator `@retry` z `tenacity` (spójny z OCRService)
   - Funkcja `_should_retry_gemini_error()` filtruje błędy do retry (sieć, timeout, rate limit)

2. ✅ **Walidacja `available_categories` w `_ai_categorize_product()`**

   - Dodano sprawdzenie `len(available_categories) == 0`

3. ✅ **Walidacja `category_id` przed użyciem w `_assign_category()`**
   - Dodano sprawdzenie istnienia kategorii w DB przed zwróceniem `Category`
   - Fallback do kategorii "Inne" jeśli AI zwróciło nieprawidłowe ID

### Pozostałe sugestie (do rozważenia):

- Obsługa błędów w `_normalize_items()` - czy `continue` jest zamierzone? (patrz CODE_REVIEW.md)
- Walidacja `category_id` w `NormalizedItem` schema (obecnie `Optional[int]`, ale zawsze używamy fallback)

---
