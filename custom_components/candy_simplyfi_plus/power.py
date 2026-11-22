"""Entità di consumo basate su un sensore di potenza esterno (presa smart)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfPower
from homeassistant.core import Event, EventStateChangedData, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD
from .cycle import power_watts
from .entity import candy_device_info


class _PowerFollower(Entity):
    """Segue un sensore di potenza esterno."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, source: str, key: str) -> None:
        self._source = source
        self._watts: float | None = None
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = candy_device_info(entry)
        self._attr_extra_state_attributes = {"sensore_sorgente": source}

    async def async_added_to_hass(self) -> None:
        self._watts = power_watts(self.hass.states.get(self._source))

        @callback
        def _changed(event: Event[EventStateChangedData]) -> None:
            self._watts = power_watts(event.data["new_state"])
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source], _changed)
        )

    @property
    def available(self) -> bool:
        return self._watts is not None


class PowerSensor(_PowerFollower, SensorEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_suggested_display_precision = 1

    def __init__(self, entry: ConfigEntry, source: str) -> None:
        super().__init__(entry, source, "potenza")

    @property
    def native_value(self) -> float | None:
        return self._watts


class ConsumingSensor(_PowerFollower, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.POWER

    def __init__(self, entry: ConfigEntry, source: str) -> None:
        super().__init__(entry, source, "in_consumo")
        self._threshold = float(entry.options.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD))
        self._attr_extra_state_attributes = {
            "sensore_sorgente": source,
            "soglia_w": self._threshold,
        }

    @property
    def is_on(self) -> bool | None:
        if self._watts is None:
            return None
        return self._watts > self._threshold
