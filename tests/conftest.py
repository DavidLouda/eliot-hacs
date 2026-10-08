"""Fixtures for ElioT tests."""
from __future__ import annotations

from collections.abc import Generator
import json
from pathlib import Path
from typing import Any
from unittest.mock import PropertyMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from custom_components.eliot.const import (
    API_DEVICES_ENDPOINT,
    API_ENDPOINT,
    CONF_EUI,
    DOMAIN,
)

EUI = "0000000000000001"
FIXTURES = Path(__file__).parent / "fixtures"


def load_json(name: str) -> dict[str, Any]:
    """Load a JSON fixture."""
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in all tests."""
    yield


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Enable entities that are disabled by default."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
        new_callable=PropertyMock,
    ):
        yield


@pytest.fixture
def measurement() -> dict[str, Any]:
    """Return a measurement API response (ElioT CLASSIC NB-IoT)."""
    return load_json("measurement_nbiot.json")


@pytest.fixture
def devices() -> dict[str, Any]:
    """Return a device list API response."""
    return load_json("devices_nbiot.json")


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a config entry added to hass."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=EUI,
        title=f"ElioT {EUI}",
        data={CONF_USERNAME: "user", CONF_PASSWORD: "secret", CONF_EUI: EUI},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_api(
    aioclient_mock: AiohttpClientMocker,
    measurement: dict[str, Any],
    devices: dict[str, Any],
) -> AiohttpClientMocker:
    """Mock both API endpoints with fixture data.

    Tests may modify the measurement/devices fixtures before requesting this.
    """
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    return aioclient_mock


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Set up the integration."""
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
