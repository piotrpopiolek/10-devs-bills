from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import Field, ConfigDict, model_validator

from src.common.schemas import AppBaseModel


class OCRItem(AppBaseModel):
    """Pojedyncza pozycja z paragonu (Intermediate Representation)"""
    name: str = Field(..., max_length=500, description="Nazwa produktu z paragonu")
    quantity: Decimal = Field(default=Decimal("1.0"), description="Ilość")
    unit_price: Optional[Decimal] = Field(None, description="Cena jednostkowa")
    total_price: Decimal = Field(..., description="Cena całkowita pozycji")
    category_suggestion: Optional[str] = Field(None, max_length=100, description="Sugerowana kategoria produktu (z LLM)")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Ocena pewności odczytu (0.0-1.0)")


class OCRReceiptData(AppBaseModel):
    """Dane paragonu wyekstrahowane przez LLM"""
    shop_name: Optional[str] = Field(None, max_length=200, description="Nazwa sklepu")
    shop_address: Optional[str] = Field(None, max_length=500, description="Adres sklepu")
    date: Optional[datetime] = Field(None, description="Data i czas zakupu")
    total_amount: Decimal = Field(..., description="Łączna kwota paragonu")
    items: List[OCRItem] = Field(default_factory=list, description="Lista pozycji")
    currency: str = Field(default="PLN", max_length=3, description="Waluta")

    @model_validator(mode='after')
    def validate_total_amount(self) -> 'OCRReceiptData':
        """Waliduje, czy suma pozycji jest zbliżona do total_amount (±10% tolerancja)"""
        if not self.items:
            return self

        items_sum = sum(item.total_price for item in self.items)
        tolerance = self.total_amount * Decimal("0.1")  # 10% tolerancja

        if abs(items_sum - self.total_amount) > tolerance:
            raise ValueError(
                f"Suma pozycji ({items_sum}) nie zgadza się z total_amount ({self.total_amount}). "
                f"Różnica: {abs(items_sum - self.total_amount)}"
            )

        return self


class OCRExtractResponse(AppBaseModel):
    """Odpowiedź endpointu OCR"""
    success: bool = Field(default=True, description="Status operacji")
    message: str = Field(default="Ekstrakcja zakończona pomyślnie", description="Komunikat dla użytkownika")
    data: OCRReceiptData = Field(..., description="Wyekstrahowane dane")
    raw_text: Optional[str] = Field(None, description="Surowy tekst z OCR (opcjonalnie, do debugowania)")
    execution_time: float = Field(..., description="Czas przetwarzania w sekundach")


# Strict Mode Schema dla LLM
class LLMReceiptItem(AppBaseModel):
    """Strict schema dla pojedynczej pozycji - używane w komunikacji z LLM"""
    model_config = ConfigDict(
        strict=True,  # Wymuszenie typów
        extra='forbid'  # Odrzucenie nieznanych pól
    )

    name: str
    quantity: float
    unit_price: Optional[float] = None
    total_price: float
    category_suggestion: Optional[str] = None
    confidence_score: float = 1.0


class LLMReceiptExtraction(AppBaseModel):
    """Strict schema dla całego paragonu - używane w komunikacji z LLM"""
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )

    shop_name: Optional[str] = None
    shop_address: Optional[str] = None
    date: Optional[str] = None  # Format ISO 8601
    total_amount: float
    items: List[LLMReceiptItem]
    currency: str = "PLN"

