"""Entità base."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ONLINE
from .coordinator import CandyCoordinator
from .state import is_delayed, is_running


def candy_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Dispositivo unico a cui appartengono tutte le entità."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Lavastoviglie Candy",
        manufacturer="Candy",
        model="Simply-Fi Plus",
        configuration_url=f"http://{entry.data[CONF_HOST]}/http-read.json?encrypted=1",
    )


class CandyEntity(CoordinatorEntity[CandyCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: CandyCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = candy_device_info(entry)

    @property
    def online(self) -> bool:
        return bool(self.coordinator.data.get(ONLINE))

    def field(self, name: str) -> str | None:
        return self.coordinator.data.get(name)

    @property
    def is_delayed(self) -> bool:
        return is_delayed(self.coordinator.data)

    @property
    def is_running(self) -> bool:
        return is_running(self.coordinator.data)
