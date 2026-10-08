"""Tests for the ElioT config flow."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import aiohttp
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.eliot.const import (
    API_DEVICES_ENDPOINT,
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_MESSAGE_BUDGET,
    CONF_EUI,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

from .conftest import EUI, setup_integration

CREDENTIALS = {CONF_USERNAME: "user", CONF_PASSWORD: "secret"}


async def test_user_flow(hass: HomeAssistant, mock_api) -> None:
    """Test the full user flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EUI: EUI}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"ElioT {EUI}"
    assert result["data"] == {**CREDENTIALS, CONF_EUI: EUI}
    assert result["result"].unique_id == EUI

    await hass.async_block_till_done()
    assert result["result"].state is ConfigEntryState.LOADED


@pytest.mark.parametrize(
    ("mock_kwargs", "error"),
    [
        ({"status": 401}, "invalid_auth"),
        ({"status": 500}, "cannot_connect"),
        ({"exc": aiohttp.ClientError()}, "cannot_connect"),
        ({"exc": TimeoutError()}, "cannot_connect"),
        ({"json": {"error": "x"}}, "invalid_response"),
        ({"text": "not json"}, "invalid_response"),
        ({"json": {"version": 1.0, "devices": []}}, "no_devices_found"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    aioclient_mock,
    devices: dict[str, Any],
    mock_kwargs: dict[str, Any],
    error: str,
) -> None:
    """Test errors in the user step and recovery."""
    aioclient_mock.get(API_DEVICES_ENDPOINT, **mock_kwargs)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    aioclient_mock.clear_requests()
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device"


async def test_already_configured(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    devices: dict[str, Any],
) -> None:
    """Test adding an already configured device aborts."""
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CREDENTIALS
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EUI: EUI}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test reauthentication updates the credentials and reloads the entry."""
    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_PASSWORD] == "new"
    assert config_entry.data[CONF_EUI] == EUI

    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.LOADED


async def test_reauth_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    devices: dict[str, Any],
) -> None:
    """Test reauthentication errors."""
    aioclient_mock.get(API_DEVICES_ENDPOINT, status=401)

    result = await config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "user", CONF_PASSWORD: "wrong"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    # Another account without the configured device
    devices["devices"][0]["eui"] = "ffffffffffffffff"
    aioclient_mock.clear_requests()
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_USERNAME: "other", CONF_PASSWORD: "secret"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "device_not_found"}
    assert config_entry.data[CONF_USERNAME] == "user"
    assert config_entry.data[CONF_PASSWORD] == "secret"


async def test_options_flow(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test the options flow stores options and reloads the entry."""
    await setup_integration(hass, config_entry)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 60,
            CONF_BATTERY_MESSAGE_BUDGET: 50000,
            CONF_BATTERY_CAPACITY: 3000,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {
        CONF_SCAN_INTERVAL: 3600,
        CONF_BATTERY_MESSAGE_BUDGET: 50000,
        CONF_BATTERY_CAPACITY: 3000,
    }
    # Entry was reloaded with the new interval
    assert config_entry.runtime_data.update_interval == timedelta(hours=1)


async def test_options_flow_range(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test the scan interval is limited to 15 minutes."""
    import voluptuous as vol

    await setup_integration(hass, config_entry)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    with pytest.raises(vol.Invalid):
        await hass.config_entries.options.async_configure(
            result["flow_id"],
            {
                CONF_SCAN_INTERVAL: 5,
                CONF_BATTERY_MESSAGE_BUDGET: 80000,
                CONF_BATTERY_CAPACITY: 2600,
            },
        )
