"""
Utility functions for Telegram bot message formatting.
"""

from datetime import date, timedelta
from typing import Optional
from decimal import Decimal

from src.bill_items.models import BillItem
from src.reports.schemas import (
    DailyReportResponse,
    WeeklyReportResponse,
    MonthlyReportResponse,
)


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


def format_daily_report(report: DailyReportResponse) -> str:
    """
    Formatuje raport dzienny do wyświetlenia w Telegramie.
    
    Args:
        report: DailyReportResponse z danymi raportu
        
    Returns:
        str: Sformatowany tekst raportu
    """
    lines = []
    lines.append("📊 RAPORT DZIENNY")
    lines.append("─────────────────────")
    lines.append(f"📅 Data: {report.date.strftime('%d.%m.%Y')}")
    lines.append(f"💰 Łączna kwota: {report.total_amount:.2f} PLN")
    lines.append(f"🧾 Liczba paragonów: {report.bills_count}")
    lines.append("")
    
    # Top kategorie (zgodnie z PRD: top 3, ale pokazujemy wszystkie dostępne do 10)
    if report.top_categories:
        lines.append("🏆 TOP KATEGORIE:")
        for idx, cat_summary in enumerate(report.top_categories[:10], 1):
            lines.append(
                f"{idx}. {cat_summary.category.name}: "
                f"{cat_summary.amount:.2f} PLN ({cat_summary.percentage:.1f}%)"
            )
    else:
        lines.append("ℹ️ Brak wydatków w kategoriach.")
    
    # Sklepy (opcjonalnie, jeśli są dostępne)
    if report.shops:
        lines.append("")
        lines.append("🏪 SKLEPY:")
        for shop_summary in report.shops[:5]:  # Limit do 5 sklepów
            lines.append(
                f"• {shop_summary.shop.name}: "
                f"{shop_summary.amount:.2f} PLN ({shop_summary.bills_count} paragonów)"
            )
    
    return "\n".join(lines)


def format_weekly_report(report: WeeklyReportResponse) -> str:
    """
    Formatuje raport tygodniowy do wyświetlenia w Telegramie.
    
    Args:
        report: WeeklyReportResponse z danymi raportu
        
    Returns:
        str: Sformatowany tekst raportu
    """
    lines = []
    lines.append("📊 RAPORT TYGODNIOWY")
    lines.append("─────────────────────")
    lines.append(
        f"📅 Okres: {report.week_start.strftime('%d.%m.%Y')} - "
        f"{report.week_end.strftime('%d.%m.%Y')}"
    )
    lines.append(f"💰 Łączna kwota: {report.total_amount:.2f} PLN")
    lines.append(f"🧾 Liczba paragonów: {report.bills_count}")
    lines.append("")
    
    # Podział dzienny (zgodnie z PRD: pokazujemy wszystkie dni)
    if report.daily_breakdown:
        lines.append("📅 PODZIAŁ DZIENNY:")
        for day in report.daily_breakdown:
            if day.amount > 0:
                lines.append(
                    f"• {day.date.strftime('%d.%m (%a)')}: "
                    f"{day.amount:.2f} PLN ({day.bills_count} paragonów)"
                )
        lines.append("")
    
    # Top kategorie
    if report.top_categories:
        lines.append("🏆 TOP KATEGORIE:")
        for idx, cat_summary in enumerate(report.top_categories[:10], 1):
            lines.append(
                f"{idx}. {cat_summary.category.name}: "
                f"{cat_summary.amount:.2f} PLN ({cat_summary.percentage:.1f}%)"
            )
    else:
        lines.append("ℹ️ Brak wydatków w kategoriach.")
    
    return "\n".join(lines)


def format_monthly_report(report: MonthlyReportResponse) -> str:
    """
    Formatuje raport miesięczny do wyświetlenia w Telegramie.
    
    Args:
        report: MonthlyReportResponse z danymi raportu
        
    Returns:
        str: Sformatowany tekst raportu
    """
    lines = []
    lines.append("📊 RAPORT MIESIĘCZNY")
    lines.append("─────────────────────")
    
    # Formatuj miesiąc (YYYY-MM -> "Styczeń 2024")
    try:
        year, month_num = map(int, report.month.split('-'))
        month_names = [
            "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"
        ]
        month_name = month_names[month_num - 1]
        lines.append(f"📅 Miesiąc: {month_name} {year}")
    except (ValueError, IndexError):
        lines.append(f"📅 Miesiąc: {report.month}")
    
    lines.append(f"💰 Łączna kwota: {report.total_amount:.2f} PLN")
    lines.append(f"🧾 Liczba paragonów: {report.bills_count}")
    lines.append(f"📈 Średnia dzienna: {report.daily_average:.2f} PLN")
    lines.append("")
    
    # Top kategorie
    if report.top_categories:
        lines.append("🏆 TOP KATEGORIE:")
        for idx, cat_summary in enumerate(report.top_categories[:10], 1):
            lines.append(
                f"{idx}. {cat_summary.category.name}: "
                f"{cat_summary.amount:.2f} PLN ({cat_summary.percentage:.1f}%)"
            )
        lines.append("")
    else:
        lines.append("ℹ️ Brak wydatków w kategoriach.")
        lines.append("")
    
    # Top sklepy
    if report.top_shops:
        lines.append("🏪 TOP SKLEPY:")
        for idx, shop_summary in enumerate(report.top_shops[:10], 1):
            lines.append(
                f"{idx}. {shop_summary.shop.name}: "
                f"{shop_summary.amount:.2f} PLN ({shop_summary.bills_count} paragonów)"
            )
        lines.append("")
    
    # Podział tygodniowy (opcjonalnie, jeśli są dane)
    if report.weekly_breakdown:
        lines.append("📅 PODZIAŁ TYGODNIOWY:")
        for week in report.weekly_breakdown:
            if week.amount > 0:
                week_end = week.week_start + timedelta(days=6)
                lines.append(
                    f"• {week.week_start.strftime('%d.%m')} - "
                    f"{week_end.strftime('%d.%m')}: {week.amount:.2f} PLN"
                )
    
    return "\n".join(lines)

