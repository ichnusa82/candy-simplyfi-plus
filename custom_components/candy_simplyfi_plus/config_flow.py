"""Configurazione da interfaccia."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CandyApi, CandyConnectionError, CandyKeyError
from .const import (
    CONF_KEY, CONF_MODE, CONF_POWER, CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD, DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CandyConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return CandyOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            manual_key = (user_input.get(CONF_KEY) or "").strip() or None
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            api = CandyApi(async_get_clientsession(self.hass), host, manual_key)
            try:
                mode, key = await api.async_detect()
                status = await api.async_get_status()
            except CandyConnectionError:
                errors["base"] = "cannot_connect"
            except CandyKeyError:
                errors["base"] = "invalid_key"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Errore imprevisto")
                errors["base"] = "unknown"
            else:
                _LOGGER.info("Candy Simply-Fi Plus %s: modo=%s chiave=%s campi=%s", host, mode, key, list(status))
                return self.async_create_entry(
                    title=f"Candy Simply-Fi Plus ({host})",
                    data={CONF_HOST: host, CONF_KEY: key, CONF_MODE: mode},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Optional(CONF_KEY, default=(user_input or {}).get(CONF_KEY, "")): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class CandyOptionsFlow(OptionsFlow):
    """Opzioni: sensore di potenza (presa smart) e soglia di consumo."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POWER,
                    description={"suggested_value": opts.get(CONF_POWER)},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_POWER_THRESHOLD,
                    default=opts.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=1000, step=0.5, unit_of_measurement="W",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
