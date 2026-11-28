"""Interpretazione dello stato letto dalla lavastoviglie (codici verificati sul CDIMN 4D622PBE)."""
from __future__ import annotations

from .const import F_DELAY, F_STATE, F_WIFI, ONLINE


def delay_minutes(data: dict) -> int:
    try:
        return int(data.get(F_DELAY) or 0)
    except (TypeError, ValueError):
        return 0


def is_online(data: dict | None) -> bool:
    return bool(data and data.get(ONLINE))


def is_delayed(data: dict | None) -> bool:
    """Partenza ritardata in attesa: StatoDWash 3 con DelayStart > 0."""
    return is_online(data) and data.get(F_STATE) == "3" and delay_minutes(data) > 0


def is_running(data: dict | None) -> bool:
    """In lavaggio: StatoDWash 3 senza ritardo (StartStop resta 0 mentre lava)."""
    if not is_online(data) or is_delayed(data):
        return False
    # StartStop non basta: dopo un avvio da remoto resta a 1 anche a lavaggio finito
    return data.get(F_STATE) == "3"


def is_finished(data: dict | None) -> bool:
    return is_online(data) and data.get(F_STATE) == "5"


def is_remote_enabled(data: dict | None) -> bool:
    """Controllo remoto attivo sul pannello (StatoWiFi = 1)."""
    return is_online(data) and data.get(F_WIFI) == "1"
