"""Tests for ElioT diagnostics."""
from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant

from custom_components.eliot.diagnostics import async_get_config_entry_diagnostics

from .conftest import setup_integration


async def test_diagnostics(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test diagnostics contain raw API data without secrets."""
    await setup_integration(hass, config_entry)

    result = await async_get_config_entry_diagnostics(hass, config_entry)

    assert result["entry"]["data"] == {
        "username": REDACTED,
        "password": REDACTED,
        "eui": REDACTED,
    }
    assert result["measurement"]["battery_state"] == 254
    assert result["measurement"]["fcnt"] == 7223
    assert result["device"]["eui"] == REDACTED
    assert result["device"]["lat"] is None  # None values are kept
    assert result["device"]["expires"] == 1796218654
    assert result["last_update_success"] is True
