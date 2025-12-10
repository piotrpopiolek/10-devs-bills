# Plan implementacji modułu AI Categorization Service

**Data utworzenia:** 2025-12-10  
**Status:** Plan implementacji  
**Priorytet:** Wysoki (blokujące MVP)

---

## 1. Przegląd modułu

### 1.1. Cel modułu

Moduł AI Categorization Service odpowiada za:
- **Normalizację nazw produktów** - mapowanie wariantów OCR na standardowe nazwy z Product Index
- **Kategoryzację produktów** - przypisanie produktów do predefiniowanych kategorii
- **Uczenie się z weryfikacji** - zapisywanie aliasów produktów na podstawie weryfikacji użytkownika
- **Fallback do kategorii "Inne"** - dla produktów nieznanych systemowi

### 1.2. Wymagania z PRD

Zgodnie z `.ai/prd.md`:

- **F-03: Kategoryzacja i Normalizacja AI**
  - Wykorzystanie modeli AI (Gemini) do przypisywania każdej pozycji z paragonu do predefiniowanej kategorii
  - Normalizacja nazwy produktu w oparciu o wewnętrzny "słownik produktów" (Product Index)
  
- **F-04: Weryfikacja przez użytkownika**
  - Pozycje niepewne są prezentowane użytkownikowi w Telegramie
  - Użytkownik może potwierdzić lub poprawić sugestię
  - System uczy się na podstawie weryfikacji (product aliases)

- **F-05: Walidacja sumy**
  - System sprawdza poprawność odczytu (już zaimplementowane w OCR Service)

- **F-10: Zarządzanie kategoriami (Admin)**
  - Kategorie produktów są predefiniowane
  - Produkty niepasujące do żadnej kategorii trafiają do domyślnej kategorii "Inne"

### 1.3. Architektura modułu

```
┌─────────────────────────────────────────────────────────────┐
│                    Receipt Processing Pipeline               │
│                                                             │
│  OCR Service → AI Categorization Service → BillItems       │
│      ↓                ↓                          ↓          │
│  OCRItem      NormalizedProduct          BillItemCreate     │
│  (raw text)   (index_id, category)      (z index_id)       │
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
├── schemas.py              # Pydantic schemas dla normalizacji
├── exceptions.py           # Wyjątki specyficzne dla AI
├── dependencies.py         # Dependency Injection
└── strategies.py           # Strategie wyszukiwania (fuzzy, exact, alias)
```

### 2.2. Zależności

Moduł wymaga:
- `ProductIndexService` - wyszukiwanie produktów w słowniku
- `ProductIndexAliasService` - zarządzanie aliasami
- `CategoryService` - wyszukiwanie kategorii (w tym "Inne")
- `AsyncSession` - dostęp do bazy danych
- `Gemini API` - dla zaawansowanej kategoryzacji

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
    └───────────────┘         │ ProductIndex     │
                              └──────────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                      ZNALEZIONO              NIE ZNALEZIONO
                          │                       │
                          ↓                       ↓
                  ┌───────────────┐      ┌──────────────────┐
                  │ Zwróć index_id│      │ Step 3: AI       │
                  │ z fuzzy match │      │ Categorization    │
                  └───────────────┘      │ (opcjonalnie)    │
                                        └──────────────────┘
                                                │
                                    ┌───────────┴───────────┐
                                    │                       │
                            KATEGORIA ZNALEZIONA      BRAK KATEGORII
                                    │                       │
                                    ↓                       ↓
                            ┌───────────────┐      ┌──────────────┐
                            │ Zwróć category │      │ Fallback do  │
                            │ z ProductIndex│      │ "Inne"       │
                            └───────────────┘      └──────────────┘
```

### 3.2. Szczegółowy algorytm normalizacji

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
    - Exact match na LOWER(raoriginal_textw_name) (case-insensitive)
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
    2. Jeśli category_suggestion podane, filtruje po kategorii
    3. Sortuje po podobieństwie (DESC)
    4. Zwraca najlepszy match (jeśli similarity >= threshold)
    
    Używa:
    - Indeks: idx_product_indexes_name_trgm (GIN z pg_trgm)
    - Funkcja: similarity() z pg_trgm
    """
```

**Query SQL:**
```sql
-- Wymaga: CREATE EXTENSION pg_trgm;

-- Bez filtrowania po kategorii
SELECT pi.*, 
       similarity(LOWER(pi.name), LOWER(:raw_name)) as sim_score
FROM product_indexes pi
WHERE similarity(LOWER(pi.name), LOWER(:raw_name)) >= :threshold
ORDER BY sim_score DESC
LIMIT 1;

-- Z filtrowaniem po kategorii (jeśli category_suggestion podane)
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

## 3. Workflow kategoryzacji

### 3.1. Przypisanie kategorii do produktu

Kategoria produktu może pochodzić z:
1. **ProductIndex.category_id** - jeśli produkt jest w słowniku
2. **AI Category** - Gemini wybiera kategorię dla produktu z listy kategorii zdefniowanej w bazie
3. **Fallback "Inne"** - jeśli nic nie pasuje

```python
async def _assign_category(
    product_index: Optional[ProductIndex],
    category_suggestion: Optional[str]
) -> Category:
    """
    Przypisuje kategorię do produktu.
    
    Priorytety:
    1. Jeśli product_index ma category_id → użyj tej kategorii
    2. Gemini wybiera kategorię dla produktu z listy kategorii zdefniowanej w bazie, może sugerować się category_suggestion
    3. W przeciwnym razie → użyj "Inne"
    """
```

### 3.2. Walidacja kategorii

```python
async def _validate_category_name(category_name: str) -> Optional[Category]:
    """
    Sprawdza czy kategoria istnieje w bazie (case-insensitive).
    
    Używa:
    - Indeks: idx_categories_name
    """
```

**Query SQL:**
```sql
SELECT * FROM categories 
WHERE LOWER(name) = LOWER(:category_name)
LIMIT 1;
```

---

## 4. Workflow uczenia się (Learning)

### 4.1. Zapis aliasu po weryfikacji użytkownika

Gdy użytkownik weryfikuje BillItem (poprawia `index_id`):

```python
async def learn_from_verification(
    bill_item_id: int,
    verified_index_id: int,
    shop_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> ProductIndexAlias:
    """
    Zapisuje alias produktu na podstawie weryfikacji użytkownika.
    
    Flow:
    1. Pobierz BillItem (original_text)
    2. Sprawdź czy alias już istnieje (raw_name + index_id)
    3. Jeśli istnieje → zwiększ confirmations_count
    4. Jeśli nie istnieje → utwórz nowy alias
    
    Używa:
    - ProductIndexAliasService.create() lub update()
    """
```

**Logika:**
- Jeśli alias istnieje: `confirmations_count += 1`
- Jeśli nie istnieje: utwórz z `confirmations_count = 1`
- Zapisuj `shop_id` i `user_id` jeśli dostępne (dla lepszego kontekstu)

### 4.2. Automatyczny zapis aliasu po normalizacji

Po udanej normalizacji (gdy znaleziono produkt w ProductIndex):

```python
async def _save_alias_if_new(
    raw_name: str,
    index_id: int,
    shop_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> None:
    """
    Zapisuje alias produktu jeśli nie istnieje.
    
    Używa:
    - Unique constraint: uq_alias_raw_name_index (LOWER(raw_name), index_id)
    - Jeśli już istnieje → zwiększ confirmations_count
    """
```

**Query SQL:**
```sql
-- Sprawdź czy istnieje
SELECT * FROM product_index_aliases
WHERE LOWER(raw_name) = LOWER(:raw_name)
  AND index_id = :index_id
LIMIT 1;

-- Jeśli istnieje → UPDATE confirmations_count
UPDATE product_index_aliases
SET confirmations_count = confirmations_count + 1,
    last_seen_at = NOW()
WHERE LOWER(raw_name) = LOWER(:raw_name)
  AND index_id = :index_id;

-- Jeśli nie istnieje → INSERT
INSERT INTO product_index_aliases (raw_name, index_id, shop_id, user_id, confirmations_count)
VALUES (:raw_name, :index_id, :shop_id, :user_id, 1);
```

---

## 5. Integracja z Receipt Processing Pipeline

### 5.1. Miejsce w pipeline

```python
# backend/src/processing/service.py

async def process_receipt(self, bill_id: int) -> None:
    # ... existing code ...
    
    # Step 4: Call OCR Service
    ocr_data = await self._extract_receipt_data(file_content, bill.image_url)
    
    # Step 4.5: AI Categorization & Normalization (NOWY KROK)
    normalized_items = await self._normalize_items(
        ocr_data.items,
        shop_id=shop_id,  # jeśli już znaleziony
        user_id=bill.user_id
    )
    
    # Step 6: Create BillItems (z normalized_items zamiast ocr_data.items)
    await self._create_bill_items(bill_id, normalized_items)
```

### 5.2. Normalizacja wszystkich pozycji

```python
async def _normalize_items(
    ocr_items: List[OCRItem],
    shop_id: Optional[int] = None,
    user_id: Optional[int] = None
) -> List[NormalizedItem]:
    """
    Normalizuje wszystkie pozycje z OCR.
    
    Returns:
        List[NormalizedItem] - lista znormalizowanych pozycji z index_id
    """
```

**Schema NormalizedItem:**
```python
class NormalizedItem(AppBaseModel):
    """Znormalizowana pozycja produktu"""
    # Dane z OCR
    original_text: str
    quantity: Decimal
    unit_price: Optional[Decimal]
    total_price: Decimal
    confidence_score: float
    
    # Dane znormalizowane
    index_id: Optional[int]  # ID produktu z ProductIndex (None jeśli nie znaleziono)
    category_id: Optional[int]  # ID kategorii (zawsze ustawione, nawet jeśli "Inne")
    normalization_confidence: float  # Pewność normalizacji (0.0-1.0)
    
    # Metadata
    matched_via: Literal["alias", "fuzzy", "ai", "fallback"]  # Jak znaleziono
```

---

## 6. API i interfejsy

### 6.1. Główny serwis

```python
# backend/src/ai/service.py

class AICategorizationService:
    """
    Serwis do kategoryzacji i normalizacji produktów.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        product_index_service: ProductIndexService,
        product_alias_service: ProductIndexAliasService,
        category_service: CategoryService
    ):
        self.session = session
        self.product_index_service = product_index_service
        self.product_alias_service = product_alias_service
        self.category_service = category_service
    
    async def normalize_product(
        self,
        raw_name: str,
        category_suggestion: Optional[str] = None,
        confidence_score: float = 1.0,
        shop_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> NormalizedProduct:
        """
        Główna metoda normalizacji produktu.
        
        Returns:
            NormalizedProduct - znormalizowany produkt z index_id i category_id
        """
    
    async def normalize_items(
        self,
        ocr_items: List[OCRItem],
        shop_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> List[NormalizedItem]:
        """
        Normalizuje listę pozycji z OCR.
        """
    
    async def learn_from_verification(
        self,
        bill_item_id: int,
        verified_index_id: int
    ) -> ProductIndexAlias:
        """
        Zapisuje alias na podstawie weryfikacji użytkownika.
        """
```

### 6.2. Schemas

```python
# backend/src/ai/schemas.py

class NormalizedProduct(AppBaseModel):
    """Znormalizowany produkt"""
    index_id: Optional[int] = Field(None, description="ID produktu z ProductIndex")
    category_id: int = Field(..., description="ID kategorii (zawsze ustawione)")
    normalization_confidence: float = Field(..., ge=0.0, le=1.0)
    matched_via: Literal["alias", "fuzzy", "ai", "fallback"]

class NormalizedItem(AppBaseModel):
    """Znormalizowana pozycja z paragonu"""
    # ... (jak wyżej)
```

### 6.3. Exceptions

```python
# backend/src/ai/exceptions.py

class AICategorizationError(Exception):
    """Błąd podczas kategoryzacji AI"""
    pass

class ProductNormalizationError(Exception):
    """Błąd podczas normalizacji produktu"""
    pass

class CategoryNotFoundError(Exception):
    """Kategoria nie znaleziona (nawet "Inne")"""
    pass
```

---

## 7. Strategie wyszukiwania

### 7.1. Priorytetyzacja strategii

1. **Alias Search** (najszybsze, najbardziej precyzyjne)
   - Exact match na `LOWER(raw_name)`
   - Używa `confirmations_count` do sortowania
   - Kontekst: user_id, shop_id

2. **Fuzzy Search** (średnia szybkość, dobra precyzja)
   - pg_trgm similarity >= 0.6
   - Filtrowanie po kategorii (jeśli dostępne)
   - Sortowanie po similarity score

3. **AI Categorization** (najwolniejsze, opcjonalne)
   - Tylko jeśli fuzzy search nie znalazł
   - Dla MVP: użyj tylko `category_suggestion` z OCR
   - Dla post-MVP: wywołanie Gemini API

4. **Fallback "Inne"** (zawsze dostępne)
   - Jeśli nic nie pasuje
   - Kategoria "Inne" zawsze istnieje (lub jest tworzona)

### 7.2. Performance optimization

- **Caching kategorii "Inne"** - nie szukaj w bazie za każdym razem
- **Batch processing** - normalizuj wiele pozycji w jednej transakcji
- **Indeksy** - wszystkie potrzebne indeksy już istnieją w DB plan

---

## 8. Error handling

### 8.1. Scenariusze błędów

1. **Brak kategorii "Inne"**
   - **Rozwiązanie:** Utwórz automatycznie przy pierwszym użyciu

2. **Błąd fuzzy search (pg_trgm nie dostępne)**
   - **Rozwiązanie:** Fallback do exact match na LOWER(name)

3. **Błąd zapisu aliasu**
   - **Rozwiązanie:** Loguj błąd, kontynuuj bez zapisu aliasu

4. **Błąd AI API (jeśli używane)**
   - **Rozwiązanie:** Fallback do category_suggestion z OCR

### 8.2. Logging

```python
logger.info(f"Normalized product: {raw_name} → {index_id} (via {matched_via})")
logger.warning(f"Product not found in index: {raw_name}, using fallback category")
logger.error(f"Error normalizing product: {raw_name}: {error}")
```

---

## 9. Testy i walidacja

### 9.1. Test cases

1. **Normalizacja przez alias**
   - Alias istnieje dla użytkownika → zwraca index_id
   - Alias istnieje globalnie → zwraca index_id

2. **Normalizacja przez fuzzy search**
   - Podobna nazwa w ProductIndex → zwraca index_id
   - Różna nazwa → zwraca None, używa fallback

3. **Fallback do "Inne"**
   - Nieznany produkt → category_id = "Inne"
   - Kategoria "Inne" nie istnieje → tworzy ją

4. **Uczenie się z weryfikacji**
   - Weryfikacja użytkownika → zapisuje alias
   - Powtórna weryfikacja → zwiększa confirmations_count

### 9.2. Metryki sukcesu

- **Dokładność normalizacji:** % pozycji z `index_id != None`
- **Czas normalizacji:** średni czas na pozycję
- **Użycie aliasów:** % pozycji znalezionych przez aliasy

---

## 10. Implementacja krok po kroku

### Krok 1: Utworzenie struktury modułu
- [ ] Utworzyć `backend/src/ai/` directory
- [ ] Utworzyć `__init__.py`, `service.py`, `schemas.py`, `exceptions.py`, `dependencies.py`

### Krok 2: Implementacja schemas
- [ ] `NormalizedProduct` schema
- [ ] `NormalizedItem` schema
- [ ] Walidacja pól

### Krok 3: Implementacja wyszukiwania w aliasach
- [ ] `_find_by_alias()` - wyszukiwanie po raw_name
- [ ] Priorytetyzacja (user+shop → shop → global)
- [ ] Testy jednostkowe

### Krok 4: Implementacja fuzzy search
- [ ] `_fuzzy_search_product()` - pg_trgm similarity
- [ ] Filtrowanie po kategorii
- [ ] Testy jednostkowe

### Krok 5: Implementacja kategoryzacji
- [ ] `_assign_category()` - przypisanie kategorii
- [ ] `_get_default_category()` - kategoria "Inne"
- [ ] Walidacja kategorii

### Krok 6: Implementacja uczenia się
- [ ] `learn_from_verification()` - zapis aliasu
- [ ] `_save_alias_if_new()` - automatyczny zapis
- [ ] Aktualizacja `confirmations_count`

### Krok 7: Integracja z Processing Pipeline
- [ ] Dodanie `AICategorizationService` do `BillsProcessorService`
- [ ] Wywołanie normalizacji przed `_create_bill_items()`
- [ ] Aktualizacja `_create_bill_items()` do użycia `NormalizedItem`

### Krok 8: Dependency Injection
- [ ] Factory function `get_ai_categorization_service()`
- [ ] Integracja z `processing/dependencies.py`

### Krok 9: Error handling i logging
- [ ] Obsługa błędów w każdym kroku
- [ ] Logging dla monitoringu
- [ ] Fallback strategies

### Krok 10: Testy integracyjne
- [ ] Test pełnego flow: OCR → Normalizacja → BillItems
- [ ] Test uczenia się z weryfikacji
- [ ] Test performance (batch processing)

---

## 11. Konfiguracja

### 11.1. Parametry konfiguracyjne

```python
# backend/src/config.py

class AIConfig:
    # Fuzzy search threshold
    SIMILARITY_THRESHOLD: float = 0.6  # 60% podobieństwa
    
    # AI API (opcjonalnie, dla post-MVP)
    USE_AI_API: bool = False  # Dla MVP: False (używamy tylko OCR category_suggestion)
    AI_API_MODEL: str = "gpt-4"  # Dla post-MVP
    
    # Performance
    BATCH_SIZE: int = 10  # Liczba pozycji do normalizacji w batch
```

### 12.2. Zmienne środowiskowe

```bash
# .env

# AI Categorization
AI_SIMILARITY_THRESHOLD=0.6
AI_USE_API=false  # Dla MVP: false
AI_API_KEY=  # Dla post-MVP
```

---

## 12. Uwagi i ograniczenia

### 12.1. MVP vs Post-MVP

**Dla MVP:**
- Fuzzy search + aliasy wystarczą dla większości przypadków

**Dla post-MVP:**
- Ulepszenie fuzzy search (dostrojenie threshold)
- Machine learning na podstawie weryfikacji użytkowników

### 13.2. Ograniczenia

- **Język:** Tylko polski (locale: 'pl_PL')
- **Kategorie:** Predefiniowane (tylko admin może dodawać)
- **Product Index:** Musi być wypełniony przez admina (lub import)

### 13.3. Rozszerzenia w przyszłości

- **Multi-language support** - różne locale dla aliasów
- **Auto-learning** - automatyczne tworzenie ProductIndex z często weryfikowanych aliasów
- **Category suggestions** - AI sugeruje nowe kategorie na podstawie danych

---

## 14. Przykłady użycia

### 14.1. Normalizacja pojedynczego produktu

```python
# W BillsProcessorService

ai_service = await get_ai_categorization_service(session)

normalized = await ai_service.normalize_product(
    raw_name="Mleko 3.2% 1L",
    category_suggestion="Nabiał",
    confidence_score=0.95,
    shop_id=shop_id,
    user_id=bill.user_id
)

# normalized.index_id = 42 (jeśli znaleziono w ProductIndex)
# normalized.category_id = 5 (kategoria "Nabiał")
# normalized.matched_via = "alias" (lub "fuzzy", "fallback")
```

### 14.2. Normalizacja wszystkich pozycji

```python
normalized_items = await ai_service.normalize_items(
    ocr_items=ocr_data.items,
    shop_id=shop_id,
    user_id=bill.user_id
)

# Tworzenie BillItems z normalized_items
for normalized in normalized_items:
    bill_item = BillItemCreate(
        bill_id=bill_id,
        quantity=normalized.quantity,
        unit_price=normalized.unit_price,
        total_price=normalized.total_price,
        original_text=normalized.original_text,
        confidence_score=normalized.confidence_score,
        index_id=normalized.index_id,  # ← Znormalizowane!
        is_verified=normalized.normalization_confidence >= 0.8
    )
```

### 14.3. Uczenie się z weryfikacji

```python
# W BillItemService.update() (po weryfikacji użytkownika)

if update_data.index_id and bill_item.index_id != update_data.index_id:
    # Użytkownik zmienił index_id → zapisz alias
    await ai_service.learn_from_verification(
        bill_item_id=bill_item.id,
        verified_index_id=update_data.index_id,
        shop_id=bill.shop_id,
        user_id=bill.user_id
    )
```

---

## 15. Podsumowanie

### 15.1. Kluczowe decyzje

1. **Normalizacja PRZED zapisem BillItems** ✅
   - Dane spójne od początku
   - Lepsza wydajność
   - Raporty działają od razu

2. **Priorytetyzacja strategii: Alias → Fuzzy → AI → Fallback**
   - Aliasy są najszybsze i najbardziej precyzyjne
   - Fuzzy search dla nieznanych produktów

3. **Uczenie się z weryfikacji**
   - Zapis aliasów po weryfikacji użytkownika
   - Automatyczny zapis po udanej normalizacji
   - `confirmations_count` dla priorytetyzacji

4. **Fallback do "Inne"**
   - Zawsze dostępna kategoria

### 15.2. Następne kroki

1. Implementacja modułu zgodnie z planem (kroki 1-10)
2. Integracja z Receipt Processing Pipeline
3. Testy jednostkowe i integracyjne
4. Monitoring i optymalizacja

---

**Status:** Plan gotowy do implementacji  
**Szacowany czas:** 8-10h (zgodnie z PLAN_AKTUALIZACJA.md)

