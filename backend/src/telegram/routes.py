from fastapi import APIRouter, Request, status, Header, HTTPException
from src.config import settings
from src.telegram.services import TelegramBotService

router = APIRouter()

@router.post("/webhooks/telegram", status_code=status.HTTP_200_OK, summary="Telegram Webhook Endpoint")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(None, alias="X-Telegram-Bot-Api-Secret-Token")
):
    """
    Handle incoming Telegram updates.
    """
    # Validate secret token if configured
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid secret token")

    await TelegramBotService.process_webhook_update(request, x_telegram_bot_api_secret_token)
    return {"status": "ok"}

