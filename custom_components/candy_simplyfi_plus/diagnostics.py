"""Diagnostica scaricabile (Impostazioni → Dispositivi e servizi → ⋮ → Scarica diagnostica)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from . import CandyConfigEntry
from .const import CONF_KEY, DOMAIN

TO_REDACT = {CONF_KEY, CONF_HOST, "unique_id", "title", "configuration_url"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: CandyConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    tracker = coordinator.tracker
    integration = await async_get_integration(hass, DOMAIN)
    return {
        "versione": str(integration.version),
        "voce": async_redact_data(
            {"title": entry.title, "unique_id": entry.unique_id, "data": dict(entry.data)},
            TO_REDACT,
        ),
        "opzioni": dict(entry.options),
        "modo_lettura": coordinator.api.mode,
        "ultima_lettura_ok": coordinator.last_update_success,
        "intervallo_s": coordinator.update_interval.total_seconds() if coordinator.update_interval else None,
        "dati": dict(coordinator.data or {}),
        "cicli": tracker.data if tracker is not None else None,
    }
