from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Supabase (for auth, if needed)
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str | None = None
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"
    
    class Config:
        env_file = ".env"