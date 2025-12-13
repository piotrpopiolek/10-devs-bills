"""
Reports module for expense reports and analytics.

This module provides endpoints for generating daily, weekly, and monthly expense reports
with aggregated data from bills and bill_items.
"""

from src.reports.routes import router

__all__ = ["router"]
