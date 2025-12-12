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
from src.telegram.utils import format_bill_item_for_verification, create_verification_keyboard

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
    
    async with get_or_create_session() as session:
        auth_service = AuthService(session)
        
        # Generate magic link
        try:
            magic_link, url = await auth_service.create_magic_link_for_user(user.id)
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
    await update.message.reply_text("Raport dzienny - funkcja w przygotowaniu.")


async def weekly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Raport tygodniowy - funkcja w przygotowaniu.")


async def monthly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Raport miesięczny - funkcja w przygotowaniu.")


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
        logger.info(f"User for Telegram ID {update.effective_user.id}: {user.id}")

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
                user_id=user.id,
                extension=extension
            )
            
            # Check for duplicate bills with same image_hash
            stmt = select(Bill).where(Bill.image_hash == image_hash).where(Bill.user_id == user.id).order_by(Bill.id.desc())
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
                    user_id=user.id,
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
                    await start_bill_verification(update, context, bill.id)
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
    bill_id: int
):
    """
    Rozpoczyna proces weryfikacji rachunku.
    Wysyła pierwszą pozycję wymagającą weryfikacji.
    
    Args:
        update: Telegram Update object
        context: Telegram context
        bill_id: ID rachunku do weryfikacji
    """
    if not update.effective_user:
        return
    
    user = get_user()
    if not user:
        logger.error(f"User not found in context for telegram_id {update.effective_user.id}")
        return
    
    async with get_or_create_session() as session:
        try:
            verification_service = await get_bill_verification_service(session=session)
            
            # Pobierz wszystkie pozycje wymagające weryfikacji
            unverified_items = await verification_service.get_unverified_items(
                bill_id=bill_id,
                user_id=user.id
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
                f"Started verification for bill_id={bill_id}, user_id={user.id}. "
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
                    user_id=user.id
                )
                await query.edit_message_text("✅ Pozycja zatwierdzona!")
                
            elif action == "skip":
                # Pomiń pozycję
                await verification_service.skip_item(
                    bill_item_id=bill_item_id,
                    user_id=user.id
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
            
            # Pobierz następną pozycję
            unverified_item_ids = verification_state.get('unverified_item_ids', [])
            if bill_item_id in unverified_item_ids:
                unverified_item_ids.remove(bill_item_id)
            
            next_item = await verification_service.get_next_unverified_item(
                bill_id=bill_id,
                user_id=user.id,
                exclude_item_ids=unverified_item_ids
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
                
                # Pobierz wszystkie pozycje do licznika
                all_unverified = await verification_service.get_unverified_items(
                    bill_id=bill_id,
                    user_id=user.id
                )
                
                current_index = len(unverified_item_ids) - len(all_unverified) + 1
                total_items = len(all_unverified) + (len(unverified_item_ids) - len(all_unverified))
                
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
                
                # Zaktualizuj stan
                verification_state['unverified_item_ids'] = unverified_item_ids
                context.user_data['verification'] = verification_state
            else:
                # Sprawdź czy wszystkie pozycje zostały zweryfikowane
                if await verification_service.check_all_items_verified(bill_id, user.id):
                    # Finalizuj weryfikację
                    await verification_service.finalize_verification(bill_id, user.id)
                    
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
                user_id=user.id,
                edited_text=edited_text
            )
            
            await update.message.reply_text("✅ Pozycja zaktualizowana i zatwierdzona!")
            
            # Wyczyść tryb edycji
            verification_state['editing_item_id'] = None
            bill_id = verification_state.get('bill_id')
            
            if bill_id:
                # Pobierz następną pozycję
                unverified_item_ids = verification_state.get('unverified_item_ids', [])
                if editing_item_id in unverified_item_ids:
                    unverified_item_ids.remove(editing_item_id)
                
                next_item = await verification_service.get_next_unverified_item(
                    bill_id=bill_id,
                    user_id=user.id,
                    exclude_item_ids=unverified_item_ids
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
                    
                    # Pobierz wszystkie pozycje do licznika
                    all_unverified = await verification_service.get_unverified_items(
                        bill_id=bill_id,
                        user_id=user.id
                    )
                    
                    current_index = len(unverified_item_ids) - len(all_unverified) + 1
                    total_items = len(all_unverified) + (len(unverified_item_ids) - len(all_unverified))
                    
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
                    
                    # Zaktualizuj stan
                    verification_state['unverified_item_ids'] = unverified_item_ids
                    context.user_data['verification'] = verification_state
                else:
                    # Sprawdź czy wszystkie pozycje zostały zweryfikowane
                    if await verification_service.check_all_items_verified(bill_id, user.id):
                        # Finalizuj weryfikację
                        await verification_service.finalize_verification(bill_id, user.id)
                        
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
