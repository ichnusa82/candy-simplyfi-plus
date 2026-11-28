"""Pulsanti: Filtro pulito, Avvia, Ferma."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .control import StartButton, StopButton
from .tracker_entities import FilterCleanedButton


async def async_setup_entry(
    hass: HomeAssistant, entry: CandyConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities([FilterCleanedButton(c, c.tracker), StartButton(c), StopButton(c)])
