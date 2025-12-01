from fastapi import FastAPI
from src.config import settings
from src.health import router as health_router
from src.categories.routes import router as categories_router
from src.bills.routes import router as bills_router
from src.bill_items.routes import router as bill_items_router
from src.product_index_aliases.routes import router as product_index_aliases_router
from src.product_indexes.routes import router as product_indexes_router
from src.shops.routes import router as shops_router
from src.telegram_messages.routes import router as telegram_messages_router
from src.users.routes import router as users_router
from src.error_handler import exception_handler 

app = FastAPI(
    title="Bills API",
    version="1.0.0",
    docs_url="/docs" if settings.ENV == "development" else None,
)

exception_handler(app)

app.include_router(health_router, tags=["health"])
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(bills_router, prefix="/api/v1/bills", tags=["bills"])
app.include_router(bill_items_router, prefix="/api/v1/bill-items", tags=["bill-items"])
app.include_router(product_index_aliases_router, prefix="/api/v1/product-index-aliases", tags=["product-index-aliases"])
app.include_router(product_indexes_router, prefix="/api/v1/product-indexes", tags=["product-indexes"])
app.include_router(shops_router, prefix="/api/v1/shops", tags=["shops"])
app.include_router(telegram_messages_router, prefix="/api/v1/telegram-messages", tags=["telegram-messages"])