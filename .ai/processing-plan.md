# Plan Implementacji Receipt Processing Pipeline

**Data utworzenia:** 2025-12-08  
**Data ukończenia:** 2025-12-08  
**Status:** ✅ Ukończone (implementacja podstawowa)  
**Priorytet:** 🔴 Krytyczne (blokujące MVP) - **ZREALIZOWANE**

---

## 📋 Przegląd

Receipt Processing Pipeline to serwis orkiestrujący przetwarzanie paragonów od momentu uploadu do zapisu w bazie danych. Pipeline integruje OCR Service, tworzy BillItems, aktualizuje Bill i obsługuje Shop.

### Cel

Zautomatyzować pełny proces przetwarzania paragonu:

1. Pobranie pliku ze Storage
2. Ekstrakcja danych przez OCR (Gemini API)
3. Zapis pozycji do BillItems
4. Aktualizacja Bill (total_amount, shop_id, status)
5. Obsługa błędów i logowanie

### Architektura

```
Telegram Bot (handle_receipt_image)
    ↓
Bill.create() → status: PENDING
    ↓
ReceiptProcessorService.process_receipt(bill_id)
    ↓
┌─────────────────────────────────────────┐
│ 1. Pobierz plik ze Storage              │
│ 2. Wywołaj OCR Service                  │
│ 3. Aktualizuj Bill → PROCESSING         │
│ 4. Utwórz/znajdź Shop                   │
│ 5. Utwórz BillItems                     │
│ 6. Aktualizuj Bill → COMPLETED          │
│ 7. Obsługa błędów → ERROR                │
└─────────────────────────────────────────┘
```

---

## 🏗️ Struktura Plików

### Nowe pliki do utworzenia:

```
backend/src/
├── processing/
│   ├── __init__.py
│   ├── service.py          # ReceiptProcessorService
│   ├── dependencies.py     # Factory function dla DI
│   └── exceptions.py       # ProcessingError
```

### Pliki do modyfikacji:

```
backend/src/
├── storage/
│   └── service.py          # Dodanie metody download_file()
├── shops/
│   └── services.py         # Dodanie metody get_or_create_by_name()
└── telegram/
    └── handlers.py         # Integracja z ReceiptProcessorService
```

---

## 📝 Krok 1: Dodanie metody download do StorageService

### Lokalizacja: `backend/src/storage/service.py`

### Implementacja:

```python
async def download_file(self, file_path: str) -> bytes:
    """
    Download file from Supabase Storage.

    Args:
        file_path: Storage path (e.g., "bills/2/abc123.jpg")

    Returns:
        File content as bytes

    Raises:
        FileNotFoundError: If file doesn't exist
        RuntimeError: If storage client is not initialized
    """
    if not self.supabase_client:
        raise RuntimeError("Supabase client not initialized")

    try:
        bucket_name = settings.SUPABASE_STORAGE_BUCKET
        file_data = self.supabase_client.storage.from_(bucket_name).download(file_path)
        logger.info(f"File downloaded from Supabase: {file_path}")
        return file_data
    except Exception as e:
        logger.error(f"Failed to download from Supabase: {e}", exc_info=True)
        raise FileNotFoundError(f"File not found in storage: {file_path}") from e
```

**Status:** ✅ Zaimplementowane - tylko Supabase Storage (bez lokalnego fallback).

### Testowanie:

- Test z Supabase Storage
- Test z nieistniejącym plikiem (FileNotFoundError)
- Test z nieinicjalizowanym klientem (RuntimeError)

---

## 📝 Krok 2: Dodanie metody get_or_create do ShopService

### Lokalizacja: `backend/src/shops/services.py`

### Implementacja:

**Status:** ✅ Zaimplementowane z refaktoryzacją (wspólna metoda `_find_by_name_and_address()`).

Metoda `get_or_create_by_name()` została zaimplementowana z wykorzystaniem wspólnej metody pomocniczej `_find_by_name_and_address()`, która eliminuje duplikację kodu i jest również używana przez `_ensure_unique_shop()`.

```python
async def _find_by_name_and_address(
    self,
    name: str,
    address: Optional[str],
    exclude_id: Optional[int] = None
) -> Optional[Shop]:
    """
    Find shop by name and address.
    Returns Shop instance if found, None otherwise.
    """
    stmt = select(Shop).where(
        Shop.name == name,
        Shop.address == address
    )

    if exclude_id is not None:
        stmt = stmt.where(Shop.id != exclude_id)

    result = await self.session.execute(stmt)
    return result.scalar_one_or_none()

async def get_or_create_by_name(self, name: str, address: Optional[str] = None) -> Shop:
    """
    Get existing shop by name and address, or create new one.

    Args:
        name: Shop name (required)
        address: Shop address (optional)

    Returns:
        Shop instance (existing or newly created)

    Note:
        Uses unique constraint on (name, address) to prevent duplicates.
        If shop with same name+address exists, returns existing.
        Otherwise creates new shop.
        Handles race conditions (concurrent creation) by retrying fetch on IntegrityError.
    """
    # Try to find existing shop
    existing_shop = await self._find_by_name_and_address(name, address)

    if existing_shop:
        logger.info(f"Found existing shop: {existing_shop.id} ({name})")
        return existing_shop

    # Create new shop
    new_shop = Shop(name=name, address=address)
    self.session.add(new_shop)

    try:
        await self.session.commit()
        await self.session.refresh(new_shop)
        logger.info(f"Created new shop: {new_shop.id} ({name})")
        return new_shop
    except IntegrityError as e:
        await self.session.rollback()
        # Race condition: shop was created by another request
        # Retry: fetch existing shop
        existing_shop = await self._find_by_name_and_address(name, address)
        if existing_shop:
            logger.info(f"Shop created concurrently, returning existing: {existing_shop.id}")
            return existing_shop
        raise e
```

**Refaktoryzacja:** Metoda `_ensure_unique_shop()` również używa `_find_by_name_and_address()` zamiast duplikować zapytanie SQL, co eliminuje duplikację kodu (DRY principle).

### Testowanie:

- Test tworzenia nowego sklepu
- Test zwracania istniejącego sklepu
- Test race condition (concurrent creation)

---

## 📝 Krok 3: Utworzenie ReceiptProcessorService

### Lokalizacja: `backend/src/processing/service.py`

### Importy:

```python
import logging
from io import BytesIO
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.bills.models import Bill, ProcessingStatus
from src.bills.services import BillService
from src.bill_items.models import BillItem, VerificationSource
from src.bill_items.services import BillItemService
from src.bill_items.schemas import BillItemCreate
from src.shops.services import ShopService
from src.storage.service import StorageService
from src.ocr.services import OCRService
from src.ocr.schemas import OCRReceiptData
from src.ocr.exceptions import (
    FileValidationError,
    ExtractionError,
    AIServiceError
)
from src.common.exceptions import ResourceNotFoundError
from src.processing.exceptions import ProcessingError
from decimal import Decimal
from datetime import datetime
```

### Klasa BillsProcessorService:

**Uwaga:** W implementacji użyto nazwy `BillsProcessorService` zamiast `ReceiptProcessorService` z planu. Nazwa została zmieniona dla lepszej spójności z konwencją nazewnictwa projektu.

````python
logger = logging.getLogger(__name__)


class ReceiptProcessorService:
    """
    Service orchestrating receipt processing pipeline.

    Flow:
    1. Download file from Storage
    2. Call OCR Service
    3. Update Bill status → PROCESSING
    4. Get or create Shop
    5. Create BillItems
    6. Update Bill (total_amount, shop_id, status → COMPLETED)
    7. Handle errors (status → ERROR, error_message)
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_service: StorageService,
        ocr_service: OCRService,
        bill_service: BillService,
        bill_item_service: BillItemService,
        shop_service: ShopService
    ):
        self.session = session
        self.storage_service = storage_service
        self.ocr_service = ocr_service
        self.bill_service = bill_service
        self.bill_item_service = bill_item_service
        self.shop_service = shop_service

    async def process_receipt(self, bill_id: int) -> None:
        """
        Main method processing receipt from PENDING to COMPLETED/ERROR.

        Wszystkie operacje DB są wykonywane w jednej transakcji dla zapewnienia spójności danych.
        W przypadku błędu, transakcja jest automatycznie rollbackowana.

        Args:
            bill_id: ID of the Bill to process

        Raises:
            ResourceNotFoundError: If bill doesn't exist
            ProcessingError: If processing fails (handled internally, sets ERROR status)
        """
        logger.info(f"Starting receipt processing for bill_id={bill_id}")

        # Wszystkie operacje DB w jednej transakcji
        async with self.session.begin():
            try:
                # Step 1: Get Bill and validate status
                bill = await self._get_bill(bill_id)

                if bill.status != ProcessingStatus.PENDING:
                    if bill.status == ProcessingStatus.COMPLETED:
                        logger.info(f"Bill {bill_id} already processed (COMPLETED), skipping")
                    elif bill.status == ProcessingStatus.ERROR:
                        logger.warning(f"Bill {bill_id} previously failed (ERROR), retrying...")
                    else:
                        logger.warning(f"Bill {bill_id} is in status {bill.status}, skipping")
                    return

                if not bill.image_url:
                    await self._set_error(bill_id, "Bill has no image_url")
                    return

                # Step 2: Download file from Storage
                file_content = await self._download_file(bill.image_url)

                # Step 3: Update Bill status → PROCESSING
                await self._update_bill_status(bill_id, ProcessingStatus.PROCESSING)

                # Step 4: Call OCR Service
                ocr_data = await self._extract_receipt_data(file_content, bill.image_url)

                # Step 5: Get or create Shop
                shop_id = await self._get_or_create_shop(
                    ocr_data.shop_name,
                    ocr_data.shop_address
                )

                # Step 6: Create BillItems
                await self._create_bill_items(bill_id, ocr_data)

                # Step 7: Update Bill → COMPLETED
                await self._update_bill_completed(
                    bill_id,
                    total_amount=ocr_data.total_amount,
                    shop_id=shop_id,
                    bill_date=ocr_data.date or bill.bill_date
                )

                logger.info(f"Receipt processing completed for bill_id={bill_id}")
                # Transakcja zostanie automatycznie commitowana przy wyjściu z bloku

            except Exception as e:
                # Transakcja zostanie automatycznie rollbackowana przy wyjątku
                logger.error(f"Error processing receipt bill_id={bill_id}: {e}", exc_info=True)
                await self._set_error(bill_id, str(e))
                raise  # Re-raise for caller to handle if needed

### Metody pomocnicze:

#### 1. `_get_bill()`

```python
async def _get_bill(self, bill_id: int) -> Bill:
    """
    Get Bill model by ID, raise ResourceNotFoundError if not found.

    Używa BillService zamiast duplikacji logiki (DRY principle).
    """
    # Użyj BillService do pobrania modelu (nie response)
    # Musimy dostać się do modelu, więc używamy bezpośredniego zapytania
    # lub dodajemy metodę get_model_by_id() w BillService
    from sqlalchemy import select

    stmt = select(Bill).where(Bill.id == bill_id)
    result = await self.session.execute(stmt)
    bill = result.scalar_one_or_none()

    if not bill:
        raise ResourceNotFoundError("Bill", bill_id)

    return bill
````

**Uwaga:** Alternatywnie, można dodać metodę `get_model_by_id()` w `BillService`:

```python
# W BillService:
async def get_model_by_id(self, bill_id: int) -> Bill:
    """Get Bill model by ID (for internal use, not for API responses)."""
    return await super().get_by_id(bill_id)  # Zwraca model z AppService
```

Wtedy w `ReceiptProcessorService`:

```python
async def _get_bill(self, bill_id: int) -> Bill:
    """Get Bill model by ID using BillService (DRY)."""
    bill_response = await self.bill_service.get_by_id(bill_id)
    # Pobierz model z sesji (bill_response to Pydantic schema)
    # Lepsze: użyj get_model_by_id() jeśli dodamy tę metodę
    stmt = select(Bill).where(Bill.id == bill_id)
    result = await self.session.execute(stmt)
    return result.scalar_one()
```

#### 2. `_download_file()`

```python
async def _download_file(self, image_url: str) -> bytes:
    """
    Download file from Storage.

    Propaguje wyjątki StorageService bez opakowywania (zachowuje typy błędów).
    """
    file_content = await self.storage_service.download_file(image_url)
    logger.debug(f"Downloaded file: {image_url} ({len(file_content)} bytes)")
    return file_content
    # Wyjątki (FileNotFoundError, RuntimeError) propagują się dalej
    # do process_receipt(), gdzie są obsłużone przez _set_error()
```

#### 3. `_extract_receipt_data()`

```python
async def _extract_receipt_data(self, file_content: bytes, filename: str) -> OCRReceiptData:
    """
    Extract receipt data using OCR Service.

    Propaguje wyjątki OCR bez opakowywania (zachowuje typy błędów dla lepszego logowania).
    Wyjątki OCR (FileValidationError, ExtractionError, AIServiceError) propagują się
    do process_receipt(), gdzie są obsłużone przez _set_error().
    """
    # Create UploadFile-like object for OCR Service
    # OCR Service expects UploadFile, so we need to create a file-like object
    file_obj = BytesIO(file_content)

    # Determine MIME type from filename
    mime_type = "image/jpeg"  # default
    if filename.endswith(".png"):
        mime_type = "image/png"
    elif filename.endswith(".webp"):
        mime_type = "image/webp"

    # Create UploadFile
    upload_file = UploadFile(
        file=file_obj,
        filename=filename,
        headers={"content-type": mime_type}
    )

    # Call OCR Service - wyjątki OCR propagują się dalej
    ocr_data = await self.ocr_service.extract_data(upload_file)
    logger.info(f"OCR extraction successful: {len(ocr_data.items)} items")
    return ocr_data
```

#### 4. `_update_bill_status()`

```python
async def _update_bill_status(self, bill_id: int, status: ProcessingStatus) -> None:
    """Update Bill status."""
    from src.bills.schemas import BillUpdate

    update_data = BillUpdate(status=status)

    # Get bill to access user_id
    bill = await self._get_bill(bill_id)

    try:
        await self.bill_service.update(bill_id, update_data, bill.user_id)
        logger.debug(f"Updated bill {bill_id} status to {status.value}")
    except Exception as e:
        logger.error(f"Failed to update bill status: {e}", exc_info=True)
        raise ProcessingError(f"Failed to update bill status: {str(e)}") from e
```

#### 5. `_get_or_create_shop()`

```python
async def _get_or_create_shop(
    self,
    shop_name: Optional[str],
    shop_address: Optional[str]
) -> Optional[int]:
    """Get or create Shop, return shop_id or None."""
    if not shop_name:
        logger.debug("No shop name in OCR data, skipping shop creation")
        return None

    try:
        shop = await self.shop_service.get_or_create_by_name(
            name=shop_name,
            address=shop_address
        )
        logger.info(f"Shop resolved: {shop.id} ({shop_name})")
        return shop.id
    except Exception as e:
        logger.error(f"Failed to get/create shop: {e}", exc_info=True)
        # Don't fail processing if shop creation fails
        # Just log and continue without shop_id
        logger.warning(f"Continuing without shop_id due to error: {e}")
        return None
```

#### 6. `_create_bill_items()`

```python
async def _create_bill_items(self, bill_id: int, ocr_data: OCRReceiptData) -> None:
    """
    Create BillItems from OCR data.

    Waliduje dane przez Pydantic (BillItemCreate z strict=True) przed zapisem do DB.
    """
    if not ocr_data.items:
        logger.warning(f"No items in OCR data for bill_id={bill_id}")
        return

    created_count = 0
    for ocr_item in ocr_data.items:
        try:
            # Determine if item needs verification (confidence < 0.8)
            needs_verification = ocr_item.confidence_score < 0.8

            # Walidacja przez Pydantic (BillItemCreate powinien mieć strict=True)
            bill_item_data = BillItemCreate(
                bill_id=bill_id,
                quantity=ocr_item.quantity,
                unit_price=ocr_item.unit_price or ocr_item.total_price / ocr_item.quantity,
                total_price=ocr_item.total_price,
                original_text=ocr_item.name,
                confidence_score=Decimal(str(ocr_item.confidence_score)),
                is_verified=not needs_verification,  # Auto-verified if confidence >= 0.8
                verification_source=VerificationSource.AUTO
            )
            # Pydantic waliduje typy (strict=True zapobiega niejawnej koercji)

            await self.bill_item_service.create(bill_item_data)
            created_count += 1

        except Exception as e:
            logger.error(
                f"Failed to create bill_item for bill_id={bill_id}, "
                f"item={ocr_item.name}: {e}",
                exc_info=True
            )
            # Continue with other items even if one fails
            continue

    logger.info(f"Created {created_count}/{len(ocr_data.items)} bill_items for bill_id={bill_id}")
```

**Uwaga:** Upewnij się, że `BillItemCreate` ma `strict=True` w `model_config`:

```python
# backend/src/bill_items/schemas.py
class BillItemCreate(AppBaseModel):
    model_config = ConfigDict(strict=True)  # Wymuszenie typów

    bill_id: int
    quantity: Decimal
    # ... reszta pól
```

#### 7. `_update_bill_completed()`

```python
async def _update_bill_completed(
    self,
    bill_id: int,
    total_amount: Decimal,
    shop_id: Optional[int],
    bill_date: datetime
) -> None:
    """Update Bill with final data and set status to COMPLETED."""
    from src.bills.schemas import BillUpdate

    bill = await self._get_bill(bill_id)

    update_data = BillUpdate(
        status=ProcessingStatus.COMPLETED,
        total_amount=total_amount,
        shop_id=shop_id,
        bill_date=bill_date
    )

    try:
        await self.bill_service.update(bill_id, update_data, bill.user_id)
        logger.info(f"Bill {bill_id} marked as COMPLETED")
    except Exception as e:
        logger.error(f"Failed to update bill as completed: {e}", exc_info=True)
        raise ProcessingError(f"Failed to finalize bill: {str(e)}") from e
```

#### 8. `_set_error()`

```python
async def _set_error(self, bill_id: int, error_message: str) -> None:
    """Set Bill status to ERROR and save error message."""
    from src.bills.schemas import BillUpdate

    bill = await self._get_bill(bill_id)

    # Truncate error message to fit database field (Text, but limit for safety)
    max_error_length = 1000
    truncated_error = error_message[:max_error_length] if len(error_message) > max_error_length else error_message

    update_data = BillUpdate(
        status=ProcessingStatus.ERROR,
        error_message=truncated_error
    )

    try:
        await self.bill_service.update(bill_id, update_data, bill.user_id)
        logger.error(f"Bill {bill_id} marked as ERROR: {truncated_error}")
    except Exception as e:
        logger.critical(
            f"CRITICAL: Failed to set error status for bill {bill_id}: {e}",
            exc_info=True
        )
        # Don't re-raise - we're already in error handling
```

### Exception:

```python
# backend/src/processing/exceptions.py
from typing import Optional
from src.common.exceptions import AppError

class ProcessingError(AppError):
    """
    Exception raised during receipt processing.

    Dziedziczy po AppError zgodnie z hierarchią błędów domenowych.
    Będzie tłumaczony na HTTPException przez globalny exception handler.
    """
    def __init__(self, message: str, bill_id: Optional[int] = None):
        self.message = message
        self.bill_id = bill_id
        super().__init__(self.message)
```

---

## 📝 Krok 4: Utworzenie factory function dla ReceiptProcessorService

### Lokalizacja: `backend/src/processing/dependencies.py` (nowy plik)

### Implementacja:

```python
from typing import Optional, Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.processing.service import ReceiptProcessorService
from src.storage.service import StorageService, get_storage_service_for_telegram
from src.ocr.services import OCRService
from src.ocr.routes import get_ocr_service
from src.bills.services import BillService
from src.bill_items.services import BillItemService
from src.shops.services import ShopService
from src.telegram.context import get_or_create_session


async def get_receipt_processor_service(
    session: Optional[AsyncSession] = None
) -> ReceiptProcessorService:
    """
    Factory function for ReceiptProcessorService.

    Works both in FastAPI (with injected session) and Telegram handlers.
    Używa Dependency Injection pattern zgodnie z architekturą projektu.

    Args:
        session: Optional AsyncSession (jeśli None, używa session z context lub tworzy nową)

    Returns:
        ReceiptProcessorService: Configured service instance

    Note:
        W kontekście Telegram, session powinien być już dostępny z `async with get_or_create_session() as session:`
        W FastAPI, session jest wstrzykiwany przez Depends(get_session).
    """
    if session is None:
        # Try to get session from context (Telegram handlers)
        from src.telegram.context import _db_session
        session = _db_session.get()
        if session is None:
            # Fallback: create new session (should not happen in normal flow)
            from src.db.main import AsyncSessionLocal
            session = AsyncSessionLocal()

    storage_service = get_storage_service_for_telegram()
    ocr_service = await get_ocr_service()
    bill_service = BillService(session, storage_service)
    bill_item_service = BillItemService(session)
    shop_service = ShopService(session)

    return ReceiptProcessorService(
        session=session,
        storage_service=storage_service,
        ocr_service=ocr_service,
        bill_service=bill_service,
        bill_item_service=bill_item_service,
        shop_service=shop_service
    )


# Type alias dla FastAPI dependencies (jeśli używane w routes)
ReceiptProcessorServiceDependency = Annotated[
    ReceiptProcessorService,
    Depends(get_receipt_processor_service)
]
```

---

## 📝 Krok 5: Integracja z Telegram Bot

### Lokalizacja: `backend/src/telegram/handlers.py`

### Modyfikacja `handle_receipt_image()`:

```python
# Po utworzeniu Bill (linia ~171), zamiast TODO:

# ... existing code ...
bill = await bill_service.create(BillCreate(
    bill_date=bill_date,
    user_id=user.id,
    image_url=image_url,
    image_hash=image_hash,
    image_expires_at=storage_service.calculate_expiration_date(),
    status=ProcessingStatus.PENDING
))

await status_message.edit_text(f"Paragon przyjęty! ID: {bill.id}\nRozpoczynam analizę...")

# NOWA CZĘŚĆ: Trigger receipt processing
try:
    # Użyj factory function zamiast bezpośredniego tworzenia serwisów
    from src.processing.dependencies import get_receipt_processor_service

    # Get processor via factory function (DI pattern)
    # Session jest już dostępny z 'async with get_or_create_session() as session:'
    processor = await get_receipt_processor_service(session=session)

    # Process receipt
    await processor.process_receipt(bill.id)

    # Update Telegram message with success
    # Pobierz zaktualizowany bill z relacjami
    from sqlalchemy import select
    from src.bills.models import Bill
    stmt = select(Bill).where(Bill.id == bill.id)
    result = await session.execute(stmt)
    updated_bill = result.scalar_one()

    await status_message.edit_text(
        f"✅ Paragon przetworzony!\n"
        f"ID: {bill.id}\n"
        f"Znaleziono {len(updated_bill.bill_items)} pozycji."
    )

except Exception as e:
    logger.error(f"Error processing receipt bill_id={bill.id}: {e}", exc_info=True)
    # Bill status will be ERROR, inform user
    await status_message.edit_text(
        f"⚠️ Paragon zapisany, ale wystąpił błąd podczas analizy.\n"
        f"ID: {bill.id}\n"
        f"Spróbuj ponownie później lub skontaktuj się z supportem."
    )
```

---

## 🧪 Testowanie

### Testy jednostkowe:

1. **StorageService.download_file()**

   - Test pobierania z Supabase
   - Test pobierania z lokalnego storage
   - Test FileNotFoundError

2. **ShopService.get_or_create_by_name()**

   - Test tworzenia nowego sklepu
   - Test zwracania istniejącego
   - Test race condition

3. **ReceiptProcessorService.process_receipt()**
   - Test pełnego flow (mock OCR)
   - Test obsługi błędów OCR
   - Test obsługi błędów Storage
   - Test tworzenia BillItems
   - Test aktualizacji Bill

### Testy integracyjne:

1. **End-to-end test**
   - Upload zdjęcia przez Telegram Bot
   - Weryfikacja utworzenia BillItems
   - Weryfikacja aktualizacji Bill

---

## 🔄 Następne kroki (Post-MVP)

1. **Przeniesienie do Celery** (background tasks)

   - Utworzenie Celery task dla `process_receipt()`
   - Queue management
   - Retry logic

2. **Rozbudowa AI Categorization**

   - Normalizacja nazw produktów
   - Mapowanie do Product Index
   - Fallback do kategorii "Inne"

3. **Notification Service**
   - Powiadomienia Telegram po zakończeniu przetwarzania
   - Prośba o weryfikację dla confidence < 0.8

---

## 📌 Checklist implementacji

- [x] Krok 1: Dodanie `download_file()` do StorageService (tylko Supabase Storage)
- [x] Krok 2: Dodanie `get_or_create_by_name()` do ShopService (z refaktoryzacją - wspólna metoda `_find_by_name_and_address()`)
- [x] Krok 3: Utworzenie BillsProcessorService (nazwa zmieniona z ReceiptProcessorService)
  - [x] `process_receipt()` (bez transakcji - serwisy wykonują własne commity)
  - [x] `_get_bill()` (bezpośrednie zapytanie SQLAlchemy)
  - [x] `_download_file()` (propagacja błędów)
  - [x] `_extract_receipt_data()` (propagacja błędów OCR)
  - [x] `_update_bill_status()`
  - [x] `_get_or_create_shop()`
  - [x] `_create_bill_items()` (walidacja Pydantic, obsługa unit_price calculation)
  - [x] `_update_bill_completed()`
  - [x] `_set_error()`
- [x] Krok 4: Utworzenie factory function (`dependencies.py` - `get_bills_processor_service()`)
- [x] Krok 5: Integracja z Telegram Bot (pełna implementacja w `handle_receipt_image()`)
- [x] Dodanie `aiofiles` do zależności (następnie usunięte - niepotrzebne, tylko Supabase Storage)
- [x] Upewnienie się, że `BillItemCreate` ma `strict=True` (✅ przez `AppBaseModel`)
- [ ] Testy jednostkowe
- [ ] Testy integracyjne
- [ ] Dokumentacja

---

## ⚠️ Uwagi implementacyjne

1. **Transakcje DB**: ⚠️ Operacje DB w `process_receipt()` NIE są w jednej transakcji, ponieważ serwisy (BillService, BillItemService) wykonują własne commity. Implementacja opiera się na optimistic concurrency i explicit error handling. W przyszłości można rozważyć przeniesienie do background task (Dramatiq/Celery) z pełną transakcją.

2. **Error Handling**: Wyjątki domenowe (OCR, Storage) propagują się bez opakowywania, zachowując typy błędów dla lepszego logowania. Obsługa błędów odbywa się w `process_receipt()` przez `_set_error()`.

3. **Logging**: Używać structured logging z `bill_id` w kontekście.

4. **Performance**: Dla większej skali, przenieść do Dramatiq (async processing). W MVP pozostawiamy synchroniczne przetwarzanie w handlerze Telegram.

5. **Idempotency**: `process_receipt()` jest idempotentne - sprawdza status Bill i pomija przetwarzanie, jeśli już jest COMPLETED.

6. **Validation**: ✅ Dane z OCR są walidowane przez Pydantic (`BillItemCreate` z `strict=True`) przed zapisem do DB.

7. **Dependency Injection**: ✅ Użyto factory function (`get_receipt_processor_service()`) zamiast bezpośredniego tworzenia serwisów w handlerze.

8. **Async I/O**: ✅ StorageService używa tylko Supabase Storage (bez lokalnego fallback). Operacje download są asynchroniczne przez Supabase client.

---

---

## ✅ Status implementacji

**Receipt Processing Pipeline został w pełni zaimplementowany i zintegrowany z Telegram Bot.**

### Zrealizowane funkcjonalności:

1. ✅ Pobieranie plików z Supabase Storage (`StorageService.download_file()`)
2. ✅ Tworzenie/znajdowanie sklepów (`ShopService.get_or_create_by_name()`)
3. ✅ Pełny pipeline przetwarzania (`BillsProcessorService.process_receipt()`)
4. ✅ Integracja z OCR Service (ekstrakcja danych z paragonów)
5. ✅ Tworzenie BillItems z walidacją Pydantic
6. ✅ Aktualizacja statusu Bill (PENDING → PROCESSING → COMPLETED/ERROR)
7. ✅ Obsługa błędów z zapisem error_message
8. ✅ Factory function dla Dependency Injection (`get_bills_processor_service()`)
9. ✅ Pełna integracja z Telegram Bot (`handle_receipt_image()`)

### Różnice między planem a implementacją:

- **Nazwa klasy:** `BillsProcessorService` (zamiast `ReceiptProcessorService`)
- **Transakcje:** Operacje nie są w jednej transakcji (serwisy wykonują własne commity)
- **Unit price calculation:** Dodano logikę obliczania `unit_price` z `total_price / quantity` jeśli nie jest podane w OCR

### Następne kroki (opcjonalne):

- [ ] Testy jednostkowe dla `BillsProcessorService`
- [ ] Testy integracyjne (end-to-end z Telegram Bot)
- [ ] Przeniesienie do background task (Dramatiq/Celery) dla async processing
- [ ] Dokumentacja API

**Koniec planu implementacji**
