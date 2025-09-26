from __future__ import annotations

from typing import Iterable, List

import flet as ft

from . import theme

__all__ = [
    "build_summary_cards",
    "section_container",
]


def build_summary_cards(count: int = 4) -> List[ft.Container]:
    cards: List[ft.Container] = []
    for _ in range(count):
        cards.append(
            ft.Container(
                bgcolor=theme.SURFACE,
                border_radius=theme.CARD_RADIUS,
                padding=ft.padding.all(16),
                content=ft.Column(
                    [
                        ft.Text("-", size=24, weight=ft.FontWeight.W_700),
                        ft.Text("", color=theme.TEXT_MUTED),
                    ],
                    spacing=4,
                ),
            )
        )
    return cards


def section_container(content: ft.Control | Iterable[ft.Control], *, title: str | None = None) -> ft.Container:
    inner = content
    if isinstance(content, Iterable) and not isinstance(content, ft.Control):
        inner = ft.Column(list(content), spacing=14)
    column_controls: List[ft.Control] = []
    if title:
        column_controls.append(ft.Text(title, size=18, weight=ft.FontWeight.W_600))
    column_controls.append(inner if isinstance(inner, ft.Control) else ft.Column(inner))
    return ft.Container(
        bgcolor=theme.SURFACE,
        border_radius=theme.SECTION_RADIUS,
        padding=ft.padding.all(20),
        content=ft.Column(column_controls, spacing=14),
    )
