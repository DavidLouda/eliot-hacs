"""The ElioT integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import EliotDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type EliotConfigEntry = ConfigEntry[EliotDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: EliotConfigEntry) -> bool:
    """Set up ElioT from a config entry."""
    coordinator = EliotDataUpdateCoordinator(hass, entry)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    # Reload on options change (scan interval, battery estimate parameters)
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_update_options(hass: HomeAssistant, entry: EliotConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: EliotConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
