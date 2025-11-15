from fastapi import FastAPI
from app.api.v1 import auth, users, bills
from app.config import settings

app = FastAPI(
    title="Bills API",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(bills.router, prefix="/api/v1/bills", tags=["bills"])