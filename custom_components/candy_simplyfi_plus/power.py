"""Entità di consumo basate su un sensore di potenza esterno (presa smart)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.sensor import (
    RestoreSensor, SensorDeviceClass, SensorEntity, SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import Event, EventStateChangedData, State, callback
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_state_change_event

from homeassistant.util import dt as dt_util

from .const import CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD, F_PROGRAM, PROGRAMS
from .entity import CandyEntity, candy_device_info


def power_watts(state: State | None) -> float | None:
    """Valore in W del sensore sorgente (converte kW e mW)."""
    if state is None or state.state in ("unknown", "unavailable", ""):
        return None
    try:
        value = float(state.state)
    except ValueError:
        return None
    unit = (state.attributes.get("unit_of_measurement") or "W").strip()
    if unit == "kW":
        value *= 1000
    elif unit == "mW":
        value /= 1000
    return round(value, 1)


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


class CycleEnergySensor(CandyEntity, RestoreSensor):
    """Energia consumata dal ciclo in corso (o dall'ultimo ciclo terminato)."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:lightning-bolt-circle"

    def __init__(self, coordinator, source: str) -> None:
        super().__init__(coordinator, "energia_ciclo")
        self._source = source
        self._kwh: float | None = None
        self._watts: float | None = None
        self._last_ts = dt_util.utcnow()
        self._running = False
        self._info: dict = {}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_sensor_data()
        if last is not None and last.native_value is not None:
            try:
                self._kwh = float(last.native_value)
            except (TypeError, ValueError):
                self._kwh = None
        if (state := await self.async_get_last_state()) is not None:
            self._info = {
                k: v for k, v in state.attributes.items()
                if k in ("programma", "inizio", "fine", "durata_min", "in_corso")
            }
            self._running = bool(self._info.get("in_corso"))
        self._watts = power_watts(self.hass.states.get(self._source))
        self._last_ts = dt_util.utcnow()

        @callback
        def _changed(event: Event[EventStateChangedData]) -> None:
            self._accumulate()
            self._watts = power_watts(event.data["new_state"])
            self.async_write_ha_state()

        self.async_on_remove(
            async_track_state_change_event(self.hass, [self._source], _changed)
        )

    def _accumulate(self) -> None:
        """Somma l'energia dall'ultima lettura (potenza costante nel frattempo)."""
        now = dt_util.utcnow()
        if self._running and self._watts is not None:
            hours = (now - self._last_ts).total_seconds() / 3600
            if 0 < hours < 1:  # salta i buchi lunghi (es. riavvio di HA)
                self._kwh = (self._kwh or 0.0) + self._watts * hours / 1000
        self._last_ts = now

    @callback
    def _handle_coordinator_update(self) -> None:
        running = self.is_running
        now = dt_util.now()
        if running and not self._running:
            # inizio ciclo: azzera
            self._kwh = 0.0
            self._last_ts = dt_util.utcnow()
            code = self.field(F_PROGRAM)
            self._info = {
                "programma": PROGRAMS.get(code or "", code),
                "inizio": now.isoformat(timespec="minutes"),
                "fine": None,
                "durata_min": None,
                "in_corso": True,
            }
        elif running:
            self._accumulate()
        elif self._running:
            # fine ciclo: congela il totale
            self._accumulate()
            self._info["fine"] = now.isoformat(timespec="minutes")
            self._info["in_corso"] = False
            try:
                start = dt_util.parse_datetime(self._info.get("inizio") or "")
                if start is not None:
                    self._info["durata_min"] = round((now - start).total_seconds() / 60)
            except (TypeError, ValueError):
                pass
        self._running = running
        if not running:
            self._last_ts = dt_util.utcnow()
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float | None:
        return None if self._kwh is None else round(self._kwh, 3)

    @property
    def extra_state_attributes(self) -> dict:
        return {**self._info, "sensore_sorgente": self._source}
