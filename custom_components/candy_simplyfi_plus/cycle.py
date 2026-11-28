"""Segue i cicli di lavaggio: energia, costo, statistiche e manutenzione del filtro.

I dati sono salvati su disco (.storage/candy_simplyfi_plus.<entry_id>) e
sopravvivono ai riavvii di Home Assistant.
"""
from __future__ import annotations

from collections.abc import Callable
import copy
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_FILTER_EVERY, CONF_POWER, CONF_PRICE, CONF_PRICE_ENTITY,
    DEFAULT_FILTER_EVERY, DOMAIN, F_PROGRAM, F_STATE, PROGRAM_OLD_NAMES, PROGRAMS,
)
from .state import is_finished, is_online, is_running

MAX_CYCLE_HOURS = 12  # un ciclo più lungo è sicuramente rimasto aperto per errore
MAX_OFFLINE_MIN = 30  # irraggiungibile più a lungo durante un lavaggio = lavaggio interrotto

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
OLD_OUTCOMES = {"completato": "completed", "annullato": "cancelled"}
SAVE_DELAY = 10  # secondi

EMPTY = {
    "ciclo": {
        "in_corso": False,
        "kwh": None,
        "costo": None,
        "programma": None,
        "codice": None,
        "inizio": None,
        "fine": None,
        "durata_min": None,
        "esito": None,
    },
    "statistiche": {
        "lavaggi": 0,
        "programmi": {},       # chiave programma -> {lavaggi, misurati, kwh, costo}
        "misurati": 0,         # lavaggi con energia misurata
        "kwh": 0.0,
        "costo": 0.0,
        "ultimo": None,        # copia del ciclo terminato
    },
    "filtro": {
        "lavaggi": 0,
        "ultima_pulizia": None,
    },
}


def power_watts(state: State | None) -> float | None:
    """Valore in W di un sensore di potenza (converte kW e mW)."""
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


class CycleTracker:
    """Un oggetto per lavastoviglie, condiviso dalle entità di energia e statistiche."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, coordinator) -> None:
        self.hass = hass
        self.entry = entry
        self.coordinator = coordinator
        self._store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.data: dict = copy.deepcopy(EMPTY)
        self.power_entity: str | None = entry.options.get(CONF_POWER)
        self._watts: float | None = None
        self._last_ts = dt_util.utcnow()
        self._last_online = dt_util.utcnow()
        self._listeners: list[Callable[[], None]] = []
        self._unsubs: list[Callable[[], None]] = []

    # ------------------------------------------------------------------
    # avvio / arresto
    # ------------------------------------------------------------------
    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if isinstance(stored, dict):
            for key, default in EMPTY.items():
                value = stored.get(key)
                if isinstance(value, dict):
                    merged = copy.deepcopy(default)
                    merged.update(value)
                    self.data[key] = merged
            self._migrate()

    def _migrate(self) -> None:
        """Converte i dati salvati con i nomi italiani nelle chiavi traducibili."""
        def conv(cycle: dict | None) -> None:
            if not cycle:
                return
            name = cycle.get("programma")
            if name in PROGRAM_OLD_NAMES:
                cycle["programma"] = PROGRAM_OLD_NAMES[name]
            cycle["esito"] = OLD_OUTCOMES.get(cycle.get("esito"), cycle.get("esito"))

        conv(self.data["ciclo"])
        conv(self.data["statistiche"].get("ultimo"))
        progs = self.data["statistiche"]["programmi"]
        for name in list(progs):
            key = PROGRAM_OLD_NAMES.get(name)
            if key and key != name:
                old = progs.pop(name)
                cur = progs.setdefault(key, {"lavaggi": 0, "misurati": 0, "kwh": 0.0, "costo": 0.0})
                for k in cur:
                    cur[k] = round(cur[k] + old.get(k, 0), 4)

    @callback
    def async_start(self) -> None:
        self._unsubs.append(self.coordinator.async_add_listener(self._on_coordinator))
        if self.power_entity:
            self._watts = power_watts(self.hass.states.get(self.power_entity))
            self._unsubs.append(
                async_track_state_change_event(self.hass, [self.power_entity], self._on_power)
            )
        self._last_ts = dt_util.utcnow()

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        await self._store.async_save(self.data)

    @callback
    def add_listener(self, update: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(update)

        @callback
        def _remove() -> None:
            if update in self._listeners:
                self._listeners.remove(update)

        return _remove

    @callback
    def _notify(self) -> None:
        for update in list(self._listeners):
            update()

    @callback
    def _save(self) -> None:
        self._store.async_delay_save(lambda: self.data, SAVE_DELAY)

    # ------------------------------------------------------------------
    # proprietà comode per le entità
    # ------------------------------------------------------------------
    @property
    def cycle(self) -> dict:
        return self.data["ciclo"]

    @property
    def stats(self) -> dict:
        return self.data["statistiche"]

    @property
    def filter(self) -> dict:
        return self.data["filtro"]

    @property
    def filter_every(self) -> int:
        return int(self.entry.options.get(CONF_FILTER_EVERY, DEFAULT_FILTER_EVERY))

    @property
    def has_price(self) -> bool:
        return bool(self.power_entity) and (
            self.entry.options.get(CONF_PRICE_ENTITY) is not None
            or self.entry.options.get(CONF_PRICE) is not None
        )

    def price(self) -> float | None:
        """Prezzo dell'energia per kWh in questo momento."""
        entity = self.entry.options.get(CONF_PRICE_ENTITY)
        if entity:
            state = self.hass.states.get(entity)
            if state is None:
                return None
            try:
                value = float(state.state)
            except ValueError:
                return None
            unit = (state.attributes.get("unit_of_measurement") or "").lower()
            if "mwh" in unit:
                value /= 1000
            elif "wh" in unit and "kwh" not in unit:
                value *= 1000
            return value
        fixed = self.entry.options.get(CONF_PRICE)
        return None if fixed is None else float(fixed)

    # ------------------------------------------------------------------
    # conteggio
    # ------------------------------------------------------------------
    def _accumulate(self) -> None:
        """Somma energia (e costo) dall'ultima lettura, a potenza costante nel frattempo."""
        now = dt_util.utcnow()
        cycle = self.cycle
        if cycle["in_corso"] and self._watts is not None and self.power_entity:
            hours = (now - self._last_ts).total_seconds() / 3600
            if 0 < hours < 1:  # salta i buchi lunghi (es. riavvio di HA)
                kwh = self._watts * hours / 1000
                cycle["kwh"] = (cycle["kwh"] or 0.0) + kwh
                price = self.price()
                if price is not None:
                    cycle["costo"] = (cycle["costo"] or 0.0) + kwh * price
        self._last_ts = now

    @callback
    def _on_power(self, event: Event[EventStateChangedData]) -> None:
        self._accumulate()
        self._watts = power_watts(event.data["new_state"])
        self._notify()

    @callback
    def _on_coordinator(self) -> None:
        data = self.coordinator.data or {}
        cycle = self.cycle
        running = is_running(data)
        changed = False
        now = dt_util.utcnow()
        if is_online(data):
            self._last_online = now
        elif cycle["in_corso"] and (now - self._last_online).total_seconds() > MAX_OFFLINE_MIN * 60:
            # il modulo WiFi non risponde da troppo: la lavastoviglie è stata spenta a metà
            self._accumulate()
            self._close_cycle(completed=False)
            self._save()
            self._notify()
            return

        if running and cycle["in_corso"] and self._too_old():
            # ciclo rimasto aperto (es. lavastoviglie spenta a metà): lo chiude
            self._close_cycle(completed=False)
            cycle = self.cycle

        if running and not cycle["in_corso"]:
            # inizio ciclo
            code = data.get(F_PROGRAM)
            self.data["ciclo"] = {
                "in_corso": True,
                "kwh": 0.0 if self.power_entity else None,
                "costo": 0.0 if self.has_price else None,
                "programma": PROGRAMS.get(code or "", "other"),
                "codice": code,
                "inizio": dt_util.now().isoformat(timespec="seconds"),
                "fine": None,
                "durata_min": None,
                "esito": None,
            }
            self._last_ts = dt_util.utcnow()
            changed = True
        elif running:
            self._accumulate()
            changed = self.power_entity is not None
        elif cycle["in_corso"] and self.is_paused:
            # porta aperta a metà lavaggio: StatoDWash passa a 4 e poi torna a 3
            self._accumulate()
        elif cycle["in_corso"] and is_online(data):
            # fine ciclo (se la lavastoviglie è solo irraggiungibile aspettiamo)
            self._accumulate()
            self._close_cycle(completed=is_finished(data))
            changed = True

        if not cycle["in_corso"] and not running:
            self._last_ts = dt_util.utcnow()
        if changed:
            self._save()
            self._notify()

    @property
    def is_unreachable(self) -> bool:
        """Lavaggio in corso ma il modulo WiFi per ora non risponde (succede per pochi minuti)."""
        return self.cycle["in_corso"] and not is_online(self.coordinator.data)

    @property
    def is_paused(self) -> bool:
        """Lavaggio interrotto (porta aperta): ciclo aperto e StatoDWash 4."""
        data = self.coordinator.data or {}
        return self.cycle["in_corso"] and is_online(data) and data.get(F_STATE) == "4"

    def _too_old(self) -> bool:
        start = dt_util.parse_datetime(self.cycle.get("inizio") or "")
        return start is not None and (dt_util.now() - start).total_seconds() > MAX_CYCLE_HOURS * 3600

    def _close_cycle(self, completed: bool) -> None:
        cycle = self.cycle
        now = dt_util.now()
        cycle["in_corso"] = False
        cycle["fine"] = now.isoformat(timespec="seconds")
        cycle["esito"] = "completed" if completed else "cancelled"
        start = dt_util.parse_datetime(cycle.get("inizio") or "")
        if start is not None:
            cycle["durata_min"] = round((now - start).total_seconds() / 60)
        if cycle["kwh"] is not None:
            cycle["kwh"] = round(cycle["kwh"], 3)
        if cycle["costo"] is not None:
            cycle["costo"] = round(cycle["costo"], 4)

        if not completed:
            return
        stats = self.stats
        stats["ultimo"] = dict(cycle)
        name = cycle.get("programma") or "other"
        prog = stats["programmi"].setdefault(
            name, {"lavaggi": 0, "misurati": 0, "kwh": 0.0, "costo": 0.0}
        )
        stats["lavaggi"] += 1
        prog["lavaggi"] += 1
        if cycle["kwh"] is not None:
            stats["misurati"] += 1
            stats["kwh"] = round(stats["kwh"] + cycle["kwh"], 3)
            prog["misurati"] += 1
            prog["kwh"] = round(prog["kwh"] + cycle["kwh"], 3)
        if cycle["costo"] is not None:
            stats["costo"] = round(stats["costo"] + cycle["costo"], 4)
            prog["costo"] = round(prog["costo"] + cycle["costo"], 4)
        self.filter["lavaggi"] += 1

    # ------------------------------------------------------------------
    # azioni
    # ------------------------------------------------------------------
    @callback
    def reset_filter(self) -> None:
        self.data["filtro"] = {
            "lavaggi": 0,
            "ultima_pulizia": dt_util.now().isoformat(timespec="seconds"),
        }
        self._save()
        self._notify()
