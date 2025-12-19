"""DataUpdateCoordinator for ElioT."""
from datetime import timedelta
import logging
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_ENDPOINT,
    CONF_EUI,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    SENSOR_HIGH_RATE,
    SENSOR_LOW_RATE,
    SENSOR_TIMESTAMP,
)

_LOGGER = logging.getLogger(__name__)


class EliotDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching ElioT data from API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.eui = entry.data[CONF_EUI]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        # Get scan interval from options, fallback to default
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"ElioT {self.eui}",
            update_interval=timedelta(seconds=scan_interval),
        )

    def update_interval_seconds(self, interval: int) -> None:
        """Update the polling interval."""
        self.update_interval = timedelta(seconds=interval)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        url = f"{API_ENDPOINT}?eui={self.eui}"

        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    auth=auth,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 401:
                        raise ConfigEntryAuthFailed(
                            "Authentication failed. Please check credentials."
                        )

                    if response.status != 200:
                        raise UpdateFailed(
                            f"Error fetching data: HTTP {response.status}"
                        )

                    data = await response.json()

                    # Validate required fields are present
                    if not all(
                        key in data
                        for key in [SENSOR_HIGH_RATE, SENSOR_LOW_RATE, SENSOR_TIMESTAMP]
                    ):
                        raise UpdateFailed("Invalid API response: missing required fields")

                    return data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
