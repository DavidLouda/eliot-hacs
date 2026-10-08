"""Client for the VISIONQ.CZ ElioT API."""
from __future__ import annotations

from typing import Any

import aiohttp

from .const import API_DEVICES_ENDPOINT, API_ENDPOINT, API_TIMEOUT


class EliotApiError(Exception):
    """Base error of the ElioT API."""


class EliotAuthError(EliotApiError):
    """Error to indicate authentication failure."""


class EliotConnectionError(EliotApiError):
    """Error to indicate we cannot connect."""


class EliotResponseError(EliotApiError):
    """Error to indicate invalid API response."""


class EliotApiClient:
    """Client for the VISIONQ.CZ ElioT API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._auth = aiohttp.BasicAuth(username, password)

    async def _async_get(self, url: str, params: dict[str, str] | None = None) -> Any:
        """Perform an authenticated GET request and return parsed JSON."""
        try:
            async with self._session.get(
                url,
                params=params,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT),
            ) as response:
                if response.status == 401:
                    raise EliotAuthError("Authentication failed")

                if response.status != 200:
                    raise EliotConnectionError(f"HTTP {response.status}")

                return await response.json(content_type=None)

        except (aiohttp.ClientError, TimeoutError) as err:
            raise EliotConnectionError(f"Connection error: {err}") from err
        except ValueError as err:
            raise EliotResponseError(f"Invalid JSON: {err}") from err

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the list of devices on the account."""
        data = await self._async_get(API_DEVICES_ENDPOINT)

        if not isinstance(data, dict) or not isinstance(data.get("devices"), list):
            raise EliotResponseError("Missing devices in response")

        return data["devices"]

    async def async_get_measurement(self, eui: str) -> dict[str, Any]:
        """Return the last measurement of a device."""
        data = await self._async_get(API_ENDPOINT, params={"eui": eui})

        if not isinstance(data, dict):
            raise EliotResponseError("Unexpected measurement response")

        return data
