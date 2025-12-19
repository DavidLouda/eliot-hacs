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
    SENSOR_BATTERY,
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

                    # Parse the new API structure
                    device_info = data.get("device", {})
                    measurements = data.get("data", [])

                    result = {}

                    # Extract device info
                    result[SENSOR_TIMESTAMP] = device_info.get("last_activity")
                    result[SENSOR_BATTERY] = device_info.get("battery_state")

                    # Extract metrics
                    for measure in measurements:
                        metric = measure.get("metric")
                        value = measure.get("value")
                        
                        if metric == 1:
                            result[SENSOR_HIGH_RATE] = value
                        elif metric == 2:
                            result[SENSOR_LOW_RATE] = value

                    # Validate we got at least some data
                    if not result:
                        raise UpdateFailed("No valid data found in API response")

                    return result

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except ConfigEntryAuthFailed:
            raise
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
