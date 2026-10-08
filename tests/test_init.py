"""Tests for ElioT setup."""
from __future__ import annotations

from typing import Any

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.eliot.const import API_DEVICES_ENDPOINT, API_ENDPOINT, DOMAIN

from .conftest import EUI, setup_integration


async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test setting up and unloading the entry."""
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    # Measurement is requested for the configured EUI
    urls = [call[1] for call in mock_api.mock_calls]
    assert any(str(url).startswith(API_ENDPOINT) and url.query["eui"] == EUI for url in urls)

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_auth_failure_starts_reauth(
    hass: HomeAssistant, config_entry: MockConfigEntry, aioclient_mock
) -> None:
    """Test 401 from the API starts a reauth flow."""
    aioclient_mock.get(API_ENDPOINT, status=401)

    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == config_entry.entry_id


async def test_api_error_retries(
    hass: HomeAssistant, config_entry: MockConfigEntry, aioclient_mock
) -> None:
    """Test API errors retry the setup."""
    aioclient_mock.get(API_ENDPOINT, status=500)

    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_device_list_failure_is_optional(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    measurement: dict[str, Any],
) -> None:
    """Test energy sensors work when the device list is unavailable."""
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, status=500)

    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    registry = er.async_get(hass)
    assert registry.async_get_entity_id("sensor", DOMAIN, f"{EUI}_high_rate")
    # Only provided by the device list
    assert not registry.async_get_entity_id(
        "sensor", DOMAIN, f"{EUI}_subscription_expires"
    )
