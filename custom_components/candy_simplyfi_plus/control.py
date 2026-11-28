"""Comandi a distanza: programma, opzioni, partenza ritardata, avvio e arresto.

Funzionano solo con il controllo remoto attivato dal pannello della lavastoviglie
(StatoWiFi = 1): è la conferma di chi è davanti all'elettrodomestico.
"""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.restore_state import RestoreEntity

from .api import CandyError, CandyReadOnlyError
from .const import (
    DOMAIN, F_PROGRAM, F_SMART_DOOR, F_TABS, MAX_DELAY_HOURS, NO_SMART_DOOR, NO_TABS,
    PROGRAM_ORDER, PROGRAMS,
)
from .entity import CandyEntity
from .state import is_delayed, is_remote_enabled, is_running

_LOGGER = logging.getLogger(__name__)

KEY_TO_CODE = {PROGRAMS[c]: c for c in PROGRAM_ORDER}
REFRESH_AFTER = 5  # secondi: poi il modulo WiFi può non rispondere per 1–3 minuti


def start_params(code: str, tabs: bool, smart_door: bool, delay_hours: float) -> list[tuple[str, str]]:
    """Comando di avvio completo: programma e opzioni vanno inviati insieme a StartStop=1."""
    halves = max(0, min(int(round(delay_hours * 2)), int(MAX_DELAY_HOURS * 2)))
    return [
        ("DelayStart", str(halves)),            # in passi di 30 minuti (si rilegge in minuti)
        ("ExtraDry", "0"),
        ("OpenDoorOpt", "1" if smart_door and code not in NO_SMART_DOOR else "0"),
        ("TreinUno", "1" if tabs and code not in NO_TABS else "0"),
        ("Eco", "0"),
        ("Program", code),
        ("MetaCarico", "0"),
        ("OpzProg", "0"),
        ("w1", "1"),
        ("StartStop", "1"),
    ]


class ControlSettings:
    """Scelte per il prossimo avvio, condivise dalle entità di comando."""

    def __init__(self) -> None:
        self.program: str | None = None   # chiave, es. "eco"
        self.tabs: bool | None = None
        self.smart_door: bool | None = None
        self.delay_hours: float = 0.0


def _settings(coordinator) -> ControlSettings:
    if getattr(coordinator, "control", None) is None:
        coordinator.control = ControlSettings()
    return coordinator.control


async def _send(entity: CandyEntity, params: list[tuple[str, str]]) -> None:
    coordinator = entity.coordinator
    try:
        await coordinator.api.async_send_command(params)
    except CandyReadOnlyError as err:
        raise HomeAssistantError(translation_domain=DOMAIN, translation_key="read_only") from err
    except CandyError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="command_failed",
            translation_placeholders={"error": str(err)},
        ) from err

    async def _refresh(_now) -> None:
        await coordinator.async_request_refresh()

    async_call_later(entity.hass, REFRESH_AFTER, _refresh)


# ----------------------------------------------------------------------
class RemoteControlSensor(CandyEntity, BinarySensorEntity):
    """Controllo remoto attivo sul pannello."""

    _attr_icon = "mdi:remote"

    def __init__(self, c) -> None:
        super().__init__(c, "controllo_remoto")

    @property
    def is_on(self) -> bool:
        return is_remote_enabled(self.coordinator.data)


class ProgramSelect(CandyEntity, SelectEntity, RestoreEntity):
    """Programma da avviare."""

    _attr_icon = "mdi:format-list-checks"
    _attr_options = [PROGRAMS[c] for c in PROGRAM_ORDER]

    def __init__(self, c) -> None:
        super().__init__(c, "programma_avvio")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        s = _settings(self.coordinator)
        last = await self.async_get_last_state()
        if s.program is None and last is not None and last.state in self._attr_options:
            s.program = last.state
        if s.program is None:
            # all'inizio propone il programma scelto sul pannello
            s.program = PROGRAMS.get(self.field(F_PROGRAM) or "", "eco")

    @property
    def available(self) -> bool:
        return True

    @property
    def current_option(self) -> str | None:
        return _settings(self.coordinator).program

    async def async_select_option(self, option: str) -> None:
        _settings(self.coordinator).program = option
        self.async_write_ha_state()


class _OptionSwitch(CandyEntity, SwitchEntity, RestoreEntity):
    _field = ""
    _attr_name_key = ""

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        s = _settings(self.coordinator)
        if getattr(s, self._attr_name_key) is None:
            last = await self.async_get_last_state()
            if last is not None and last.state in ("on", "off"):
                value = last.state == "on"
            else:
                value = self.field(self._field) == "1"   # come impostato sulla macchina
            setattr(s, self._attr_name_key, value)

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return bool(getattr(_settings(self.coordinator), self._attr_name_key))

    async def async_turn_on(self, **kwargs) -> None:
        setattr(_settings(self.coordinator), self._attr_name_key, True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        setattr(_settings(self.coordinator), self._attr_name_key, False)
        self.async_write_ha_state()


class TabsSwitch(_OptionSwitch):
    _attr_icon = "mdi:pill"
    _field = F_TABS
    _attr_name_key = "tabs"

    def __init__(self, c) -> None:
        super().__init__(c, "avvio_tabs")


class SmartDoorSwitch(_OptionSwitch):
    _attr_icon = "mdi:door-sliding-open"
    _field = F_SMART_DOOR
    _attr_name_key = "smart_door"

    def __init__(self, c) -> None:
        super().__init__(c, "avvio_smart_door")


class DelayNumber(CandyEntity, NumberEntity, RestoreEntity):
    """Partenza ritardata per il prossimo avvio (0 = subito)."""

    _attr_icon = "mdi:timer-play-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_DELAY_HOURS
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_mode = NumberMode.BOX

    def __init__(self, c) -> None:
        super().__init__(c, "ritardo_avvio")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            try:
                _settings(self.coordinator).delay_hours = float(last.state)
            except ValueError:
                pass

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float:
        return _settings(self.coordinator).delay_hours

    async def async_set_native_value(self, value: float) -> None:
        _settings(self.coordinator).delay_hours = round(value * 2) / 2
        self.async_write_ha_state()


class StartButton(CandyEntity, ButtonEntity):
    """Avvia il programma scelto, con le opzioni e il ritardo impostati."""

    _attr_icon = "mdi:play-circle"

    def __init__(self, c) -> None:
        super().__init__(c, "avvia")

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return is_remote_enabled(data) and not is_running(data) and not is_delayed(data)

    async def async_press(self) -> None:
        s = _settings(self.coordinator)
        code = KEY_TO_CODE.get(s.program or "", "P8")
        await _send(self, start_params(code, bool(s.tabs), bool(s.smart_door), s.delay_hours))


class StopButton(CandyEntity, ButtonEntity):
    """Annulla il programma in corso o la partenza ritardata (Reset=1)."""

    _attr_icon = "mdi:stop-circle"

    def __init__(self, c) -> None:
        super().__init__(c, "ferma")

    @property
    def available(self) -> bool:
        return is_remote_enabled(self.coordinator.data)

    async def async_press(self) -> None:
        await _send(self, [("Reset", "1")])
