"""Config flow for ElioT integration."""
from typing import Any
import logging

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_ENDPOINT,
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
        vol.Required(CONF_EUI): str,
    }
)


async def validate_input(hass, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    username = data[CONF_USERNAME]
    password = data[CONF_PASSWORD]
    eui = data[CONF_EUI]

    # Build API URL
    url = f"{API_ENDPOINT}?eui={eui}"

    # Attempt to fetch data with provided credentials
    auth = aiohttp.BasicAuth(username, password)
    session = async_get_clientsession(hass)

    try:
        async with session.get(
            url,
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as response:
            if response.status == 401:
                raise InvalidAuth

            if response.status == 404:
                raise InvalidEUI

            if response.status != 200:
                raise CannotConnect(f"HTTP {response.status}")

            # Try to parse JSON to ensure valid response
            data_response = await response.json()

            # Validate expected fields exist
            if "high_rate_kwh" not in data_response or "low_rate_kwh" not in data_response:
                raise InvalidResponse

    except aiohttp.ClientError as err:
        raise CannotConnect(f"Connection error: {err}") from err

    # Return info to be stored in the config entry
    return {
        "title": f"ElioT {eui}",
        "eui": eui,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ElioT."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except InvalidEUI:
                errors[CONF_EUI] = "invalid_eui"
            except InvalidResponse:
                errors["base"] = "invalid_response"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Check if device already configured
                await self.async_set_unique_id(user_input[CONF_EUI])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
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


class InvalidEUI(Exception):
    """Error to indicate invalid EUI."""


class InvalidResponse(Exception):
    """Error to indicate invalid API response."""
