"""Diagnostics support for ElioT."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import EliotConfigEntry
from .const import CONF_EUI

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, CONF_EUI, "lat", "lon"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: EliotConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    data = coordinator.data

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "measurement": async_redact_data(data.measurement, TO_REDACT) if data else None,
        "device": async_redact_data(data.device, TO_REDACT) if data and data.device else None,
        "last_update_success": coordinator.last_update_success,
    }
