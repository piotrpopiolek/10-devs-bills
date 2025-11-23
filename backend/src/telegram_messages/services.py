from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Integer, String, Text, DateTime, 
    ForeignKey, Index, BigInteger, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.db.main import Base

if TYPE_CHECKING:
    from src.bills.models import Bill
    from src.users.models import User

class TelegramMessageType(str, enum.Enum):
    TEXT = "text"
    PHOTO = "photo"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    VOICE = "voice"
    STICKER = "sticker"

class TelegramMessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class TelegramMessage(Base):
    """
    TelegramMessage model.
    Stores metadata and content of messages processed by the bot.
    """
    __tablename__ = 'telegram_messages'
    
    __table_args__ = (
        Index('idx_telegram_messages_bill_id', 'bill_id'),
        Index('idx_telegram_messages_user_id', 'user_id'),
        # Złożony indeks przydatny do raportów/historii: "Pokaż wiadomości z tego czatu, posortowane datą"
        Index('idx_telegram_messages_chat_id_created_at', 'chat_id', 'created_at'),
        {'comment': 'Telegram message tracking and content storage for bill processing'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_type: Mapped[TelegramMessageType] = mapped_column(SAEnum(TelegramMessageType, name='telegram_message_type', create_type=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="Message text or caption")
    status: Mapped[TelegramMessageStatus] = mapped_column(SAEnum(TelegramMessageStatus, name='telegram_message_status', create_type=True), nullable=False, server_default=TelegramMessageStatus.SENT.value)
    file_id: Mapped[Optional[str]] = mapped_column(String(255))
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    bill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('bills.id', ondelete='SET NULL'), nullable=True)
    bill: Mapped[Optional['Bill']] = relationship('Bill', back_populates='telegram_messages')
    user: Mapped['User'] = relationship('User', back_populates='telegram_messages')