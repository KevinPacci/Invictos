from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List
from uuid import uuid4

import flet as ft

from . import cache
from .api import ApiClient, ApiClientError, ApiConnectionError
from .models import Bet, ParlayLeg
from .state import AppState
from .sync import enqueue_operation, flush_pending

ACCENT = "#3dd598"
DANGER = "#f36b7f"
SURFACE = "#171c22"
SURFACE_ALT = "#1e242c"
TEXT = "#f5f7fa"
TEXT_MUTED = "#a1acbd"


def _format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"
    return "$ " + formatted.replace(",", " ").replace(".", ",").replace(" ", ".")


def _format_full_date(value: date) -> str:
    months = [
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
    return f"{value.day} {months[value.month - 1]} {value.year}"


def _format_month(key: str) -> str:
    year, month = key.split("-")
    months = [
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
    return f"{months[int(month) - 1]} {year}"


def _show_toast(page: ft.Page, text: str, error: bool = False) -> None:
    page.snack_bar = ft.SnackBar(
        bgcolor=DANGER if error else SURFACE_ALT,
        content=ft.Text(text),
        open=True,
    )
    page.update()


def main(page: ft.Page) -> None:
    page.title = "Invictos Tracker"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0f1215"
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.padding = ft.padding.symmetric(horizontal=28, vertical=20)
    page.scroll = ft.ScrollMode.AUTO

    api = ApiClient()
    state = AppState(cache.load_cached_bets())
    flush_pending(api, state)

    selected_date = max((bet.event_date for bet in state.as_list()), default=date.today())
    selected_month = selected_date.strftime("%Y-%m")

    date_picker = ft.DatePicker()
    page.overlay.append(date_picker)

    summary_cards = _build_summary_cards()
    metrics_row = ft.Row(summary_cards, spacing=12, run_spacing=12, wrap=True)

    selected_date_label = ft.Text(_format_full_date(selected_date), size=18, weight=ft.FontWeight.W_600)
    daily_headline = ft.Text("", color=TEXT_MUTED)
    daily_list = ft.Column(spacing=12)
    history_list = ft.Column(spacing=10)

    bet_type_selector = ft.SegmentedButton(
        selected={"single"},
        segments=[
            ft.Segment(value="single", label=ft.Text("Sencilla")),
            ft.Segment(value="parlay", label=ft.Text("Parlay")),
        ],
    )

    detail_field = ft.TextField(label="Detalle", width=420)
    stake_field = ft.TextField(label="Stake", width=160, keyboard_type=ft.KeyboardType.NUMBER)
    odds_field = ft.TextField(label="Cuota", width=160, keyboard_type=ft.KeyboardType.NUMBER)
    cashout_field = ft.TextField(label="Retorno / cashout", width=160, keyboard_type=ft.KeyboardType.NUMBER)
    outcome_field = ft.Dropdown(
        label="Estado",
        width=160,
        options=[
            ft.dropdown.Option("acertada", "Acertada"),
            ft.dropdown.Option("fallida", "Fallida"),
            ft.dropdown.Option("pendiente", "Pendiente"),
        ],
        value="pendiente",
    )

    leg_container = ft.Column(spacing=10)
    parlay_section = ft.Column(
        [
            ft.Text("Selecciones", size=14, color=TEXT_MUTED),
            leg_container,
            ft.TextButton("Agregar seleccion", icon=ft.Icons.ADD, on_click=lambda e: add_leg_row()),
        ]
    )
    parlay_section.visible = False

    form_message = ft.Text("", color=TEXT_MUTED)
    save_button = ft.FilledButton("Guardar", icon=ft.Icons.SAVE)

    def add_leg_row(detail: str = "", odds: str = "") -> None:
        detail_input = ft.TextField(label="Mercado", value=detail, width=320)
        odds_input = ft.TextField(label="Cuota", value=odds, width=120, keyboard_type=ft.KeyboardType.NUMBER)
        remove_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=DANGER)

        def _remove(_: ft.ControlEvent) -> None:
            leg_container.controls[:] = [row for row in leg_container.controls if row.data != (detail_input, odds_input)]
            leg_container.update()
            recalc_parlay_odds()

        remove_btn.on_click = _remove
        row = ft.Row([detail_input, odds_input, remove_btn], spacing=10)
        row.data = (detail_input, odds_input)
        leg_container.controls.append(row)
        leg_container.update()
        recalc_parlay_odds()

    def recalc_parlay_odds() -> None:
        if "parlay" not in bet_type_selector.selected:
            return
        total = 1.0
        valid = False
        for row in leg_container.controls:
            _, odds_input = row.data
            try:
                val = float(odds_input.value)
            except (TypeError, ValueError):
                continue
            if val <= 1:
                continue
            total *= val
            valid = True
        odds_field.value = f"{total:.2f}" if valid else ""
        odds_field.read_only = True
        odds_field.update()

    def toggle_parlay_section() -> None:
        is_parlay = "parlay" in bet_type_selector.selected
        parlay_section.visible = is_parlay
        odds_field.read_only = is_parlay
        if is_parlay and not leg_container.controls:
            add_leg_row()
            add_leg_row()
        if not is_parlay:
            leg_container.controls.clear()
            odds_field.value = ""
        parlay_section.update()
        odds_field.update()

    bet_type_selector.on_change = lambda _: toggle_parlay_section()

    def refresh_metrics() -> None:
        month_key = selected_date.strftime("%Y-%m")
        month_metrics = state.month_metrics(month_key)
        cards_data = [
            (summary_cards[0], _format_currency(month_metrics.stake_total), "Apostado"),
            (summary_cards[1], _format_currency(month_metrics.net), "Neto"),
            (summary_cards[2], f"{month_metrics.wins}/{month_metrics.count}", "Aciertos"),
            (summary_cards[3], f"{month_metrics.yield_percent:.1f}%", "Yield"),
        ]
        for container, value, label in cards_data:
            value_text, caption = container.content.controls
            value_text.value = value
            caption.value = label
            container.update()

    def refresh_daily() -> None:
        bets = state.by_date(selected_date)
        if bets:
            metrics = state.daily_metrics(selected_date)
            daily_headline.value = (
                f"{metrics.count} apuestas | Apostado {_format_currency(metrics.stake_total)} | "
                f"Retorno {_format_currency(metrics.return_total)} | Neto {_format_currency(metrics.net)}"
            )
        else:
            daily_headline.value = "Sin apuestas registradas"
        daily_headline.update()

        daily_list.controls.clear()
        if not bets:
            daily_list.controls.append(ft.Text("Agrega una apuesta para este dia", color=TEXT_MUTED))
        else:
            for bet in bets:
                daily_list.controls.append(build_bet_card(bet))
        daily_list.update()

    def refresh_history() -> None:
        history_list.controls.clear()
        for month_key in state.months():
            if month_key == selected_month:
                continue
            metrics = state.month_metrics(month_key)
            history_list.controls.append(
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=ft.padding.all(14),
                    content=ft.Column(
                        [
                            ft.Text(_format_month(month_key), weight=ft.FontWeight.W_600),
                            ft.Text(f"Neto {_format_currency(metrics.net)}", color=ACCENT if metrics.net >= 0 else DANGER),
                            ft.Text(f"Stake {_format_currency(metrics.stake_total)}", color=TEXT_MUTED, size=12),
                            ft.Text(f"Yield {metrics.yield_percent:.1f}%", color=TEXT_MUTED, size=12),
                        ],
                        spacing=4,
                    ),
                )
            )
        if not history_list.controls:
            history_list.controls.append(ft.Text("Historial vacio aun", color=TEXT_MUTED))
        history_list.update()

    def build_bet_card(bet: Bet) -> ft.Container:
        net_value = bet.net()
        outcome_selector = ft.Dropdown(
            width=160,
            value=bet.outcome,
            options=[
                ft.dropdown.Option("acertada", "Acertada"),
                ft.dropdown.Option("fallida", "Fallida"),
                ft.dropdown.Option("pendiente", "Pendiente"),
            ],
            on_change=lambda e, bet_id=bet.id: update_outcome(bet_id, e.control.value),
        )
        cashout_input = ft.TextField(
            width=140,
            label="Retorno",
            value=f"{bet.cashout:.2f}" if bet.cashout is not None else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_blur=lambda e, bet_id=bet.id: update_cashout(bet_id, e.control.value),
        )
        delete_btn = ft.OutlinedButton(
            text="Eliminar",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=lambda e, bet_id=bet.id: remove_bet(bet_id),
        )
        legs_section: ft.Control | None = None
        if bet.type == "parlay" and bet.legs:
            legs_section = ft.ExpansionTile(
                title=ft.Text(f"Ver selecciones ({len(bet.legs)})"),
                controls=[
                    ft.Column(
                        [ft.Text(f"{idx + 1}. {leg.detail} | {leg.odds:.2f}") for idx, leg in enumerate(bet.legs)],
                        spacing=6,
                    )
                ],
            )
        body = ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            ft.Text("Parlay" if bet.type == "parlay" else "Sencilla", size=12),
                            bgcolor=ACCENT if bet.type == "parlay" else "#5b8def",
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=999,
                        ),
                        ft.Text(bet.detail, size=16, weight=ft.FontWeight.W_600),
                    ],
                    spacing=12,
                ),
                ft.Text(
                    f"Stake {_format_currency(bet.stake)} | Cuota {bet.odds:.2f} | "
                    f"Retorno {_format_currency(bet.gross_return())} | Neto {_format_currency(net_value)}",
                    color=TEXT_MUTED,
                    size=12,
                ),
                ft.Row([outcome_selector, cashout_input, delete_btn], spacing=10, wrap=True),
                legs_section or ft.Container(),
            ],
            spacing=10,
        )
        return ft.Container(bgcolor=SURFACE_ALT, border_radius=12, padding=ft.padding.all(16), content=body)

    def update_outcome(bet_id: str, value: str) -> None:
        patch = {"outcome": value}
        try:
            updated = api.update_bet(bet_id, patch)
            state.upsert(updated)
        except ApiConnectionError:
            enqueue_operation("update", None, {"bet_id": bet_id, "data": patch})
            if bet_id in state.bets:
                state.bets[bet_id].outcome = value
                state.bets[bet_id].updated_at = datetime.utcnow()
        except ApiClientError as error:
            _show_toast(page, str(error), True)
            return
        cache.save_cached_bets(state.as_list())
        refresh_metrics()
        refresh_daily()

    def update_cashout(bet_id: str, value: str) -> None:
        clean = value.strip()
        payload = {"cashout": float(clean)} if clean else {"cashout": None}
        try:
            updated = api.update_bet(bet_id, payload)
            state.upsert(updated)
        except ApiConnectionError:
            enqueue_operation("update", None, {"bet_id": bet_id, "data": payload})
            if bet_id in state.bets:
                state.bets[bet_id].cashout = payload["cashout"]
                state.bets[bet_id].updated_at = datetime.utcnow()
        except (ValueError, ApiClientError):
            _show_toast(page, "Valor invalido", True)
            return
        cache.save_cached_bets(state.as_list())
        refresh_metrics()
        refresh_daily()

    def remove_bet(bet_id: str) -> None:
        try:
            api.delete_bet(bet_id)
            state.remove(bet_id)
        except ApiConnectionError:
            state.remove(bet_id)
            enqueue_operation("delete", None, {"bet_id": bet_id})
            _show_toast(page, "Eliminado localmente, pendiente de sincronizacion")
        except ApiClientError as error:
            _show_toast(page, str(error), True)
            return
        cache.save_cached_bets(state.as_list())
        refresh_metrics()
        refresh_daily()
        refresh_history()

    def set_selected_date(new_date: date) -> None:
        nonlocal selected_date, selected_month
        selected_date = new_date
        selected_month = selected_date.strftime("%Y-%m")
        selected_date_label.value = _format_full_date(selected_date)
        selected_date_label.update()
        refresh_metrics()
        refresh_daily()
        refresh_history()

    def shift_day(delta: int) -> None:
        set_selected_date(selected_date + timedelta(days=delta))

    def open_date_picker(_: ft.ControlEvent) -> None:
        def handle_pick(event: ft.DatePickerEvent) -> None:
            if event.data:
                set_selected_date(date.fromisoformat(event.data))

        date_picker.on_change = handle_pick
        date_picker.pick_date()

    def load_remote(_: ft.ControlEvent | None = None) -> None:
        try:
            remote = api.list_bets()
        except ApiConnectionError:
            _show_toast(page, "Sin conexion con el backend", True)
            return
        state.replace_all(remote, datetime.utcnow())
        cache.save_cached_bets(state.as_list())
        _show_toast(page, "Sincronizacion completa")
        refresh_metrics()
        refresh_daily()
        refresh_history()

    def reset_form() -> None:
        detail_field.value = ""
        stake_field.value = ""
        odds_field.value = ""
        cashout_field.value = ""
        outcome_field.value = "pendiente"
        bet_type_selector.selected = {"single"}
        toggle_parlay_section()
        for control in [detail_field, stake_field, odds_field, cashout_field, outcome_field, bet_type_selector]:
            control.update()
        form_message.value = ""
        form_message.update()

    def submit_form(_: ft.ControlEvent | None = None) -> None:
        detail = (detail_field.value or "").strip()
        if not detail:
            form_message.value = "Describe la apuesta"
            form_message.color = DANGER
            form_message.update()
            return
        try:
            stake = float(stake_field.value)
            odds_val = float(odds_field.value)
        except (TypeError, ValueError):
            form_message.value = "Stake/cuota invalidos"
            form_message.color = DANGER
            form_message.update()
            return
        if stake <= 0 or odds_val <= 1:
            form_message.value = "Stake y cuota deben ser > 0"
            form_message.color = DANGER
            form_message.update()
            return
        cashout = None
        if cashout_field.value:
            try:
                cashout = float(cashout_field.value)
            except ValueError:
                form_message.value = "Cashout invalido"
                form_message.color = DANGER
                form_message.update()
                return
        legs: List[ParlayLeg] = []
        if "parlay" in bet_type_selector.selected:
            for row in leg_container.controls:
                detail_input, odds_input = row.data
                leg_detail = (detail_input.value or "").strip()
                try:
                    leg_odds = float(odds_input.value)
                except (TypeError, ValueError):
                    continue
                if leg_detail and leg_odds > 1:
                    legs.append(ParlayLeg(id=str(uuid4()), detail=leg_detail, odds=leg_odds))
            if len(legs) < 2:
                form_message.value = "Un parlay necesita 2+ selecciones"
                form_message.color = DANGER
                form_message.update()
                return
        bet = Bet(
            id=str(uuid4()),
            event_date=selected_date,
            type="parlay" if "parlay" in bet_type_selector.selected else "single",
            detail=detail,
            stake=stake,
            odds=odds_val,
            cashout=cashout,
            outcome=outcome_field.value,
            legs=legs,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        try:
            created = api.create_bet(bet)
            state.upsert(created)
        except ApiConnectionError:
            state.upsert(bet)
            enqueue_operation("create", bet, bet.to_dict())
            _show_toast(page, "Sin conexion. Guardado localmente")
        except ApiClientError as error:
            form_message.value = str(error)
            form_message.color = DANGER
            form_message.update()
            return
        cache.save_cached_bets(state.as_list())
        refresh_metrics()
        refresh_daily()
        refresh_history()
        reset_form()
        form_message.value = "Apuesta guardada"
        form_message.color = ACCENT
        form_message.update()

    save_button.on_click = submit_form

    toolbar = ft.Row(
        [
            ft.Row(
                [
                    ft.TextButton("Hoy", on_click=lambda e: set_selected_date(date.today())),
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Anterior", on_click=lambda e: shift_day(-1)),
                    ft.IconButton(icon=ft.Icons.ARROW_FORWARD, tooltip="Siguiente", on_click=lambda e: shift_day(1)),
                    ft.TextButton("Elegir fecha", icon=ft.Icons.CALENDAR_MONTH, on_click=open_date_picker),
                ],
                spacing=6,
            ),
            ft.FilledButton("Sincronizar", icon=ft.Icons.CLOUD_SYNC, on_click=load_remote),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    dashboard = ft.Column(
        [
            ft.Text("Invictos Bet Tracker", size=26, weight=ft.FontWeight.W_700),
            ft.Text("Seguimiento modular de tus apuestas con sincronizacion", color=TEXT_MUTED),
            metrics_row,
            toolbar,
            selected_date_label,
            daily_headline,
            ft.Container(bgcolor=SURFACE, border_radius=14, padding=ft.padding.all(16), content=daily_list),
            ft.Text("Historial", size=20, weight=ft.FontWeight.W_600),
            ft.Container(bgcolor=SURFACE_ALT, border_radius=14, padding=ft.padding.all(16), content=history_list),
            ft.Container(
                bgcolor=SURFACE,
                border_radius=16,
                padding=ft.padding.all(20),
                content=ft.Column(
                    [
                        ft.Text("Registrar nueva apuesta", size=18, weight=ft.FontWeight.W_600),
                        bet_type_selector,
                        ft.Row([detail_field], wrap=True),
                        ft.Row([stake_field, odds_field, cashout_field, outcome_field], spacing=12, wrap=True),
                        parlay_section,
                        form_message,
                        save_button,
                    ],
                    spacing=14,
                ),
            ),
        ],
        spacing=20,
    )

    page.add(dashboard)
    refresh_metrics()
    refresh_daily()
    refresh_history()

    if not state.bets:
        load_remote(None)


def _build_summary_cards() -> List[ft.Container]:
    cards: List[ft.Container] = []
    for _ in range(4):
        cards.append(
            ft.Container(
                bgcolor=SURFACE,
                border_radius=16,
                padding=ft.padding.all(16),
                content=ft.Column(
                    [
                        ft.Text("-", size=24, weight=ft.FontWeight.W_700),
                        ft.Text("", color=TEXT_MUTED),
                    ],
                    spacing=4,
                ),
            )
        )
    return cards
