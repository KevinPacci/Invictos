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
from .ui import theme
from .ui.components import build_summary_cards
from .utils.formatting import format_currency, format_full_date, format_month
from .i18n import t

def _show_toast(page: ft.Page, text: str, error: bool = False) -> None:
    page.snack_bar = ft.SnackBar(
        bgcolor=theme.DANGER if error else theme.SURFACE_ALT,
        content=ft.Text(text),
        open=True,
    )
    page.update()


def main(page: ft.Page) -> None:
    theme.configure_page(page)

    api = ApiClient()
    state = AppState(cache.load_cached_bets())
    flush_pending(api, state)

    selected_date = max((bet.event_date for bet in state.as_list()), default=date.today())
    selected_month = selected_date.strftime("%Y-%m")

    date_picker = ft.DatePicker()
    page.overlay.append(date_picker)

    summary_cards = build_summary_cards()
    metrics_row = ft.Row(summary_cards, spacing=12, run_spacing=12, wrap=True)

    selected_date_label = ft.Text(format_full_date(selected_date), size=18, weight=ft.FontWeight.W_600)
    daily_headline = ft.Text("", color=theme.TEXT_MUTED)
    daily_list = ft.Column(spacing=12)
    history_list = ft.Column(spacing=10)

    bet_type_selector = ft.SegmentedButton(
        selected={"single"},
        segments=[
            ft.Segment(value="single", label=ft.Text(t("bet.type.single"))),
            ft.Segment(value="parlay", label=ft.Text(t("bet.type.parlay"))),
        ],
    )

    detail_field = ft.TextField(label=t("form.detail"), width=420)
    stake_field = ft.TextField(label=t("form.stake"), width=160, keyboard_type=ft.KeyboardType.NUMBER)
    odds_field = ft.TextField(label=t("form.odds"), width=160, keyboard_type=ft.KeyboardType.NUMBER)
    cashout_field = ft.TextField(label=t("form.cashout"), width=160, keyboard_type=ft.KeyboardType.NUMBER)
    outcome_field = ft.Dropdown(
        label=t("form.outcome"),
        width=160,
        options=[
            ft.dropdown.Option("acertada", t("bet.status.won")),
            ft.dropdown.Option("fallida", t("bet.status.lost")),
            ft.dropdown.Option("pendiente", t("bet.status.pending")),
        ],
        value="pendiente",
    )

    leg_container = ft.Column(spacing=10)
    parlay_section = ft.Column(
        [
            ft.Text(t("form.parlay.section"), size=14, color=theme.TEXT_MUTED),
            leg_container,
            ft.TextButton(t("form.parlay.add"), icon=ft.Icons.ADD, on_click=lambda e: add_leg_row()),
        ]
    )
    parlay_section.visible = False

    form_message = ft.Text("", color=theme.TEXT_MUTED)
    save_button = ft.FilledButton(t("form.save"), icon=ft.Icons.SAVE)

    def add_leg_row(detail: str = "", odds: str = "") -> None:
        detail_input = ft.TextField(label=t("form.parlay.market"), value=detail, width=320)
        odds_input = ft.TextField(label=t("form.odds"), value=odds, width=120, keyboard_type=ft.KeyboardType.NUMBER)
        remove_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=theme.DANGER)

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
            (summary_cards[0], format_currency(month_metrics.stake_total), t("summary.stake")),
            (summary_cards[1], format_currency(month_metrics.net), t("summary.net")),
            (summary_cards[2], f"{month_metrics.wins}/{month_metrics.count}", t("summary.hits")),
            (summary_cards[3], f"{month_metrics.yield_percent:.1f}%", t("summary.yield")),
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
            daily_headline.value = t(
                "daily.metrics",
                count=metrics.count,
                stake=format_currency(metrics.stake_total),
                gross=format_currency(metrics.return_total),
                net=format_currency(metrics.net),
            )
        else:
            daily_headline.value = t("daily.empty")
        daily_headline.update()

        daily_list.controls.clear()
        if not bets:
            daily_list.controls.append(ft.Text(t("daily.empty"), color=theme.TEXT_MUTED))
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
                    bgcolor=theme.SURFACE,
                    border_radius=12,
                    padding=ft.padding.all(14),
                    content=ft.Column(
                        [
                            ft.Text(format_month(month_key), weight=ft.FontWeight.W_600),
                            ft.Text(f"Neto {format_currency(metrics.net)}", color=theme.ACCENT if metrics.net >= 0 else theme.DANGER),
                            ft.Text(f"Stake {format_currency(metrics.stake_total)}", color=theme.TEXT_MUTED, size=12),
                            ft.Text(f"Yield {metrics.yield_percent:.1f}%", color=theme.TEXT_MUTED, size=12),
                        ],
                        spacing=4,
                    ),
                )
            )
        if not history_list.controls:
            history_list.controls.append(ft.Text(t("history.empty"), color=theme.TEXT_MUTED))
        history_list.update()

    def build_bet_card(bet: Bet) -> ft.Container:
        net_value = bet.net()
        outcome_selector = ft.Dropdown(
            width=160,
            value=bet.outcome,
            options=[
                ft.dropdown.Option("acertada", t("bet.status.won")),
                ft.dropdown.Option("fallida", t("bet.status.lost")),
                ft.dropdown.Option("pendiente", t("bet.status.pending")),
            ],
            on_change=lambda e, bet_id=bet.id: update_outcome(bet_id, e.control.value),
        )
        cashout_input = ft.TextField(
            width=140,
            label=t("form.cashout.label"),
            value=f"{bet.cashout:.2f}" if bet.cashout is not None else "",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_blur=lambda e, bet_id=bet.id: update_cashout(bet_id, e.control.value),
        )
        delete_btn = ft.OutlinedButton(
            text=t("actions.delete"),
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
                            ft.Text(t("bet.type.parlay") if bet.type == "parlay" else t("bet.type.single"), size=12),
                            bgcolor=theme.ACCENT if bet.type == "parlay" else theme.INFO,
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=999,
                        ),
                        ft.Text(bet.detail, size=16, weight=ft.FontWeight.W_600),
                    ],
                    spacing=12,
                ),
                ft.Text(
                    f"Stake {format_currency(bet.stake)} | Cuota {bet.odds:.2f} | "
                    f"Retorno {format_currency(bet.gross_return())} | Neto {format_currency(net_value)}",
                    color=theme.TEXT_MUTED,
                    size=12,
                ),
                ft.Row([outcome_selector, cashout_input, delete_btn], spacing=10, wrap=True),
                legs_section or ft.Container(),
            ],
            spacing=10,
        )
        return ft.Container(bgcolor=theme.SURFACE_ALT, border_radius=12, padding=ft.padding.all(16), content=body)

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
            _show_toast(page, t("toast.delete.offline"))
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
        selected_date_label.value = format_full_date(selected_date)
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
            _show_toast(page, t("toast.sync.fail"), True)
            return
        state.replace_all(remote, datetime.utcnow())
        cache.save_cached_bets(state.as_list())
        _show_toast(page, t("toast.sync.ok"))
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
            form_message.value = t("form.error.detail")
            form_message.color = theme.DANGER
            form_message.update()
            return
        try:
            stake = float(stake_field.value)
            odds_val = float(odds_field.value)
        except (TypeError, ValueError):
            form_message.value = t("form.error.stake_odds")
            form_message.color = theme.DANGER
            form_message.update()
            return
        if stake <= 0 or odds_val <= 1:
            form_message.value = t("form.error.positive")
            form_message.color = theme.DANGER
            form_message.update()
            return
        cashout = None
        if cashout_field.value:
            try:
                cashout = float(cashout_field.value)
            except ValueError:
                form_message.value = t("form.error.cashout")
                form_message.color = theme.DANGER
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
                form_message.value = t("form.error.parlay")
                form_message.color = theme.DANGER
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
            _show_toast(page, t("form.offline"))
        except ApiClientError as error:
            form_message.value = str(error)
            form_message.color = theme.DANGER
            form_message.update()
            return
        cache.save_cached_bets(state.as_list())
        refresh_metrics()
        refresh_daily()
        refresh_history()
        reset_form()
        form_message.value = t("form.success")
        form_message.color = theme.ACCENT
        form_message.update()

    save_button.on_click = submit_form

    toolbar = ft.Row(
        [
            ft.Row(
                [
                    ft.TextButton(t("toolbar.today"), on_click=lambda e: set_selected_date(date.today())),
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip=t("toolbar.previous"), on_click=lambda e: shift_day(-1)),
                    ft.IconButton(icon=ft.Icons.ARROW_FORWARD, tooltip=t("toolbar.next"), on_click=lambda e: shift_day(1)),
                    ft.TextButton(t("toolbar.pick_date"), icon=ft.Icons.CALENDAR_MONTH, on_click=open_date_picker),
                ],
                spacing=6,
            ),
            ft.FilledButton(t("toolbar.sync"), icon=ft.Icons.CLOUD_SYNC, on_click=load_remote),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    dashboard = ft.Column(
        [
            ft.Text(t("app.title"), size=26, weight=ft.FontWeight.W_700),
            ft.Text(t("app.subtitle"), color=theme.TEXT_MUTED),
            metrics_row,
            toolbar,
            selected_date_label,
            daily_headline,
            ft.Container(bgcolor=theme.SURFACE, border_radius=14, padding=ft.padding.all(16), content=daily_list),
            ft.Text(t("history.title"), size=20, weight=ft.FontWeight.W_600),
            ft.Container(bgcolor=theme.SURFACE_ALT, border_radius=14, padding=ft.padding.all(16), content=history_list),
            ft.Container(
                bgcolor=theme.SURFACE,
                border_radius=16,
                padding=ft.padding.all(20),
                content=ft.Column(
                    [
                        ft.Text(t("form.title"), size=18, weight=ft.FontWeight.W_600),
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















