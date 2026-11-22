"""Sensori Candy Simply-Fi Plus."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import CandyConfigEntry
from .const import (
    F_DELAY, F_ERROR, F_PROGRAM, F_REMAINING, F_START_STOP, F_STATE, ONLINE,
    ERROR_OPTIONS, ERRORS, F_PHASE, F_SOFTENER, PHASES, PROGRAM_INFO, PROGRAM_OPTIONS, PROGRAMS,
    STATE_OPTIONS, STATES,
)
from .const import CONF_POWER
from .entity import CandyEntity
from .power import PowerSensor
from .tracker_entities import (
    AverageEnergySensor, CycleCostSensor, CycleEnergySensor, FilterCountSensor,
    LastWashSensor, WashCountSensor,
)


def _int(value: str | None) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant, entry: CandyConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    tracker = c.tracker
    stats = [WashCountSensor(c, tracker), LastWashSensor(c, tracker), FilterCountSensor(c, tracker)]
    if power := entry.options.get(CONF_POWER):
        stats += [PowerSensor(entry, power), CycleEnergySensor(c, tracker), AverageEnergySensor(c, tracker)]
        if tracker.has_price:
            stats.append(CycleCostSensor(c, tracker))
    async_add_entities(stats)
    async_add_entities([
        StateSensor(c), ProgramSensor(c), RemainingSensor(c), EndTimeSensor(c),
        DelaySensor(c), StartTimeSensor(c), ProgressSensor(c), SoftenerSensor(c), ErrorSensor(c), RawSensor(c),
    ])


class StateSensor(CandyEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATE_OPTIONS
    _attr_icon = "mdi:dishwasher"

    def __init__(self, c) -> None:
        super().__init__(c, "stato")

    @property
    def native_value(self) -> str:
        if not self.online:
            return "off"
        if self.is_delayed:
            return "delayed"
        if self.is_running:
            return PHASES.get(self.field(F_PHASE) or "", "running")
        if self.coordinator.tracker is not None and self.coordinator.tracker.is_paused:
            return "paused"
        return STATES.get(self.field(F_STATE) or "", "unknown")

    @property
    def extra_state_attributes(self) -> dict:
        return {"codice": self.field(F_STATE), "fase": self.field(F_PHASE)}


class ProgramSensor(CandyEntity, SensorEntity):
    _attr_icon = "mdi:format-list-numbered"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = PROGRAM_OPTIONS

    def __init__(self, c) -> None:
        super().__init__(c, "programma")

    @property
    def native_value(self) -> str | None:
        if not self.online:
            return None
        code = self.field(F_PROGRAM)
        if code in (None, "", "P0"):
            return "none"
        return PROGRAMS.get(code, "other")

    @property
    def extra_state_attributes(self) -> dict:
        code = self.field(F_PROGRAM)
        temp, minutes = PROGRAM_INFO.get(code or "", (None, None))
        return {"codice": code, "temperatura": temp, "durata_media_min": minutes}


class RemainingSensor(CandyEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-sand"

    def __init__(self, c) -> None:
        super().__init__(c, "tempo_residuo")

    @property
    def native_value(self) -> int | None:
        if not self.online or self.field(F_STATE) == "5":
            return 0
        return _int(self.field(F_REMAINING))


class _StableTime:
    """Orario calcolato che non 'balla' di un minuto a ogni lettura."""

    def __init__(self) -> None:
        self._last: datetime | None = None

    def update(self, minutes: int | None) -> datetime | None:
        if minutes is None:
            self._last = None
            return None
        new = (dt_util.now() + timedelta(minutes=minutes)).replace(second=0, microsecond=0)
        if self._last is None or abs((new - self._last).total_seconds()) > 120:
            self._last = new
        return self._last


class EndTimeSensor(CandyEntity, SensorEntity):
    """Orario previsto di fine ciclo (durante il lavaggio o in attesa di partenza)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-end"

    def __init__(self, c) -> None:
        super().__init__(c, "fine_ciclo")
        self._time = _StableTime()

    @property
    def native_value(self) -> datetime | None:
        minutes = None
        if self.online:
            remaining = _int(self.field(F_REMAINING))
            delay = _int(self.field(F_DELAY)) or 0
            if remaining is not None:
                if self.is_running:
                    minutes = remaining
                elif self.is_delayed:
                    minutes = delay + remaining
        return self._time.update(minutes)


class StartTimeSensor(CandyEntity, SensorEntity):
    """Orario di partenza quando è impostata la partenza ritardata."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-start"

    def __init__(self, c) -> None:
        super().__init__(c, "partenza_alle")
        self._time = _StableTime()

    @property
    def native_value(self) -> datetime | None:
        minutes = None
        if self.is_delayed:
            delay = _int(self.field(F_DELAY)) or 0
            if delay > 0:
                minutes = delay
        return self._time.update(minutes)


class DelaySensor(CandyEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-play-outline"

    def __init__(self, c) -> None:
        super().__init__(c, "partenza_ritardata")

    @property
    def native_value(self) -> int | None:
        return _int(self.field(F_DELAY)) if self.online else 0


class ProgressSensor(CandyEntity, SensorEntity):
    """Avanzamento del lavaggio in %: il totale è il tempo residuo letto alla partenza."""

    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:progress-clock"

    def __init__(self, c) -> None:
        super().__init__(c, "avanzamento")
        self._total: int | None = None

    @property
    def native_value(self) -> int | None:
        if not self.is_running:
            self._total = None
            return 100 if self.online and self.field(F_STATE) == "5" else None
        remaining = _int(self.field(F_REMAINING))
        if remaining is None:
            return None
        if self._total is None or remaining > self._total:
            # durata nominale del programma (manuale), utile se HA si riavvia a ciclo iniziato
            nominal = PROGRAM_INFO.get(self.field(F_PROGRAM) or "", (None, None))[1]
            self._total = max(remaining, nominal or 0, 1)
        return max(0, min(100, round((self._total - remaining) * 100 / self._total)))


class SoftenerSensor(CandyEntity, SensorEntity):
    """Livello del decalcificatore impostato sulla macchina (S0-S7)."""

    _attr_icon = "mdi:water-opacity"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "decalcificatore")

    @property
    def native_value(self) -> str | None:
        if not self.online:
            return None
        level = _int(self.field(F_SOFTENER))
        return None if level is None else f"S{level}"


class ErrorSensor(CandyEntity, SensorEntity):
    _attr_icon = "mdi:alert-circle-outline"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ERROR_OPTIONS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "errore")

    @property
    def native_value(self) -> str | None:
        if not self.online:
            return None
        code = self.field(F_ERROR)
        if code is None:
            return None
        return ERRORS.get(code, "other")

    @property
    def extra_state_attributes(self) -> dict:
        return {"codice": self.field(F_ERROR)}


class RawSensor(CandyEntity, SensorEntity):
    """Tutti i campi grezzi come attributi: utile per capire i codici del tuo modello."""

    _attr_icon = "mdi:code-json"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "dati_grezzi")

    @property
    def native_value(self) -> str:
        return "online" if self.online else "offline"

    @property
    def extra_state_attributes(self) -> dict:
        return {k: v for k, v in self.coordinator.data.items() if k != ONLINE}
