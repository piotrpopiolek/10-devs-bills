import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from src.auth.services import AuthService
from src.bills.models import ProcessingStatus
from src.bills.schemas import BillCreate
from src.bills.services import BillService
from src.common.exceptions import (
    ResourceAlreadyExistsError,
    UserCreationError,
    ResourceNotFoundError
)
from src.telegram.context import get_or_create_session, get_storage_service_for_telegram
from src.telegram.error_mapping import get_user_message
from src.users.services import UserService

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
        
    telegram_id = update.effective_user.id
    
    async with get_or_create_session() as session:
        auth_service = AuthService(session)
        
        # Get or create user (eliminates code duplication)
        try:
            user = await auth_service.get_or_create_user_by_telegram_id(telegram_id)
            logger.info(f"User for Telegram ID {telegram_id}: {user.id} (existing or newly created)")
        except (ResourceAlreadyExistsError, UserCreationError) as e:
            logger.error(f"Error getting/creating user: {e}", exc_info=True)
            await update.message.reply_text(get_user_message(e))
            return
        except Exception as e:
            logger.error(f"Unexpected error getting/creating user: {e}", exc_info=True)
            await update.message.reply_text(get_user_message(e))
            return

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
        
    telegram_id = update.effective_user.id
    
    # Notify user we are processing
    status_message = await update.message.reply_text("Przetwarzam zdjęcie...")
    
    async with get_or_create_session() as session:
        # Create service instances with proper DI (no direct instantiation)
        # StorageService is obtained via DI pattern (ContextVar with fallback)
        # This allows for proper testability and lifecycle management.
        storage_service = get_storage_service_for_telegram()
        auth_service = AuthService(session)
        bill_service = BillService(session, storage_service)
        
        # 1. Get or create user (eliminates code duplication)
        try:
            user = await auth_service.get_or_create_user_by_telegram_id(telegram_id)
            logger.info(f"User for Telegram ID {telegram_id}: {user.id} (existing or newly created)")
        except (ResourceAlreadyExistsError, UserCreationError) as e:
            logger.error(f"Error getting/creating user: {e}", exc_info=True)
            await status_message.edit_text(get_user_message(e))
            return
        except Exception as e:
            logger.error(f"Unexpected error getting/creating user: {e}", exc_info=True)
            await status_message.edit_text(get_user_message(e))
            return

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
            
            # TODO: Trigger OCR task here via Dramatiq (using the Outbox event preferably)
            
        except ResourceNotFoundError as e:
            logger.error(f"Resource not found during receipt processing: {e}", exc_info=True)
            await status_message.edit_text("Nie znaleziono wymaganego zasobu. Spróbuj ponownie.")
        except Exception as e:
            logger.error(f"Error processing receipt: {e}", exc_info=True)
            await status_message.edit_text(get_user_message(e))

