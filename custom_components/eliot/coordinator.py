"""DataUpdateCoordinator for ElioT."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EliotApiClient, EliotApiError, EliotAuthError
from .const import CONF_EUI, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

if TYPE_CHECKING:
    from . import EliotConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class EliotData:
    """Raw data of one ElioT device."""

    # Response of device_last_measurement
    measurement: dict[str, Any]
    # Record of this device from account_devices (None if unavailable)
    device: dict[str, Any] | None


class EliotDataUpdateCoordinator(DataUpdateCoordinator[EliotData]):
    """Class to manage fetching ElioT data from API."""

    config_entry: EliotConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: EliotConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.eui: str = entry.data[CONF_EUI]
        self.client = EliotApiClient(
            async_get_clientsession(hass),
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )

        # Get scan interval from options, fallback to default
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"ElioT {self.eui}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> EliotData:
        """Fetch data from API endpoint."""
        try:
            measurement = await self.client.async_get_measurement(self.eui)
        except EliotAuthError as err:
            raise ConfigEntryAuthFailed(
                "Authentication failed. Please check credentials."
            ) from err
        except EliotApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err

        return EliotData(
            measurement=measurement,
            device=await self._async_get_device(),
        )

    async def _async_get_device(self) -> dict[str, Any] | None:
        """Fetch the device record (signal, subscription, coulomb counter).

        This data is optional, so errors keep the previous record.
        """
        previous = self.data.device if self.data else None

        try:
            devices = await self.client.async_get_devices()
        except EliotApiError as err:
            _LOGGER.debug("Error fetching device list: %s", err)
            return previous

        for device in devices:
            if isinstance(device, dict) and str(device.get("eui")).lower() == self.eui.lower():
                return device

        _LOGGER.debug("Device %s not found in device list", self.eui)
        return previous
