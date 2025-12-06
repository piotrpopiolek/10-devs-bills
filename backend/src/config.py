from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    ENV: str
    PORT: int
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Supabase (for auth and storage)
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_KEY: str | None = None
    SUPABASE_STORAGE_BUCKET: str = "bills"
    
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_URL: str | None = None
    TELEGRAM_WEBHOOK_SECRET: str | None = None
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAGIC_LINK_EXPIRE_MINUTES: int = 30
    
    # Frontend
    WEB_APP_URL: str = "http://localhost:4321"
    
    # Freemium Limits
    MONTHLY_BILLS_LIMIT: int = 100  # Free tier limit per month
    
    # Celery
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "rpc://"
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore" 
    }

settings = Settings()