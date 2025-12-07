import logging
from contextvars import ContextVar
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from src.db.main import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Context variable to store database session per-request
_db_session: ContextVar[Optional[AsyncSession]] = ContextVar("db_session", default=None)


class SessionContextManager:
    """
    Context manager wrapper for existing AsyncSession from DI.
    
    This allows us to use an existing session (from FastAPI DI) as a context manager
    without closing it or managing transactions manually in the handler, 
    since FastAPI manages the session lifecycle via get_session() yield pattern.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self) -> AsyncSession:
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Don't close or commit - FastAPI manages session lifecycle
        # Just pass through any exceptions
        return False


def set_db_session(session: AsyncSession):
    """Set the database session for the current context."""
    _db_session.set(session)


def clear_db_session():
    """Clear the database session from the current context."""
    _db_session.set(None)


def get_or_create_session():
    """
    Get session from context or create a new one as async context manager.
    
    This is a helper to handle both DI (from FastAPI) and fallback scenarios (tests/background).
    Returns an async context manager that can be used with 'async with'.
    """
    session = _db_session.get()
    if session is not None:
        # Session is provided via DI (FastAPI), use it directly
        return SessionContextManager(session)
    else:
        # Fallback: create new session (for tests or direct calls outside request scope)
        logger.warning("No session in context, creating new session. Ensure this is intended (e.g. tests).")
        return AsyncSessionLocal()

