from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    pass

