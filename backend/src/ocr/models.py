from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    pass

# NOTE: W MVP endpoint OCR jest stateless - nie zapisuje danych do bazy.
# Dane są zwracane jako JSON w odpowiedzi HTTP.
# W kontekście Telegram Bot, dane są zapisywane do bill_items (is_verified=False).
# Modele bazodanowe dla OCR mogą być dodane w przyszłości, jeśli będzie potrzeba
# przechowywania historii ekstrakcji lub cache'owania wyników.

