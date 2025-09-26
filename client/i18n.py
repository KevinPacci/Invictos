from __future__ import annotations

from typing import Dict

DEFAULT_LOCALE = "es"

_STRINGS: Dict[str, Dict[str, str]] = {
    "es": {
        "app.title": "Invictos Bet Tracker",
        "app.subtitle": "Seguimiento modular de tus apuestas con sincronización",
        "nav.dashboard": "Panel",
        "nav.history": "Historial",
        "nav.new_bet": "Registrar",
        "bet.type.single": "Sencilla",
        "bet.type.parlay": "Parlay",
        "bet.status.won": "Acertada",
        "bet.status.lost": "Fallida",
        "bet.status.pending": "Pendiente",
        "summary.stake": "Apostado",
        "summary.net": "Neto",
        "summary.hits": "Aciertos",
        "summary.yield": "Yield",
        "daily.title": "Detalle del día",
        "daily.empty": "Agrega una apuesta para este día",
        "daily.metrics": "{count} apuestas | Apostado {stake} | Retorno {gross} | Neto {net}",
        "history.title": "Historial",
        "history.empty": "Historial vacío aún",
        "form.title": "Registrar nueva apuesta",
        "form.detail": "Detalle",
        "form.stake": "Stake",
        "form.odds": "Cuota",
        "form.cashout": "Retorno / cashout",
        "form.cashout.label": "Retorno",
        "form.outcome": "Estado",
        "form.parlay.add": "Agregar selección",
        "form.parlay.section": "Selecciones",
        "form.parlay.market": "Mercado",
        "form.save": "Guardar",
        "form.error.detail": "Describe la apuesta",
        "form.error.stake_odds": "Stake/cuota inválidos",
        "form.error.positive": "Stake y cuota deben ser > 0",
        "form.error.cashout": "Cashout inválido",
        "form.error.parlay": "Un parlay necesita 2+ selecciones",
        "form.success": "Apuesta guardada",
        "form.offline": "Sin conexión. Guardado localmente",
        "toast.sync.ok": "Sincronización completa",
        "toast.sync.fail": "Sin conexión con el backend",
        "toast.delete.offline": "Eliminado localmente, pendiente de sincronización",
        "toolbar.today": "Hoy",
        "toolbar.previous": "Anterior",
        "toolbar.next": "Siguiente",
        "toolbar.pick_date": "Elegir fecha",
        "toolbar.sync": "Sincronizar",
        "actions.delete": "Eliminar",
    }
}


def t(key: str, *, locale: str = DEFAULT_LOCALE, **kwargs: str) -> str:
    bundle = _STRINGS.get(locale, _STRINGS[DEFAULT_LOCALE])
    text = bundle.get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


__all__ = ["t", "DEFAULT_LOCALE"]
