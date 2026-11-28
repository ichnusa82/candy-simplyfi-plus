"""Sensori binari Candy Simply-Fi Plus."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CandyConfigEntry
from .const import (
    F_DOOR, F_RINSE, F_SALT, F_SMART_DOOR, F_START_STOP, F_TABS, F_BEEP, F_MEMO,
)
from .const import CONF_POWER
from .entity import CandyEntity
from .power import ConsumingSensor
from .control import RemoteControlSensor
from .tracker_entities import FilterDueSensor

# (chiave, campo JSON, device_class, icona, categoria)
FLAGS = [
    ("porta", F_DOOR, BinarySensorDeviceClass.DOOR, None, None),
    ("manca_sale", F_SALT, BinarySensorDeviceClass.PROBLEM, "mdi:shaker-outline", None),
    ("manca_brillantante", F_RINSE, BinarySensorDeviceClass.PROBLEM, "mdi:water-alert", None),
    ("tabs", F_TABS, None, "mdi:pill", None),
    ("smart_door", F_SMART_DOOR, None, "mdi:door-sliding-open", None),
    ("segnali_acustici", F_BEEP, None, "mdi:volume-high", EntityCategory.DIAGNOSTIC),
    ("funzione_memo", F_MEMO, None, "mdi:content-save-outline", EntityCategory.DIAGNOSTIC),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: CandyConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    entities: list[BinarySensorEntity] = [OnlineSensor(c), RunningSensor(c)]
    entities += [FlagSensor(c, *f) for f in FLAGS]
    entities.append(FilterDueSensor(c, c.tracker))
    entities.append(RemoteControlSensor(c))
    if power := entry.options.get(CONF_POWER):
        entities.append(ConsumingSensor(entry, power))
    async_add_entities(entities)


class OnlineSensor(CandyEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, c) -> None:
        super().__init__(c, "online")

    @property
    def is_on(self) -> bool:
        return self.online


class RunningSensor(CandyEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, c) -> None:
        super().__init__(c, "in_funzione")

    @property
    def is_on(self) -> bool:
        # resta acceso anche se si apre la porta a metà lavaggio
        tracker = self.coordinator.tracker
        # e anche se il modulo WiFi sparisce per qualche minuto
        return self.is_running or (
            tracker is not None and (tracker.is_paused or tracker.is_unreachable)
        )


class FlagSensor(CandyEntity, BinarySensorEntity):
    def __init__(self, c, key, field, device_class, icon, category) -> None:
        super().__init__(c, key)
        self._field = field
        self._attr_device_class = device_class
        if icon:
            self._attr_icon = icon
        self._attr_entity_category = category

    @property
    def is_on(self) -> bool | None:
        if not self.online:
            return None
        value = self.field(self._field)
        return None if value is None else value not in ("0", "")
