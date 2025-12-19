"""Config flow for ElioT integration."""
from typing import Any
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    API_DEVICES_ENDPOINT,
    CONF_EUI,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


async def validate_credentials(hass, username, password) -> list[dict[str, Any]]:
    """Validate credentials and return list of devices."""
    auth = aiohttp.BasicAuth(username, password)
    session = async_get_clientsession(hass)

    try:
        async with session.get(
            API_DEVICES_ENDPOINT,
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 401:
                raise InvalidAuth

            if response.status != 200:
                raise CannotConnect(f"HTTP {response.status}")

            data = await response.json()
            
            if "devices" not in data:
                raise InvalidResponse
                
            return data["devices"]

    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection error: {err}") from err


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ElioT."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self._username = None
        self._password = None
        self._devices = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step (credentials)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]

            try:
                self._devices = await validate_credentials(
                    self.hass, self._username, self._password
                )
                
                if not self._devices:
                    errors["base"] = "no_devices_found"
                else:
                    return await self.async_step_device()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the device selection step."""
        errors: dict[str, str] = {}

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

        # Create device list for selector
        # Only show devices that are not already configured? 
        # For now, just show all. User will get an error if they try to add duplicate.
        
        device_options = [
            {"label": f"{d.get('eui')} (Last activity: {d.get('last_activity', 'Unknown')})", "value": d.get("eui")}
            for d in self._devices
        ]

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EUI): SelectSelector(
                        SelectSelectorConfig(
                            options=device_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ElioT."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert minutes to seconds before saving
            interval_minutes = user_input[CONF_SCAN_INTERVAL]
            interval_seconds = interval_minutes * 60
            return self.async_create_entry(
                title="",
                data={CONF_SCAN_INTERVAL: interval_seconds}
            )

        # Get current interval in seconds, convert to minutes for display
        current_interval_seconds = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_interval_minutes = current_interval_seconds // 60

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval_minutes,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL // 60,
                            max=MAX_SCAN_INTERVAL // 60
                        ),
                    ),
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate authentication failure."""


class InvalidResponse(Exception):
    """Error to indicate invalid API response."""
