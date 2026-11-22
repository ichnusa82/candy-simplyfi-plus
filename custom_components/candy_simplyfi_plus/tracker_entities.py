"""Entità basate sul tracker dei cicli: energia, costo, statistiche, filtro."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory, UnitOfEnergy
from homeassistant.util import dt as dt_util

from .cycle import CycleTracker
from .entity import CandyEntity


def _ts(value: str | None) -> datetime | None:
    return dt_util.parse_datetime(value) if value else None


class TrackerEntity(CandyEntity):
    """Entità che si aggiorna quando cambia il tracker dei cicli."""

    def __init__(self, coordinator, tracker: CycleTracker, key: str) -> None:
        super().__init__(coordinator, key)
        self.tracker = tracker

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.tracker.add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return True


# ----------------------------------------------------------------------
# Energia e costo del ciclo
# ----------------------------------------------------------------------
class CycleEnergySensor(TrackerEntity, SensorEntity):
    """kWh del ciclo in corso, o dell'ultimo ciclo terminato."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:lightning-bolt-circle"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "energia_ciclo")

    @property
    def native_value(self) -> float | None:
        kwh = self.tracker.cycle.get("kwh")
        return None if kwh is None else round(kwh, 3)

    @property
    def extra_state_attributes(self) -> dict:
        c = self.tracker.cycle
        return {
            "programma": c.get("programma"),
            "inizio": c.get("inizio"),
            "fine": c.get("fine"),
            "durata_min": c.get("durata_min"),
            "in_corso": c.get("in_corso"),
            "esito": c.get("esito"),
            "sensore_sorgente": self.tracker.power_entity,
        }


class CycleCostSensor(TrackerEntity, SensorEntity):
    """Costo del ciclo in corso, o dell'ultimo ciclo terminato."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:cash"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "costo_ciclo")

    @property
    def native_unit_of_measurement(self) -> str:
        return self.hass.config.currency

    @property
    def native_value(self) -> float | None:
        cost = self.tracker.cycle.get("costo")
        return None if cost is None else round(cost, 3)

    @property
    def extra_state_attributes(self) -> dict:
        c = self.tracker.cycle
        return {
            "programma": c.get("programma"),
            "energia_kwh": c.get("kwh"),
            "prezzo_attuale_kwh": self.tracker.price(),
            "in_corso": c.get("in_corso"),
        }


# ----------------------------------------------------------------------
# Statistiche
# ----------------------------------------------------------------------
class WashCountSensor(TrackerEntity, SensorEntity):
    """Numero di lavaggi completati, con il dettaglio per programma."""

    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "lavaggi_totali")

    @property
    def native_value(self) -> int:
        return self.tracker.stats["lavaggi"]

    @property
    def extra_state_attributes(self) -> dict:
        progs = self.tracker.stats["programmi"]
        return {name: p["lavaggi"] for name, p in sorted(progs.items(), key=lambda i: -i[1]["lavaggi"])}


class LastWashSensor(TrackerEntity, SensorEntity):
    """Data e ora di fine dell'ultimo lavaggio."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:history"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "ultimo_lavaggio")

    @property
    def native_value(self) -> datetime | None:
        last = self.tracker.stats.get("ultimo") or {}
        return _ts(last.get("fine"))

    @property
    def extra_state_attributes(self) -> dict:
        last = self.tracker.stats.get("ultimo") or {}
        return {
            "programma": last.get("programma"),
            "inizio": last.get("inizio"),
            "durata_min": last.get("durata_min"),
            "energia_kwh": last.get("kwh"),
            "costo": None if last.get("costo") is None else round(last["costo"], 2),
            "esito": last.get("esito"),
        }


class AverageEnergySensor(TrackerEntity, SensorEntity):
    """Consumo medio per lavaggio, in generale e per programma."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:chart-bar"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "consumo_medio")

    @property
    def native_value(self) -> float | None:
        s = self.tracker.stats
        return round(s["kwh"] / s["misurati"], 3) if s["misurati"] else None

    @property
    def extra_state_attributes(self) -> dict:
        attrs = {}
        for name, p in sorted(self.tracker.stats["programmi"].items()):
            if p["misurati"]:
                attrs[name] = round(p["kwh"] / p["misurati"], 2)
        s = self.tracker.stats
        attrs["energia_totale_kwh"] = round(s["kwh"], 2)
        if self.tracker.has_price:
            attrs["costo_totale"] = round(s["costo"], 2)
        attrs["lavaggi_misurati"] = s["misurati"]
        return attrs


# ----------------------------------------------------------------------
# Manutenzione filtro
# ----------------------------------------------------------------------
class FilterCountSensor(TrackerEntity, SensorEntity):
    """Lavaggi completati dall'ultima pulizia del filtro."""

    _attr_icon = "mdi:air-filter"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "lavaggi_filtro")

    @property
    def native_value(self) -> int:
        return self.tracker.filter["lavaggi"]

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "ultima_pulizia": self.tracker.filter.get("ultima_pulizia"),
            "pulizia_ogni": self.tracker.filter_every or None,
        }


class FilterDueSensor(TrackerEntity, BinarySensorEntity):
    """Acceso quando è ora di pulire il filtro."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "pulizia_filtro")

    @property
    def is_on(self) -> bool:
        every = self.tracker.filter_every
        return bool(every) and self.tracker.filter["lavaggi"] >= every


class FilterCleanedButton(TrackerEntity, ButtonEntity):
    """Da premere dopo aver pulito il filtro: azzera il contatore."""

    _attr_icon = "mdi:air-filter"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator, tracker) -> None:
        super().__init__(coordinator, tracker, "filtro_pulito")

    async def async_press(self) -> None:
        self.tracker.reset_filter()
