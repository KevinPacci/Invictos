from __future__ import annotations

import flet as ft

ACCENT = "#3dd598"
DANGER = "#f36b7f"
INFO = "#5b8def"
BACKGROUND = "#0f1215"
SURFACE = "#171c22"
SURFACE_ALT = "#1e242c"
BORDER = "#232a33"
TEXT = "#f5f7fa"
TEXT_MUTED = "#a1acbd"
CARD_RADIUS = 16
SECTION_RADIUS = 14


def configure_page(page: ft.Page) -> None:
    """Apply base styling to the Flet page."""
    page.title = "Invictos Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = ft.padding.symmetric(horizontal=28, vertical=20)
    page.scroll = ft.ScrollMode.AUTO


__all__ = [
    "ACCENT",
    "DANGER",
    "INFO",
    "BACKGROUND",
    "SURFACE",
    "SURFACE_ALT",
    "BORDER",
    "TEXT",
    "TEXT_MUTED",
    "CARD_RADIUS",
    "SECTION_RADIUS",
    "configure_page",
]
