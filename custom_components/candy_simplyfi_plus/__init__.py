"""Candy Simply-Fi Plus - integrazione locale Candy simply-Fi per lavastoviglie."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CandyApi
from .const import CONF_KEY, CONF_MODE, DOMAIN
from .coordinator import CandyCoordinator
from .cycle import CycleTracker

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

CARD_FILE = Path(__file__).parent / "frontend" / "candy-simplyfi-plus-card.js"
CARD_URL = "/candy_simplyfi_plus/candy-simplyfi-plus-card.js"

type CandyConfigEntry = ConfigEntry[CandyCoordinator]


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve la card e la carica in tutte le dashboard (una sola volta)."""
    if hass.data.get(f"{DOMAIN}_card"):
        return
    hass.data[f"{DOMAIN}_card"] = True
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(CARD_URL, str(CARD_FILE), False)]
        )
    except RuntimeError:
        _LOGGER.debug("Percorso della card già registrato")
    # il ?v= cambia a ogni versione, così il browser non usa la copia vecchia
    version = int(CARD_FILE.stat().st_mtime)
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")


async def _async_reload(hass: HomeAssistant, entry: CandyConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: CandyConfigEntry) -> bool:
    await _async_register_card(hass)
    api = CandyApi(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_KEY),
        entry.data.get(CONF_MODE),
    )
    coordinator = CandyCoordinator(hass, entry, api)
    tracker = CycleTracker(hass, entry, coordinator)
    await tracker.async_load()
    coordinator.tracker = tracker
    await coordinator.async_config_entry_first_refresh()
    tracker.async_start()

    # Salva la modalità di lettura e la chiave rilevate
    if api.mode and (entry.data.get(CONF_MODE) != api.mode or entry.data.get(CONF_KEY) != api.key):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_MODE: api.mode, CONF_KEY: api.key}
        )
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CandyConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and entry.runtime_data.tracker is not None:
        await entry.runtime_data.tracker.async_stop()
    return unloaded
