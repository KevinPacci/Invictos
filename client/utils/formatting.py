from __future__ import annotations

from datetime import date

__all__ = [
    "format_currency",
    "format_full_date",
    "format_month",
]

_MONTH_NAMES = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]


def format_currency(value: float) -> str:
    """Format floats using Spanish locale-like formatting."""
    formatted = f"{value:,.2f}"
    return "$ " + formatted.replace(",", " ").replace(".", ",").replace(" ", ".")


def format_full_date(value: date) -> str:
    return f"{value.day} {_MONTH_NAMES[value.month - 1]} {value.year}"


def format_month(key: str) -> str:
    year, month = key.split("-")
    return f"{_MONTH_NAMES[int(month) - 1]} {year}"
