"""
Utility functions for Telegram bot message formatting.
"""

from typing import Optional
from decimal import Decimal

from src.bill_items.models import BillItem


def format_bill_item_for_verification(
    item: BillItem,
    item_number: Optional[int] = None,
    total_items: Optional[int] = None
) -> str:
    """
    Formatuje pozycję do wyświetlenia użytkownikowi w procesie weryfikacji.
    
    Args:
        item: Pozycja do sformatowania
        item_number: Numer aktualnej pozycji (opcjonalne)
        total_items: Całkowita liczba pozycji do weryfikacji (opcjonalne)
        
    Returns:
        str: Sformatowany tekst pozycji
    """
    lines = []
    
    # Progress indicator (jeśli dostępne)
    if item_number is not None and total_items is not None:
        lines.append(f"📋 Pozycja {item_number}/{total_items}\n")
    
    lines.append("─────────────────────")
    
    # Nazwa produktu
    product_name = item.original_text or "Brak nazwy"
    lines.append(f"📦 {product_name}")
    
    # Cena
    lines.append(f"💰 Cena: {item.total_price:.2f} PLN")
    
    # Ilość
    lines.append(f"📊 Ilość: {item.quantity}")
    
    # Cena jednostkowa
    if item.unit_price:
        lines.append(f"💵 Cena jednostkowa: {item.unit_price:.2f} PLN")
    
    # Pewność (jeśli dostępna)
    if item.confidence_score is not None:
        confidence_percent = float(item.confidence_score) * 100
        lines.append(f"🎯 Pewność: {confidence_percent:.0f}%")
    
    # Kategoria (jeśli dostępna)
    if item.category:
        lines.append(f"🏷️ Kategoria: {item.category.name}")
    
    lines.append("─────────────────────")
    
    return "\n".join(lines)


def create_verification_keyboard(bill_item_id: int) -> "InlineKeyboardMarkup":
    """
    Tworzy inline keyboard z przyciskami weryfikacji.
    
    Args:
        bill_item_id: ID pozycji do weryfikacji
        
    Returns:
        InlineKeyboardMarkup: Keyboard z przyciskami
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Zatwierdź",
                callback_data=f"verify:approve:{bill_item_id}"
            ),
            InlineKeyboardButton(
                "✏️ Edytuj",
                callback_data=f"verify:edit:{bill_item_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "⏭️ Pomiń",
                callback_data=f"verify:skip:{bill_item_id}"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

