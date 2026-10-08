"""Config flow for ElioT integration."""
from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .api import EliotApiClient, EliotAuthError, EliotConnectionError, EliotResponseError
from .const import (
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_MESSAGE_BUDGET,
    CONF_EUI,
    CONF_SCAN_INTERVAL,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_BATTERY_MESSAGE_BUDGET,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_BATTERY_CAPACITY,
    MAX_BATTERY_MESSAGE_BUDGET,
    MAX_SCAN_INTERVAL,
    MIN_BATTERY_CAPACITY,
    MIN_BATTERY_MESSAGE_BUDGET,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_credentials(
    hass: HomeAssistant, username: str, password: str
) -> list[dict[str, Any]]:
    """Validate credentials and return list of devices."""
    client = EliotApiClient(async_get_clientsession(hass), username, password)
    return await client.async_get_devices()


async def _async_validate_input(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Validate credentials and return devices and form errors."""
    try:
        devices = await validate_credentials(
            hass, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
        )
    except EliotConnectionError:
        return [], {"base": "cannot_connect"}
    except EliotAuthError:
        return [], {"base": "invalid_auth"}
    except EliotResponseError:
        return [], {"base": "invalid_response"}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected exception")
        return [], {"base": "unknown"}

    if not devices:
        return [], {"base": "no_devices_found"}

    return devices, {}


class EliotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ElioT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._username: str | None = None
        self._password: str | None = None
        self._devices: list[dict[str, Any]] = []

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step (credentials)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._devices, errors = await _async_validate_input(self.hass, user_input)

            if not errors:
                self._username = user_input[CONF_USERNAME]
                self._password = user_input[CONF_PASSWORD]
                return await self.async_step_device()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the device selection step."""
        if user_input is not None:
            eui = user_input[CONF_EUI]

            # Check if device already configured
            await self.async_set_unique_id(eui)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"ElioT {eui}",
                data={
                    CONF_USERNAME: self._username,
                    CONF_PASSWORD: self._password,
                    CONF_EUI: eui,
                },
            )

        if not self._devices:
            return self.async_abort(reason="no_devices_found")

        # Create device dict for selection
        devices_map = {}
        for device in self._devices:
            eui = device.get("eui")
            if not eui:
                continue

            label_suffix = ""
            last_activity = device.get("last_activity")
            if last_activity:
                try:
                    dt = dt_util.as_local(dt_util.utc_from_timestamp(int(last_activity)))
                    label_suffix = f" ({dt.strftime('%Y-%m-%d %H:%M:%S')})"
                except (ValueError, TypeError, OSError):
                    pass

            devices_map[eui] = f"{eui}{label_suffix}"

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EUI): vol.In(devices_map),
                }
            ),
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication when credentials stop working."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for new credentials."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            devices, errors = await _async_validate_input(self.hass, user_input)

            if not errors and not any(
                device.get("eui") == entry.data[CONF_EUI] for device in devices
            ):
                errors["base"] = "device_not_found"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA,
                {CONF_USERNAME: entry.data[CONF_USERNAME]},
            ),
            description_placeholders={"eui": entry.data[CONF_EUI]},
            errors=errors,
        )


class OptionsFlowHandler(OptionsFlow):
    """Handle options flow for ElioT."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    # Stored in seconds, shown in minutes
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL] * 60,
                    CONF_BATTERY_MESSAGE_BUDGET: user_input[CONF_BATTERY_MESSAGE_BUDGET],
                    CONF_BATTERY_CAPACITY: user_input[CONF_BATTERY_CAPACITY],
                }
            )

        options = self.config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                        // 60,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL // 60,
                            max=MAX_SCAN_INTERVAL // 60,
                        ),
                    ),
                    vol.Required(
                        CONF_BATTERY_MESSAGE_BUDGET,
                        default=options.get(
                            CONF_BATTERY_MESSAGE_BUDGET, DEFAULT_BATTERY_MESSAGE_BUDGET
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_BATTERY_MESSAGE_BUDGET,
                            max=MAX_BATTERY_MESSAGE_BUDGET,
                        ),
                    ),
                    vol.Required(
                        CONF_BATTERY_CAPACITY,
                        default=options.get(
                            CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY
                        ),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_BATTERY_CAPACITY, max=MAX_BATTERY_CAPACITY),
                    ),
                }
            ),
        )
