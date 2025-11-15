from fastapi import FastAPI
from src.config import settings
from src.health import router as health_router
from src.categories.routes import router as categories_router   

app = FastAPI(
    title="Bills API",
    version="1.0.0",
    docs_url="/docs" if settings.ENV == "development" else None,
)

app.include_router(health_router, tags=["health"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["categories"])