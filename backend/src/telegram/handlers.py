import logging
from datetime import datetime, timezone

from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.auth.services import AuthService
from src.bills.models import Bill, ProcessingStatus
from src.bills.schemas import BillCreate
from src.bills.services import BillService
from src.bill_items.models import BillItem
from src.common.exceptions import ResourceNotFoundError
from src.processing.dependencies import get_bills_processor_service
from src.bills.dependencies import get_bill_verification_service
from src.telegram.context import get_or_create_session, get_storage_service_for_telegram, get_user
from src.telegram.error_mapping import get_user_message
from src.telegram.utils import (
    format_bill_item_for_verification,
    create_verification_keyboard,
    format_daily_report,
    format_weekly_report,
    format_monthly_report,
)
from src.reports.services import ReportService
from src.reports.exceptions import InvalidDateRangeError, InvalidMonthFormatError

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    """
    if not update.message or not update.effective_user:
        return
    
    username = update.effective_user.username or update.effective_user.first_name

    await update.message.reply_text(
        f"Cześć {username}! Jestem botem do śledzenia wydatków.\n"
        "Użyj /login aby się zalogować lub zarejestrować.\n"
        "Możesz też od razu wysłać zdjęcie paragonu."
    )


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /login command using Magic Link.
    """
    if not update.message or not update.effective_user:
        return
        
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    async with get_or_create_session() as session:
        auth_service = AuthService(session)
        
        # Generate magic link
        try:
            magic_link, url = await auth_service.create_magic_link_for_user(user_id)
            await update.message.reply_text(
                f"Oto Twój link do logowania (ważny 30 min):\n{url}",
                disable_web_page_preview=True
            )
        except ResourceNotFoundError as e:
            logger.error(f"User not found when creating magic link: {e}", exc_info=True)
            await update.message.reply_text("Użytkownik nie został znaleziony. Spróbuj /start.")
        except Exception as e:
            logger.error(f"Error creating magic link: {e}", exc_info=True)
            await update.message.reply_text("Wystąpił błąd podczas generowania linku.")


async def daily_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /dzis command - generate daily expense report.
    
    Most Koncepcyjny (PHP → Python):
    W Symfony/Laravel używałbyś Command z argumentami (Symfony Console lub Artisan).
    W python-telegram-bot argumenty są dostępne przez context.args - idiomatyczne
    podejście dla botów Telegram, gdzie argumenty są przekazywane jako lista stringów.
    W tym przypadku, jeśli nie ma argumentów, używamy dzisiejszej daty (domyślna wartość).
    """
    if not update.message or not update.effective_user:
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Parse optional date argument (format: YYYY-MM-DD)
    from datetime import date as date_type
    report_date = date_type.today()  # Default: today
    
    if context.args and len(context.args) > 0:
        try:
            # Parse date from argument (format: YYYY-MM-DD)
            report_date = date_type.fromisoformat(context.args[0])
        except ValueError:
            await update.message.reply_text(
                "⚠️ Nieprawidłowy format daty.\n\n"
                "Użycie: /dzis [YYYY-MM-DD]\n"
                "Przykład: /dzis 2024-01-15\n"
                "Jeśli nie podasz daty, zostanie użyta dzisiejsza data."
            )
            return
    
    async with get_or_create_session() as session:
        try:
            report_service = ReportService(session)
            report = await report_service.get_daily_report(user_id, report_date)
            
            # Format and send report
            formatted_report = format_daily_report(report)
            await update.message.reply_text(formatted_report)
            
        except InvalidDateRangeError as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            logger.error(f"Error generating daily report for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(get_user_message(e))


async def weekly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /tydzien command - generate weekly expense report.
    
    Most Koncepcyjny (PHP → Python):
    Podobnie jak w daily_report_command, używamy context.args do parsowania opcjonalnej daty.
    Jeśli nie ma argumentu, obliczamy początek bieżącego tygodnia (poniedziałek).
    """
    if not update.message or not update.effective_user:
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Parse optional week_start argument (format: YYYY-MM-DD, Monday)
    from datetime import date as date_type, timedelta
    today = date_type.today()
    days_since_monday = today.weekday()
    week_start = today - timedelta(days=days_since_monday)  # Default: current week start
    
    if context.args and len(context.args) > 0:
        try:
            # Parse date from argument (format: YYYY-MM-DD)
            week_start = date_type.fromisoformat(context.args[0])
            # Validate it's Monday (weekday() == 0)
            if week_start.weekday() != 0:
                await update.message.reply_text(
                    "⚠️ Data musi być poniedziałkiem.\n\n"
                    "Użycie: /tydzien [YYYY-MM-DD]\n"
                    "Przykład: /tydzien 2024-01-15 (musi być poniedziałek)\n"
                    "Jeśli nie podasz daty, zostanie użyty początek bieżącego tygodnia."
                )
                return
        except ValueError:
            await update.message.reply_text(
                "⚠️ Nieprawidłowy format daty.\n\n"
                "Użycie: /tydzien [YYYY-MM-DD]\n"
                "Przykład: /tydzien 2024-01-15 (musi być poniedziałek)\n"
                "Jeśli nie podasz daty, zostanie użyty początek bieżącego tygodnia."
            )
            return
    
    async with get_or_create_session() as session:
        try:
            report_service = ReportService(session)
            report = await report_service.get_weekly_report(user_id, week_start)
            
            # Format and send report
            formatted_report = format_weekly_report(report)
            await update.message.reply_text(formatted_report)
            
        except InvalidDateRangeError as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            logger.error(f"Error generating weekly report for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(get_user_message(e))


async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /prywatnosc command - display privacy policy.
    
    Most Koncepcyjny (PHP → Python):
    W Symfony/Laravel używałbyś Command do wyświetlania statycznych treści lub linków.
    W python-telegram-bot po prostu wysyłamy wiadomość tekstową z informacjami o prywatności.
    """
    if not update.message or not update.effective_user:
        return
    
    privacy_text = (
        "🔒 POLITYKA PRYWATNOŚCI\n"
        "─────────────────────\n\n"
        "Twoje dane są dla nas ważne. Oto jak je przetwarzamy:\n\n"
        "📸 ZDJĘCIA PARAGONÓW:\n"
        "• Zdjęcia są przetwarzane automatycznie przez system OCR\n"
        "• Po przetworzeniu zdjęcia są usuwane z serwera\n"
        "• Przechowujemy tylko zanonimizowane dane o produktach i kategoriach\n\n"
        "📊 DANE O WYDATKACH:\n"
        "• Zapisujemy tylko informacje o produktach, cenach i kategoriach\n"
        "• Nie przetwarzamy danych osobowych z paragonów (np. imię kasjera)\n"
        "• Twoje dane są dostępne tylko dla Ciebie\n\n"
        "🔐 BEZPIECZEŃSTWO:\n"
        "• Wszystkie dane są szyfrowane podczas przesyłania\n"
        "• Dostęp do danych wymaga autoryzacji\n"
        "• Nie udostępniamy Twoich danych osobom trzecim\n\n"
        "❓ PYTANIA?\n"
        "Jeśli masz pytania dotyczące prywatności, skontaktuj się z nami."
    )
    
    await update.message.reply_text(privacy_text)


async def monthly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /miesiac command - generate monthly expense report.
    
    Most Koncepcyjny (PHP → Python):
    Podobnie jak w poprzednich komendach, używamy context.args do parsowania opcjonalnego miesiąca.
    Format: YYYY-MM (np. "2024-01"). Jeśli nie ma argumentu, używamy bieżącego miesiąca.
    """
    if not update.message or not update.effective_user:
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Parse optional month argument (format: YYYY-MM)
    from datetime import date as date_type
    today = date_type.today()
    month = today.strftime("%Y-%m")  # Default: current month
    
    if context.args and len(context.args) > 0:
        month = context.args[0]
        # Validate format (basic check, ReportService will do full validation)
        if not month or len(month) != 7 or month[4] != '-':
            await update.message.reply_text(
                "⚠️ Nieprawidłowy format miesiąca.\n\n"
                "Użycie: /miesiac [YYYY-MM]\n"
                "Przykład: /miesiac 2024-01\n"
                "Jeśli nie podasz miesiąca, zostanie użyty bieżący miesiąc."
            )
            return
    
    async with get_or_create_session() as session:
        try:
            report_service = ReportService(session)
            report = await report_service.get_monthly_report(user_id, month)
            
            # Format and send report
            formatted_report = format_monthly_report(report)
            await update.message.reply_text(formatted_report)
            
        except InvalidMonthFormatError as e:
            await update.message.reply_text(str(e))
        except InvalidDateRangeError as e:
            await update.message.reply_text(str(e))
        except Exception as e:
            logger.error(f"Error generating monthly report for user {user_id}: {e}", exc_info=True)
            await update.message.reply_text(get_user_message(e))


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /verify command with bill_id argument.
    Allows manual start of bill verification process.
    
    Usage: /verify {bill_id}
    
    Most Koncepcyjny (PHP → Python):
    W Symfony/Laravel używałbyś Command z argumentami (Symfony Console lub Artisan).
    W python-telegram-bot argumenty są dostępne przez context.args - idiomatyczne
    podejście dla botów Telegram, gdzie argumenty są przekazywane jako lista stringów.
    """
    if not update.message or not update.effective_user:
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Parse bill_id from command arguments
    # context.args contains list of arguments after command (e.g., ["136"] for "/verify 136")
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "⚠️ Nieprawidłowe użycie komendy.\n\n"
            "Użycie: /verify {bill_id}\n"
            "Przykład: /verify 136"
        )
        return
    
    # Validate bill_id is a number
    try:
        bill_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "⚠️ ID rachunku musi być liczbą.\n\n"
            "Użycie: /verify {bill_id}\n"
            "Przykład: /verify 136"
        )
        return
    
    # Validate bill_id is positive
    if bill_id <= 0:
        await update.message.reply_text(
            "⚠️ ID rachunku musi być liczbą dodatnią."
        )
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    async with get_or_create_session() as session:
        try:
            # Verify bill exists and belongs to user
            verification_service = await get_bill_verification_service(session=session)
            
            # Check if bill exists and user has access (via get_unverified_items which checks ownership)
            unverified_items = await verification_service.get_unverified_items(
                bill_id=bill_id,
                user_id=user_id
            )
            
            # Check bill status
            stmt = select(Bill).where(Bill.id == bill_id)
            result = await session.execute(stmt)
            bill = result.scalar_one_or_none()
            
            if not bill:
                await update.message.reply_text(
                    f"⚠️ Rachunek o ID {bill_id} nie został znaleziony."
                )
                return
            
            # Check if bill belongs to user (double check)
            if bill.user_id != user_id:
                await update.message.reply_text(
                    f"⚠️ Nie masz dostępu do rachunku o ID {bill_id}."
                )
                return
            
            # Check if bill is in correct status
            if bill.status == ProcessingStatus.COMPLETED:
                await update.message.reply_text(
                    f"✅ Rachunek o ID {bill_id} został już w pełni przetworzony.\n"
                    f"Wszystkie pozycje zostały zweryfikowane."
                )
                return
            
            if bill.status == ProcessingStatus.ERROR:
                await update.message.reply_text(
                    f"⚠️ Rachunek o ID {bill_id} ma status błędu.\n"
                    f"Nie można rozpocząć weryfikacji."
                )
                return
            
            if bill.status == ProcessingStatus.PENDING or bill.status == ProcessingStatus.PROCESSING:
                await update.message.reply_text(
                    f"⏳ Rachunek o ID {bill_id} jest w trakcie przetwarzania.\n"
                    f"Poczekaj na zakończenie przetwarzania przed weryfikacją."
                )
                return
            
            # Check if there are items to verify
            if not unverified_items:
                await update.message.reply_text(
                    f"✅ Rachunek o ID {bill_id} nie ma pozycji wymagających weryfikacji.\n"
                    f"Wszystkie pozycje zostały już zweryfikowane."
                )
                return
            
            # Start verification process
            await update.message.reply_text(
                f"🔍 Rozpoczynam weryfikację rachunku ID: {bill_id}..."
            )
            
            # Use existing start_bill_verification function
            # Pass user_id to avoid lazy-loading issues when accessing user.id
            await start_bill_verification(update, context, bill_id, user_id)
            
        except ResourceNotFoundError:
            await update.message.reply_text(
                f"⚠️ Rachunek o ID {bill_id} nie został znaleziony."
            )
        except Exception as e:
            logger.error(f"Error in verify_command for bill_id={bill_id}: {e}", exc_info=True)
            await update.message.reply_text(
                f"⚠️ Wystąpił błąd podczas rozpoczynania weryfikacji.\n"
                f"Spróbuj ponownie później lub skontaktuj się z supportem."
            )


async def handle_receipt_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming receipt images.
    Orchestrates the process: Auth -> Download -> Upload -> Create Bill Record.
    """
    if not update.message or not update.effective_user:
        return
        
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await update.message.reply_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Notify user we are processing
    status_message = await update.message.reply_text("Przetwarzam zdjęcie...")
    
    async with get_or_create_session() as session:
        # Create service instances with proper DI (no direct instantiation)
        # StorageService is obtained via DI pattern (ContextVar with fallback)
        # This allows for proper testability and lifecycle management.
        storage_service = get_storage_service_for_telegram()
        # auth_service = AuthService(session) # Not needed as user is already here
        bill_service = BillService(session, storage_service)
        
        # User is already retrieved from context (middleware)
        logger.info(f"User for Telegram ID {update.effective_user.id}: {user_id}")

        # TODO: Check user receipt limit (Freemium Model F-09)
        # if user.receipts_count >= 100: ...

        # 2. Get file from Telegram
        try:
            # Get the largest photo or the document
            if update.message.document:
                file_id = update.message.document.file_id
            else:
                # Photos comes in array of different sizes, last one is biggest
                file_id = update.message.photo[-1].file_id
            
            # Download file
            new_file = await context.bot.get_file(file_id)
            file_content = await new_file.download_as_bytearray()
            
            # 3. Upload to Storage
            # Determine extension (default to jpg if unknown)
            file_path = new_file.file_path
            extension = "jpg"
            if file_path:
                ext = file_path.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'webp']:
                    extension = ext
            
            # Note: storage_service should ideally be async to avoid blocking the event loop
            image_url, image_hash = await storage_service.upload_file_content(
                file_content=bytes(file_content),
                user_id=user_id,
                extension=extension
            )
            
            # Check for duplicate bills with same image_hash
            stmt = select(Bill).where(Bill.image_hash == image_hash).where(Bill.user_id == user_id).order_by(Bill.id.desc())
            result = await session.execute(stmt)
            existing_bills = list(result.scalars().all())  # Convert to list to ensure it's evaluated
            
            # If duplicate exists, use the most recent one instead of creating a new bill
            if existing_bills:
                existing_bill = existing_bills[0]  # Most recent (ordered by id desc)
                
                # Refresh bill from database to ensure we have the latest status
                try:
                    await session.refresh(existing_bill)
                except Exception:
                    # If refresh fails, continue with the status we have
                    pass
                
                # If the existing bill is already processed, just inform the user
                if existing_bill.status in (ProcessingStatus.COMPLETED, ProcessingStatus.TO_VERIFY):
                    # Reload bill with items for display
                    stmt = (
                        select(Bill)
                        .where(Bill.id == existing_bill.id)
                        .options(selectinload(Bill.bill_items))
                    )
                    result = await session.execute(stmt)
                    bill_with_items = result.scalar_one()
                    
                    items_count = len(bill_with_items.bill_items) if bill_with_items.bill_items else 0
                    status_text = "✅ Paragon przetworzony!" if bill_with_items.status == ProcessingStatus.COMPLETED else "✅ Paragon przetworzony!"
                    verification_text = "\n⚠️ Niektóre pozycje wymagają weryfikacji." if bill_with_items.status == ProcessingStatus.TO_VERIFY else ""
                    
                    await status_message.edit_text(
                        f"{status_text}\n"
                        f"ID: {existing_bill.id}\n"
                        f"Znaleziono {items_count} pozycji.\n"
                        f"Kwota: {bill_with_items.total_amount:.2f} PLN{verification_text}\n"
                        f"ℹ️ Ten paragon został już wcześniej przetworzony."
                    )
                    return
                
                # If existing bill is PENDING or PROCESSING, use it and trigger processing
                bill = existing_bill
                await status_message.edit_text(f"Paragon przyjęty! ID: {bill.id}\nRozpoczynam analizę...")
            else:
                # No duplicate found - create new bill
                # 4. Create Bill record
                # TODO: Implement Transactional Outbox here for SAGA pattern
                # Instead of just creating bill, we should also emit 'RECEIPT_UPLOADED' event
                bill_date = update.message.date or datetime.now(timezone.utc)
                
                bill = await bill_service.create(BillCreate(
                    bill_date=bill_date,
                    user_id=user_id,
                    image_url=image_url, # We store the internal storage path here
                    image_hash=image_hash,
                    image_expires_at=storage_service.calculate_expiration_date(),
                    status=ProcessingStatus.PENDING
                ))
                
                await status_message.edit_text(f"Paragon przyjęty! ID: {bill.id}\nRozpoczynam analizę...")
            
            # Trigger bill processing via BillsProcessorService
            try:
                # Get processor via factory function (DI pattern)
                # Session jest już dostępny z 'async with get_or_create_session() as session:'
                processor = await get_bills_processor_service(session=session)
                
                # Process receipt (OCR → AI → Database)
                await processor.process_receipt(bill.id)
                
                # Pobierz zaktualizowany bill z relacjami do wyświetlenia statystyk
                stmt = (
                    select(Bill)
                    .where(Bill.id == bill.id)
                    .options(selectinload(Bill.bill_items))
                )
                result = await session.execute(stmt)
                updated_bill = result.scalar_one()
                
                # Sprawdź status i wyświetl odpowiedni komunikat
                if updated_bill.status == ProcessingStatus.COMPLETED:
                    items_count = len(updated_bill.bill_items) if updated_bill.bill_items else 0
                    await status_message.edit_text(
                        f"✅ Paragon przetworzony!\n"
                        f"ID: {bill.id}\n"
                        f"Znaleziono {items_count} pozycji.\n"
                        f"Kwota: {updated_bill.total_amount:.2f} PLN"
                    )
                elif updated_bill.status == ProcessingStatus.ERROR:
                    error_msg = updated_bill.error_message[:100] if updated_bill.error_message else "Nieznany błąd"
                    await status_message.edit_text(
                        f"⚠️ Paragon zapisany, ale wystąpił błąd podczas analizy.\n"
                        f"ID: {bill.id}\n"
                        f"Błąd: {error_msg}\n"
                        f"Spróbuj ponownie później lub skontaktuj się z supportem."
                    )
                elif updated_bill.status == ProcessingStatus.TO_VERIFY:
                    items_count = len(updated_bill.bill_items) if updated_bill.bill_items else 0
                    unverified_count = sum(1 for item in updated_bill.bill_items if not item.is_verified)
                    
                    await status_message.edit_text(
                        f"✅ Paragon przetworzony!\n"
                        f"ID: {bill.id}\n"
                        f"Znaleziono {items_count} pozycji.\n"
                        f"Kwota: {updated_bill.total_amount:.2f} PLN\n"
                        f"⚠️ {unverified_count} pozycji wymaga weryfikacji.\n\n"
                        f"Rozpoczynam weryfikację..."
                    )
                    
                    # Automatycznie rozpocznij proces weryfikacji
                    # Pass user_id to avoid lazy-loading issues when accessing user.id
                    await start_bill_verification(update, context, bill.id, user_id)
                else:
                    # Status PROCESSING (nie powinno się zdarzyć, ale na wszelki wypadek)
                    await status_message.edit_text(
                        f"⏳ Paragon w trakcie przetwarzania...\n"
                        f"ID: {bill.id}"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing receipt bill_id={bill.id}: {e}", exc_info=True)
                # Bill status will be ERROR (set by BillsProcessorService._set_error())
                # Inform user about the error
                await status_message.edit_text(
                    f"⚠️ Paragon zapisany, ale wystąpił błąd podczas analizy.\n"
                    f"ID: {bill.id}\n"
                    f"Spróbuj ponownie później lub skontaktuj się z supportem."
                )
            
        except ResourceNotFoundError as e:
            logger.error(f"Resource not found during receipt processing: {e}", exc_info=True)
            await status_message.edit_text("Nie znaleziono wymaganego zasobu. Spróbuj ponownie.")
        except Exception as e:
            logger.error(f"Error processing receipt: {e}", exc_info=True)
            await status_message.edit_text(get_user_message(e))


async def start_bill_verification(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    bill_id: int,
    user_id: int
):
    """
    Rozpoczyna proces weryfikacji rachunku.
    Wysyła pierwszą pozycję wymagającą weryfikacji.
    
    Args:
        update: Telegram Update object
        context: Telegram context
        bill_id: ID rachunku do weryfikacji
        user_id: ID użytkownika (musi być przekazane, aby uniknąć problemów z lazy-loading)
    """
    if not update.effective_user:
        return
    
    async with get_or_create_session() as session:
        try:
            verification_service = await get_bill_verification_service(session=session)
            
            # Pobierz wszystkie pozycje wymagające weryfikacji
            unverified_items = await verification_service.get_unverified_items(
                bill_id=bill_id,
                user_id=user_id
            )
            
            if not unverified_items:
                # Wszystkie pozycje już zweryfikowane
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="✅ Wszystkie pozycje zostały już zweryfikowane!"
                )
                return
            
            # Pobierz pierwszą pozycję
            first_item = unverified_items[0]
            
            # Pobierz pozycję z relacjami (category)
            stmt = (
                select(BillItem)
                .where(BillItem.id == first_item.id)
                .options(selectinload(BillItem.category))
            )
            result = await session.execute(stmt)
            item_with_relations = result.scalar_one()
            
            # Formatuj wiadomość
            total_items = len(unverified_items)
            message_text = format_bill_item_for_verification(
                item=item_with_relations,
                item_number=1,
                total_items=total_items
            )
            
            # Utwórz keyboard
            keyboard = create_verification_keyboard(first_item.id)
            
            # Wyślij wiadomość
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message_text,
                reply_markup=keyboard
            )
            
            # Zapisz stan weryfikacji w context.user_data
            context.user_data['verification'] = {
                'bill_id': bill_id,
                'current_item_index': 0,
                'unverified_item_ids': [item.id for item in unverified_items],
                'editing_item_id': None
            }
            
            logger.info(
                f"Started verification for bill_id={bill_id}, user_id={user_id}. "
                f"Total items to verify: {total_items}"
            )
            
        except Exception as e:
            logger.error(f"Error starting bill verification bill_id={bill_id}: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Wystąpił błąd podczas rozpoczynania weryfikacji. Spróbuj ponownie później."
            )


async def handle_item_verification_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Obsługuje callback z przycisków weryfikacji.
    Callback data format: "verify:{action}:{bill_item_id}"
    Actions: "approve", "edit", "skip"
    """
    if not update.callback_query or not update.effective_user:
        return
    
    query: CallbackQuery = update.callback_query
    await query.answer()
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        await query.edit_message_text("Błąd autoryzacji. Spróbuj ponownie za chwilę.")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Parsuj callback_data: "verify:{action}:{bill_item_id}"
    try:
        _, action, bill_item_id_str = query.data.split(":", 2)
        bill_item_id = int(bill_item_id_str)
    except ValueError:
        logger.error(f"Invalid callback data format: {query.data}")
        await query.edit_message_text("⚠️ Nieprawidłowy format danych. Spróbuj ponownie.")
        return
    
    async with get_or_create_session() as session:
        try:
            verification_service = await get_bill_verification_service(session=session)
            
            # Pobierz stan weryfikacji z context
            verification_state = context.user_data.get('verification', {})
            bill_id = verification_state.get('bill_id')
            
            if not bill_id:
                # Jeśli nie ma stanu, spróbuj pobrać z BillItem
                from src.bill_items.services import BillItemService
                bill_item_service = BillItemService(session)
                bill_item = await bill_item_service.get_by_id(bill_item_id)
                bill_id = bill_item.bill_id
                verification_state = {
                    'bill_id': bill_id,
                    'current_item_index': 0,
                    'unverified_item_ids': [],
                    'editing_item_id': None
                }
            
            if action == "approve":
                # Zatwierdź pozycję
                await verification_service.verify_item(
                    bill_item_id=bill_item_id,
                    user_id=user_id
                )
                await query.edit_message_text("✅ Pozycja zatwierdzona!")
                
            elif action == "skip":
                # Pomiń pozycję
                await verification_service.skip_item(
                    bill_item_id=bill_item_id,
                    user_id=user_id
                )
                await query.edit_message_text("⏭️ Pozycja pominięta.")
                
            elif action == "edit":
                # Przejdź do trybu edycji
                verification_state['editing_item_id'] = bill_item_id
                context.user_data['verification'] = verification_state
                
                await query.edit_message_text(
                    "✏️ Wpisz poprawioną nazwę produktu:\n\n"
                    "(Możesz anulować edycję wysyłając /cancel)"
                )
                return
            else:
                logger.error(f"Unknown action in callback: {action}")
                await query.edit_message_text("⚠️ Nieznana akcja.")
                return
            
            # Pobierz następną pozycję (bez exclude_item_ids - pozycja już zweryfikowana ma is_verified=True)
            next_item = await verification_service.get_next_unverified_item(
                bill_id=bill_id,
                user_id=user_id,
                exclude_item_ids=None
            )
            
            if next_item:
                # Pobierz pozycję z relacjami
                stmt = (
                    select(BillItem)
                    .where(BillItem.id == next_item.id)
                    .options(selectinload(BillItem.category))
                )
                result = await session.execute(stmt)
                item_with_relations = result.scalar_one()
                
                # Pobierz wszystkie pozycje do licznika (aktualne, po weryfikacji)
                all_unverified = await verification_service.get_unverified_items(
                    bill_id=bill_id,
                    user_id=user_id
                )
                
                # Oblicz aktualny numer pozycji i całkowitą liczbę
                # Pobierz wszystkie pozycje z rachunku (do obliczenia całkowitej liczby)
                bill_stmt = select(Bill).where(Bill.id == bill_id).options(selectinload(Bill.bill_items))
                bill_result = await session.execute(bill_stmt)
                bill = bill_result.scalar_one()
                total_items_count = len(bill.bill_items) if bill.bill_items else 0
                
                # Oblicz ile pozycji zostało już zweryfikowanych
                verified_count = total_items_count - len(all_unverified)
                current_index = verified_count + 1
                total_items = total_items_count
                
                # Formatuj wiadomość
                message_text = format_bill_item_for_verification(
                    item=item_with_relations,
                    item_number=current_index,
                    total_items=total_items
                )
                
                # Utwórz keyboard
                keyboard = create_verification_keyboard(next_item.id)
                
                # Wyślij następną pozycję
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=message_text,
                    reply_markup=keyboard
                )
                
                # Zaktualizuj stan (zachowaj bill_id dla kolejnych weryfikacji)
                verification_state['bill_id'] = bill_id
                context.user_data['verification'] = verification_state
            else:
                # Sprawdź czy wszystkie pozycje zostały zweryfikowane
                if await verification_service.check_all_items_verified(bill_id, user_id):
                    # Finalizuj weryfikację
                    await verification_service.finalize_verification(bill_id, user_id)
                    
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=(
                            "✅ Weryfikacja zakończona!\n\n"
                            f"Wszystkie pozycje zostały zweryfikowane.\n"
                            f"Rachunek ID: {bill_id} został oznaczony jako ukończony."
                        )
                    )
                    
                    # Wyczyść stan weryfikacji
                    context.user_data.pop('verification', None)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="ℹ️ Nie znaleziono więcej pozycji do weryfikacji."
                    )
            
        except Exception as e:
            logger.error(f"Error handling verification callback: {e}", exc_info=True)
            await query.edit_message_text("⚠️ Wystąpił błąd podczas przetwarzania. Spróbuj ponownie.")


async def handle_item_edit_text(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """
    Obsługuje edycję tekstu pozycji (gdy użytkownik jest w trybie edycji).
    """
    if not update.message or not update.effective_user:
        return
    
    # Sprawdź czy użytkownik jest w trybie edycji
    verification_state = context.user_data.get('verification', {})
    editing_item_id = verification_state.get('editing_item_id')
    
    if not editing_item_id:
        # Nie jesteśmy w trybie edycji, ignoruj
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        return
    
    # Access user.id before entering async context to avoid lazy-loading issues
    user_id = user.id
    
    # Sprawdź czy to komenda /cancel
    if update.message.text and update.message.text.strip().lower() == "/cancel":
        verification_state['editing_item_id'] = None
        context.user_data['verification'] = verification_state
        await update.message.reply_text("❌ Anulowano edycję.")
        return
    
    edited_text = update.message.text.strip() if update.message.text else ""
    
    if not edited_text:
        await update.message.reply_text("⚠️ Tekst nie może być pusty. Wpisz nazwę produktu lub /cancel aby anulować.")
        return
    
    async with get_or_create_session() as session:
        try:
            verification_service = await get_bill_verification_service(session=session)
            
            # Weryfikuj pozycję z edytowanym tekstem
            verified_item = await verification_service.verify_item(
                bill_item_id=editing_item_id,
                user_id=user_id,
                edited_text=edited_text
            )
            
            await update.message.reply_text("✅ Pozycja zaktualizowana i zatwierdzona!")
            
            # Wyczyść tryb edycji
            verification_state['editing_item_id'] = None
            bill_id = verification_state.get('bill_id')
            
            if bill_id:
                # Pobierz następną pozycję (bez exclude_item_ids - pozycja już zweryfikowana ma is_verified=True)
                next_item = await verification_service.get_next_unverified_item(
                    bill_id=bill_id,
                    user_id=user_id,
                    exclude_item_ids=None
                )
                
                if next_item:
                    # Pobierz pozycję z relacjami
                    stmt = (
                        select(BillItem)
                        .where(BillItem.id == next_item.id)
                        .options(selectinload(BillItem.category))
                    )
                    result = await session.execute(stmt)
                    item_with_relations = result.scalar_one()
                    
                    # Pobierz wszystkie pozycje do licznika (aktualne, po weryfikacji)
                    all_unverified = await verification_service.get_unverified_items(
                        bill_id=bill_id,
                        user_id=user_id
                    )
                    
                    # Oblicz aktualny numer pozycji i całkowitą liczbę
                    # Pobierz wszystkie pozycje z rachunku (do obliczenia całkowitej liczby)
                    bill_stmt = select(Bill).where(Bill.id == bill_id).options(selectinload(Bill.bill_items))
                    bill_result = await session.execute(bill_stmt)
                    bill = bill_result.scalar_one()
                    total_items_count = len(bill.bill_items) if bill.bill_items else 0
                    
                    # Oblicz ile pozycji zostało już zweryfikowanych
                    verified_count = total_items_count - len(all_unverified)
                    current_index = verified_count + 1
                    total_items = total_items_count
                    
                    # Formatuj wiadomość
                    message_text = format_bill_item_for_verification(
                        item=item_with_relations,
                        item_number=current_index,
                        total_items=total_items
                    )
                    
                    # Utwórz keyboard
                    keyboard = create_verification_keyboard(next_item.id)
                    
                    # Wyślij następną pozycję
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=message_text,
                        reply_markup=keyboard
                    )
                    
                    # Zaktualizuj stan (zachowaj bill_id dla kolejnych weryfikacji)
                    verification_state['bill_id'] = bill_id
                    context.user_data['verification'] = verification_state
                else:
                    # Sprawdź czy wszystkie pozycje zostały zweryfikowane
                    if await verification_service.check_all_items_verified(bill_id, user_id):
                        # Finalizuj weryfikację
                        await verification_service.finalize_verification(bill_id, user_id)
                        
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=(
                                "✅ Weryfikacja zakończona!\n\n"
                                f"Wszystkie pozycje zostały zweryfikowane.\n"
                                f"Rachunek ID: {bill_id} został oznaczony jako ukończony."
                            )
                        )
                        
                        # Wyczyść stan weryfikacji
                        context.user_data.pop('verification', None)
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="ℹ️ Nie znaleziono więcej pozycji do weryfikacji."
                        )
            
        except Exception as e:
            logger.error(f"Error handling item edit: {e}", exc_info=True)
            await update.message.reply_text("⚠️ Wystąpił błąd podczas aktualizacji pozycji. Spróbuj ponownie.")
