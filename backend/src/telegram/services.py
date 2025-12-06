import logging
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from fastapi import Request

from src.config import settings
from src.db.main import AsyncSessionLocal
from src.users.services import UserService
from src.auth.services import AuthService
from src.users.schemas import UserCreate
from src.bills.services import BillService
from src.bills.schemas import BillCreate
from src.bills.models import ProcessingStatus
from src.storage.service import get_storage_service
from src.telegram_messages.services import TelegramMessageService
from src.telegram_messages.schemas import TelegramMessageCreate

logger = logging.getLogger(__name__)

class TelegramBotService:
    _application: Application | None = None

    @classmethod
    async def get_application(cls) -> Application:
        """
        Get or create the singleton Telegram Application instance.
        """
        if cls._application is None:
            # .updater(None) is crucial here because we are using webhooks via FastAPI
            # and don't want python-telegram-bot to initialize its own Updater (which causes issues in some envs)
            cls._application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).updater(None).build()
            await cls._register_handlers(cls._application)
            await cls._application.initialize()
            await cls._application.start()
        return cls._application

    @classmethod
    async def shutdown(cls):
        """
        Shutdown the application on server stop.
        """
        if cls._application:
            await cls._application.stop()
            await cls._application.shutdown()

    @classmethod
    async def _register_handlers(cls, app: Application):
        app.add_handler(CommandHandler("start", cls.start_command))
        app.add_handler(CommandHandler("login", cls.login_command))
        app.add_handler(CommandHandler("dzis", cls.daily_report_command))
        app.add_handler(CommandHandler("tydzien", cls.weekly_report_command))
        app.add_handler(CommandHandler("miesiac", cls.monthly_report_command))
        
        # Handle photos (receipts)
        app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, cls.handle_receipt_image))

    @staticmethod
    async def handle_receipt_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming receipt images.
        """
        if not update.message or not update.effective_user:
            return
            
        telegram_id = update.effective_user.id
        
        # Notify user we are processing
        status_message = await update.message.reply_text("Przetwarzam zdjęcie...")
        
        async with AsyncSessionLocal() as session:
            auth_service = AuthService(session)
            user_service = UserService(session)
            bill_service = BillService(session)
            storage_service = get_storage_service()
            
            # 1. Get or create user
            user = await auth_service.get_user_by_telegram_id(telegram_id)
            if not user:
                try:
                    user = await user_service.create(UserCreate(
                        external_id=telegram_id,
                        is_active=True
                    ))
                except Exception as e:
                    logger.error(f"Error creating user: {e}", exc_info=True)
                    await status_message.edit_text("Błąd autoryzacji. Spróbuj /start.")
                    return

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
                
                image_url, image_hash = await storage_service.upload_file_content(
                    file_content=bytes(file_content),
                    user_id=user.id,
                    extension=extension
                )
                
                # 4. Create Bill record
                from datetime import datetime, timezone
                
                bill_date = update.message.date or datetime.now(timezone.utc)
                
                bill = await bill_service.create(BillCreate(
                    bill_date=bill_date,
                    user_id=user.id,
                    image_url=image_url,
                    image_hash=image_hash,
                    image_expires_at=storage_service.calculate_expiration_date(),
                    status=ProcessingStatus.PENDING
                ))
                
                await status_message.edit_text(f"Paragon przyjęty! ID: {bill.id}\nRozpoczynam analizę...")
                
                # TODO: Trigger OCR task here
                
            except Exception as e:
                logger.error(f"Error processing receipt: {e}", exc_info=True)
                await status_message.edit_text("Wystąpił błąd podczas przetwarzania zdjęcia.")

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.effective_user:
            return
        
        user_id = update.effective_user.id
        username = update.effective_user.username or update.effective_user.first_name

        # We don't necessarily create the user here, we wait for /login or first interaction
        await update.message.reply_text(
            f"Cześć {username}! Jestem botem do śledzenia wydatków.\n"
            "Użyj /login aby się zalogować lub zarejestrować.\n"
            "Możesz też od razu wysłać zdjęcie paragonu."
        )

    @staticmethod
    async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.effective_user:
            return
            
        telegram_id = update.effective_user.id
        
        async with AsyncSessionLocal() as session:
            auth_service = AuthService(session)
            user_service = UserService(session)
            
            # Find user
            user = await auth_service.get_user_by_telegram_id(telegram_id)
            
            if not user:
                # Create user if not exists (auto-registration via Telegram)
                try:
                    user = await user_service.create(UserCreate(
                        external_id=telegram_id,
                        is_active=True
                    ))
                    logger.info(f"Created new user for Telegram ID {telegram_id}")
                except Exception as e:
                    logger.error(f"Error creating user: {e}", exc_info=True)
                    await update.message.reply_text("Wystąpił błąd podczas rejestracji.")
                    return

            # Generate magic link
            try:
                magic_link, url = await auth_service.create_magic_link_for_user(user.id)
                await update.message.reply_text(
                    f"Oto Twój link do logowania (ważny 30 min):\n{url}",
                    disable_web_page_preview=True
                )
            except Exception as e:
                logger.error(f"Error creating magic link: {e}", exc_info=True)
                await update.message.reply_text("Wystąpił błąd podczas generowania linku.")

    @staticmethod
    async def daily_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Raport dzienny - funkcja w przygotowaniu.")

    @staticmethod
    async def weekly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Raport tygodniowy - funkcja w przygotowaniu.")
    
    @staticmethod
    async def monthly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Raport miesięczny - funkcja w przygotowaniu.")

    @classmethod
    async def process_webhook_update(cls, request: Request, secret_token: Optional[str] = None):
        """
        Process incoming webhook update from Telegram.
        """
        # Validate secret token if configured
        # (Telegram sends 'X-Telegram-Bot-Api-Secret-Token' header)
        # For now we skip strict validation unless configured in settings, but it's good practice.
        
        body = await request.json()
        app = await cls.get_application()
        
        # This assumes body is a dict properly formatted as Update
        try:
            update = Update.de_json(body, app.bot)
            if update:
                await app.process_update(update)
        except Exception as e:
            logger.error(f"Failed to process update: {e}", exc_info=True)
            # We still return 200 to Telegram so it doesn't retry infinitely

