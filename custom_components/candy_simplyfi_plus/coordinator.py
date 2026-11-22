"""Coordinator: interroga la lavastoviglie (ogni 30 s, configurabile)."""
from __future__ import annotations

import csv
import logging
import os
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import CandyApi, CandyConnectionError, CandyError
from .const import CONF_LOG, CONF_SCAN, DEFAULT_LOG, DEFAULT_SCAN, DOMAIN, ONLINE

_LOGGER = logging.getLogger(__name__)

LOG_FILE = "candy_simplyfi_plus_registro.csv"
LOG_MAX_BYTES = 2_000_000  # oltre 2 MB il file viene rinominato in .old.csv


class CandyCoordinator(DataUpdateCoordinator[dict]):
    """Gestisce il polling."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: CandyApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=int(entry.options.get(CONF_SCAN, DEFAULT_SCAN))),
        )
        self.api = api
        self._last_logged: dict | None = None
        self.log_path = hass.config.path(LOG_FILE)
        self.log_enabled = bool(entry.options.get(CONF_LOG, DEFAULT_LOG))
        self.tracker = None  # CycleTracker, assegnato in __init__.py

    async def _async_update_data(self) -> dict:
        try:
            data = await self.api.async_get_status()
        except CandyConnectionError as err:
            # Quando è spenta il modulo WiFi non risponde: non è un errore
            _LOGGER.debug("Lavastoviglie non raggiungibile: %s", err)
            data = {ONLINE: False}
        except CandyError as err:
            raise UpdateFailed(str(err)) from err
        else:
            data[ONLINE] = True

        if self.log_enabled and data != self._last_logged:
            self._last_logged = dict(data)
            await self.hass.async_add_executor_job(self._write_log, dict(data))
        return data

    def _write_log(self, data: dict) -> None:
        """Aggiunge una riga al registro CSV quando qualcosa cambia."""
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > LOG_MAX_BYTES:
                os.replace(self.log_path, self.log_path.replace(".csv", ".old.csv"))
            new_file = not os.path.exists(self.log_path)
            fields = [k for k in data if k != ONLINE]
            with open(self.log_path, "a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh, delimiter=";")
                ora = dt_util.now().strftime("%Y-%m-%d %H:%M:%S")
                if new_file:
                    writer.writerow(["ora", "online", "dati"])
                if not data.get(ONLINE):
                    writer.writerow([ora, "no", ""])
                else:
                    writer.writerow([ora, "si", " ".join(f"{k}={data[k]}" for k in fields)])
        except OSError as err:
            _LOGGER.warning("Candy Simply-Fi Plus: impossibile scrivere il registro: %s", err)
