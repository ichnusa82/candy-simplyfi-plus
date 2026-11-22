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
    CONF_FILTER_EVERY, CONF_KEY, CONF_LOG, CONF_MODE, CONF_POWER, CONF_POWER_THRESHOLD,
    CONF_PRICE, CONF_PRICE_ENTITY, CONF_SCAN, DEFAULT_FILTER_EVERY, DEFAULT_LOG,
    DEFAULT_POWER_THRESHOLD, DEFAULT_SCAN, DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _async_probe(hass, host: str, manual_key: str | None) -> tuple[dict | None, dict[str, str]]:
    """Prova a leggere la lavastoviglie: restituisce i dati della voce oppure gli errori."""
    api = CandyApi(async_get_clientsession(hass), host, manual_key)
    try:
        mode, key = await api.async_detect()
        status = await api.async_get_status()
    except CandyConnectionError:
        return None, {"base": "cannot_connect"}
    except CandyKeyError:
        return None, {"base": "invalid_key"}
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Errore imprevisto")
        return None, {"base": "unknown"}
    _LOGGER.info("Candy Simply-Fi Plus %s: modo=%s campi=%s", host, mode, list(status))
    return {CONF_HOST: host, CONF_KEY: key, CONF_MODE: mode}, {}


def _title(host: str) -> str:
    return f"Candy Simply-Fi Plus ({host})"


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

            data, errors = await _async_probe(self.hass, host, manual_key)
            if data is not None:
                return self.async_create_entry(title=_title(host), data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Optional(CONF_KEY, default=(user_input or {}).get(CONF_KEY, "")): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Cambia l'indirizzo IP (o la chiave) senza rimuovere l'integrazione."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            manual_key = (user_input.get(CONF_KEY) or "").strip() or None
            if host != entry.unique_id:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
            data, errors = await _async_probe(self.hass, host, manual_key)
            if data is not None:
                return self.async_update_reload_and_abort(
                    entry, unique_id=host, title=_title(host), data_updates=data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or entry.data).get(CONF_HOST, "")): str,
                vol.Optional(CONF_KEY, default=(user_input or {}).get(CONF_KEY, "")): str,
            }
        )
        return self.async_show_form(
            step_id="reconfigure", data_schema=schema, errors=errors,
            description_placeholders={"host": entry.data.get(CONF_HOST, "")},
        )


def _number(min_, max_, step, unit=None):
    # unit_of_measurement deve essere una stringa: se manca non va passato
    config = selector.NumberSelectorConfig(
        min=min_, max=max_, step=step, mode=selector.NumberSelectorMode.BOX,
    )
    if unit:
        config["unit_of_measurement"] = unit
    return selector.NumberSelector(config)


class CandyOptionsFlow(OptionsFlow):
    """Opzioni: consumi e costo, manutenzione filtro, lettura e registro."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if (user_input.get(CONF_PRICE) is not None or user_input.get(CONF_PRICE_ENTITY)) \
                    and not user_input.get(CONF_POWER):
                errors["base"] = "price_needs_power"
            else:
                return self.async_create_entry(data=user_input)

        opts = user_input or self.config_entry.options
        currency = self.hass.config.currency
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_POWER, description={"suggested_value": opts.get(CONF_POWER)},
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Required(
                    CONF_POWER_THRESHOLD,
                    default=opts.get(CONF_POWER_THRESHOLD, DEFAULT_POWER_THRESHOLD),
                ): _number(0, 1000, 0.5, "W"),
                vol.Optional(
                    CONF_PRICE, description={"suggested_value": opts.get(CONF_PRICE)},
                ): _number(0, 10, "any", f"{currency}/kWh"),
                vol.Optional(
                    CONF_PRICE_ENTITY, description={"suggested_value": opts.get(CONF_PRICE_ENTITY)},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["sensor", "input_number", "number"])
                ),
                vol.Required(
                    CONF_FILTER_EVERY, default=opts.get(CONF_FILTER_EVERY, DEFAULT_FILTER_EVERY),
                ): _number(0, 500, 1),
                vol.Required(
                    CONF_SCAN, default=opts.get(CONF_SCAN, DEFAULT_SCAN),
                ): _number(10, 300, 5, "s"),
                vol.Required(
                    CONF_LOG, default=opts.get(CONF_LOG, DEFAULT_LOG),
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
