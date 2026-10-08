"""Tests for ElioT sensors."""
from __future__ import annotations

from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.eliot.const import (
    API_DEVICES_ENDPOINT,
    API_ENDPOINT,
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_MESSAGE_BUDGET,
    DOMAIN,
)

from .conftest import EUI, setup_integration


def _state(hass: HomeAssistant, key: str):
    """Return the state of the sensor with the given key."""
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{EUI}_{key}")
    assert entity_id is not None, f"sensor {key} not created"
    return hass.states.get(entity_id)


def _exists(hass: HomeAssistant, key: str) -> bool:
    """Return True if the sensor with the given key was created."""
    return (
        er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{EUI}_{key}")
        is not None
    )


async def test_nbiot_sensors(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test sensors with real ElioT CLASSIC NB-IoT data."""
    await setup_integration(hass, config_entry)

    assert float(_state(hass, "high_rate").state) == 10675.62
    assert float(_state(hass, "low_rate").state) == 15348.966
    assert float(_state(hass, "total").state) == pytest.approx(26024.586)
    assert _state(hass, "last_activity").state == "2026-10-08T11:56:26+00:00"
    assert _state(hass, "battery_state").state == "100"
    assert _state(hass, "battery_state").attributes["raw_value"] == 254
    # 7223 messages of 80000 -> 91 % (matches the VISIONQ.CZ portal)
    assert _state(hass, "battery_estimate").state == "91"
    assert _state(hass, "messages_sent").state == "7223"
    assert float(_state(hass, "signal_rsrp").state) == -80.5
    assert _state(hass, "subscription_expires").state == "2026-12-02T13:37:34+00:00"

    # Not provided for NB-IoT CLASSIC
    assert not _exists(hass, "signal_rssi")
    assert not _exists(hass, "consumed_charge")


async def test_legacy_unique_ids(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test unique IDs of existing sensors are unchanged."""
    await setup_integration(hass, config_entry)

    for key in ("high_rate", "low_rate", "total", "last_activity", "battery_state"):
        assert _exists(hass, key)


async def test_device_info(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test device info."""
    await setup_integration(hass, config_entry)

    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, EUI)})
    assert device is not None
    assert device.name == "ElioT"
    assert device.manufacturer == "VISIONQ.CZ"
    assert device.model == "ElioT (NB IOT)"
    assert device.serial_number == EUI


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_nbiot_scaling(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_api
) -> None:
    """Test NB-IoT radio values are converted from tenths."""
    await setup_integration(hass, config_entry)

    assert float(_state(hass, "signal_snr").state) == 24.8
    assert float(_state(hass, "tx_power").state) == 8.0
    assert _state(hass, "coverage_level").state == "0"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (0, STATE_UNKNOWN),  # external power / not measured (issue #1)
        (1, "0"),
        (127, "50"),
        (254, "100"),
        (255, STATE_UNKNOWN),  # unknown or powered from socket
        (None, STATE_UNKNOWN),
        ("invalid", STATE_UNKNOWN),
    ],
)
async def test_battery_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    measurement: dict[str, Any],
    devices: dict[str, Any],
    raw: Any,
    expected: str,
) -> None:
    """Test conversion of the battery_state byte."""
    measurement["battery_state"] = raw
    devices["devices"][0]["battery_state"] = raw
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    await setup_integration(hass, config_entry)

    assert _state(hass, "battery_state").state == expected


async def test_battery_estimate_options(
    hass: HomeAssistant, mock_api, measurement: dict[str, Any]
) -> None:
    """Test the message budget option is used for the estimate."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=EUI,
        data={"username": "user", "password": "secret", "eui": EUI},
        options={CONF_BATTERY_MESSAGE_BUDGET: 10000},
    )
    entry.add_to_hass(hass)
    await setup_integration(hass, entry)

    # 7223 of 10000 messages used
    assert _state(hass, "battery_estimate").state == "28"


async def test_battery_estimate_clamped(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    measurement: dict[str, Any],
    devices: dict[str, Any],
) -> None:
    """Test the estimate never drops below 0 %."""
    measurement["fcnt"] = 200000
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    await setup_integration(hass, config_entry)

    assert _state(hass, "battery_estimate").state == "0"


async def test_pro_coulomb_counter(
    hass: HomeAssistant,
    aioclient_mock,
    measurement: dict[str, Any],
    devices: dict[str, Any],
) -> None:
    """Test devices with a coulomb counter (ElioT PRO)."""
    devices["devices"][0]["coulomb_counter"] = 1000
    devices["devices"][0]["coulomb_counter_lsb_mah"] = 0.5
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=EUI,
        data={"username": "user", "password": "secret", "eui": EUI},
        options={CONF_BATTERY_CAPACITY: 2000},
    )
    entry.add_to_hass(hass)
    await setup_integration(hass, entry)

    assert float(_state(hass, "consumed_charge").state) == 500
    # 500 of 2000 mAh used, the coulomb counter wins over the message count
    assert _state(hass, "battery_estimate").state == "75"


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_lorawan_device(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    measurement: dict[str, Any],
    devices: dict[str, Any],
) -> None:
    """Test LoRaWAN radio values are not scaled."""
    for key in ("rsrp", "ecl", "tx_power"):
        measurement.pop(key)
        devices["devices"][0][key] = None
    measurement["network"] = "LORAWAN"
    measurement["snr"] = 7.5
    devices["devices"][0]["snr"] = 7.5
    devices["devices"][0]["rssi"] = -110
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    await setup_integration(hass, config_entry)

    assert float(_state(hass, "signal_rssi").state) == -110
    assert float(_state(hass, "signal_snr").state) == 7.5
    assert not _exists(hass, "signal_rsrp")
    assert not _exists(hass, "tx_power")
    assert not _exists(hass, "coverage_level")


async def test_single_tariff(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    aioclient_mock,
    measurement: dict[str, Any],
    devices: dict[str, Any],
) -> None:
    """Test total uses available values when the low rate is missing."""
    measurement["low_rate_kwh"] = None
    aioclient_mock.get(API_ENDPOINT, json=measurement)
    aioclient_mock.get(API_DEVICES_ENDPOINT, json=devices)
    await setup_integration(hass, config_entry)

    assert _state(hass, "low_rate").state == STATE_UNKNOWN
    assert float(_state(hass, "total").state) == 10675.62
