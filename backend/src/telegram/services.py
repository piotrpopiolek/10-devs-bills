import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, TypeHandler, CallbackQueryHandler, filters

from src.config import settings
from src.telegram import handlers
from src.telegram.bot import LoggingBot
from src.telegram.middleware import logging_middleware
from src.telegram.context import set_db_session, clear_db_session, clear_user

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Service responsible for the lifecycle of the Telegram Bot application.
    It manages initialization, handler registration, and webhook processing.
    """
    _application: Application | None = None

    @classmethod
    async def get_application(cls) -> Application:
        """
        Get or create the singleton Telegram Application instance.
        """
        if cls._application is None:
            # Initialize custom bot with logging capabilities
            bot = LoggingBot(token=settings.TELEGRAM_BOT_TOKEN)
            
            # .updater(None) is crucial here because we are using webhooks via FastAPI
            # and don't want python-telegram-bot to initialize its own Updater
            # We pass our custom bot instance
            cls._application = Application.builder().bot(bot).updater(None).build()
            
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
        """
        Register command and message handlers from the handlers module.
        """
        # Register middleware (group -1 ensures it runs before others)
        app.add_handler(TypeHandler(Update, logging_middleware), group=-1)

        app.add_handler(CommandHandler("start", handlers.start_command))
        app.add_handler(CommandHandler("login", handlers.login_command))
        app.add_handler(CommandHandler("dzis", handlers.daily_report_command))
        app.add_handler(CommandHandler("tydzien", handlers.weekly_report_command))
        app.add_handler(CommandHandler("miesiac", handlers.monthly_report_command))
        app.add_handler(CommandHandler("verify", handlers.verify_command))
        
        # Handle photos (receipts)
        app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handlers.handle_receipt_image))
        
        # Handle verification callbacks (inline keyboard buttons)
        app.add_handler(
            CallbackQueryHandler(
                handlers.handle_item_verification_callback,
                pattern=r"^verify:"
            )
        )
        
        # Handle text messages (for item editing during verification)
        # This handler should run after other message handlers
        # We check in the handler itself if user is in edit mode
        app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                handlers.handle_item_edit_text
            )
        )

    @classmethod
    async def process_webhook_update(
        cls, 
        request: Request, 
        session: AsyncSession,
        secret_token: str | None = None
    ):
        """
        Process incoming webhook update from Telegram.
        
        This method acts as a bridge between FastAPI and python-telegram-bot.
        It injects the database session into the context so handlers can access it.
        
        Args:
            request: FastAPI Request object
            session: Database session injected via FastAPI Depends(get_session)
            secret_token: Optional secret token for webhook validation
        """
        # Set session in context variable so handlers can access it
        set_db_session(session)
        # Clear any previous user context to be safe
        clear_user()
        
        try:
            # Validate secret token if configured
            # (Telegram sends 'X-Telegram-Bot-Api-Secret-Token' header)
            
            body = await request.json()
            app = await cls.get_application()
            
            try:
                update = Update.de_json(body, app.bot)
                if update:
                    await app.process_update(update)
            except Exception as e:
                logger.error(f"Failed to process update: {e}", exc_info=True)
                # We still return 200 to Telegram so it doesn't retry infinitely
        finally:
            # Clear context variable after request to prevent leaks
            clear_db_session()
            clear_user()
