"""Sensor platform for ElioT integration."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfEnergy,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EliotConfigEntry
from .const import (
    ATTR_COULOMB_COUNTER,
    ATTR_COULOMB_COUNTER_LSB,
    ATTR_ECL,
    ATTR_EXPIRES,
    ATTR_FCNT,
    ATTR_NETWORK,
    ATTR_RSRP,
    ATTR_RSSI,
    ATTR_SNR,
    ATTR_TX_POWER,
    BATTERY_STATE_EXTERNAL_POWER,
    BATTERY_STATE_MAX,
    BATTERY_STATE_UNKNOWN,
    CONF_BATTERY_CAPACITY,
    CONF_BATTERY_MESSAGE_BUDGET,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_BATTERY_MESSAGE_BUDGET,
    DOMAIN,
    SENSOR_BATTERY,
    SENSOR_BATTERY_ESTIMATE_KEY,
    SENSOR_BATTERY_KEY,
    SENSOR_CONSUMED_CHARGE_KEY,
    SENSOR_COVERAGE_LEVEL_KEY,
    SENSOR_HIGH_RATE,
    SENSOR_LAST_ACTIVITY_KEY,
    SENSOR_LOW_RATE,
    SENSOR_MESSAGES_SENT_KEY,
    SENSOR_NT_KEY,
    SENSOR_RSRP_KEY,
    SENSOR_RSSI_KEY,
    SENSOR_SNR_KEY,
    SENSOR_SUBSCRIPTION_EXPIRES_KEY,
    SENSOR_TIMESTAMP,
    SENSOR_TOTAL_KEY,
    SENSOR_TX_POWER_KEY,
    SENSOR_VT_KEY,
)
from .coordinator import EliotData, EliotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


def _get(data: EliotData, key: str) -> Any:
    """Return a value from the measurement, falling back to the device record."""
    value = data.measurement.get(key)
    if value is None and data.device is not None:
        value = data.device.get(key)
    return value


def _to_float(value: Any) -> float | None:
    """Convert an API value to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        _LOGGER.debug("Invalid numeric value: %s", value)
        return None


def _to_int(value: Any) -> int | None:
    """Convert an API value to int."""
    value = _to_float(value)
    return None if value is None else int(value)


def _to_timestamp(value: Any) -> datetime | None:
    """Convert a Unix timestamp to an aware UTC datetime."""
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        _LOGGER.debug("Invalid timestamp value: %s", value)
        return None


def _is_nbiot(data: EliotData) -> bool:
    """Return True for NB-IoT devices."""
    return "NB" in str(data.measurement.get(ATTR_NETWORK) or "").upper()


def _radio_value(data: EliotData, key: str) -> float | None:
    """Return a radio value; NB-IoT modems report them in tenths (0.1 dB/dBm)."""
    value = _to_float(_get(data, key))
    if value is not None and _is_nbiot(data):
        return value / 10
    return value


def _total_energy(data: EliotData) -> float | None:
    """Return the sum of high rate and low rate that are available."""
    values = [
        value
        for key in (SENSOR_HIGH_RATE, SENSOR_LOW_RATE)
        if (value := _to_float(data.measurement.get(key))) is not None
    ]
    return sum(values) if values else None


def _battery_level(data: EliotData) -> int | None:
    """Convert the battery_state byte to percent.

    0 = external power / not measured, 1-254 = level (254 = 100 %),
    255 = unknown or powered from socket.
    """
    raw = _to_float(_get(data, SENSOR_BATTERY))
    if raw is None or not BATTERY_STATE_EXTERNAL_POWER < raw < BATTERY_STATE_UNKNOWN:
        return None
    return round(raw / BATTERY_STATE_MAX * 100)


def _consumed_charge(data: EliotData) -> float | None:
    """Return consumed battery charge in mAh (devices with a coulomb counter)."""
    counter = _to_float(_get(data, ATTR_COULOMB_COUNTER))
    lsb = _to_float(_get(data, ATTR_COULOMB_COUNTER_LSB))
    if counter is None or lsb is None:
        return None
    return counter * lsb


def _battery_estimate(data: EliotData, options: Mapping[str, Any]) -> int | None:
    """Estimate remaining battery from consumed charge or sent messages."""
    consumed = _consumed_charge(data)
    if consumed is not None:
        used = consumed / options.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)
    else:
        messages = _to_float(_get(data, ATTR_FCNT))
        if messages is None:
            return None
        used = messages / options.get(
            CONF_BATTERY_MESSAGE_BUDGET, DEFAULT_BATTERY_MESSAGE_BUDGET
        )
    return max(0, min(100, round(100 * (1 - used))))


def _has(key: str) -> Callable[[EliotData], bool]:
    """Create an exists_fn checking that the API provides a value."""
    return lambda data: _get(data, key) is not None


@dataclass(frozen=True, kw_only=True)
class EliotSensorEntityDescription(SensorEntityDescription):
    """Describes an ElioT sensor."""

    value_fn: Callable[[EliotData, Mapping[str, Any]], StateType | datetime]
    exists_fn: Callable[[EliotData], bool] = lambda _: True
    attr_fn: Callable[[EliotData], dict[str, Any]] | None = None


SENSORS: tuple[EliotSensorEntityDescription, ...] = (
    EliotSensorEntityDescription(
        key=SENSOR_VT_KEY,
        translation_key=SENSOR_VT_KEY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data, _: _to_float(data.measurement.get(SENSOR_HIGH_RATE)),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_NT_KEY,
        translation_key=SENSOR_NT_KEY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data, _: _to_float(data.measurement.get(SENSOR_LOW_RATE)),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_TOTAL_KEY,
        translation_key=SENSOR_TOTAL_KEY,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data, _: _total_energy(data),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_LAST_ACTIVITY_KEY,
        translation_key=SENSOR_LAST_ACTIVITY_KEY,
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data, _: _to_timestamp(data.measurement.get(SENSOR_TIMESTAMP)),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_BATTERY_KEY,
        translation_key=SENSOR_BATTERY_KEY,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data, _: _battery_level(data),
        attr_fn=lambda data: {"raw_value": _get(data, SENSOR_BATTERY)},
    ),
    EliotSensorEntityDescription(
        key=SENSOR_BATTERY_ESTIMATE_KEY,
        translation_key=SENSOR_BATTERY_ESTIMATE_KEY,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=_battery_estimate,
        exists_fn=lambda data: _has(ATTR_FCNT)(data) or _consumed_charge(data) is not None,
    ),
    EliotSensorEntityDescription(
        key=SENSOR_CONSUMED_CHARGE_KEY,
        translation_key=SENSOR_CONSUMED_CHARGE_KEY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="mAh",
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, _: _consumed_charge(data),
        exists_fn=lambda data: _consumed_charge(data) is not None,
    ),
    EliotSensorEntityDescription(
        key=SENSOR_MESSAGES_SENT_KEY,
        translation_key=SENSOR_MESSAGES_SENT_KEY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, _: _to_int(_get(data, ATTR_FCNT)),
        exists_fn=_has(ATTR_FCNT),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_RSRP_KEY,
        translation_key=SENSOR_RSRP_KEY,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, _: _radio_value(data, ATTR_RSRP),
        exists_fn=_has(ATTR_RSRP),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_RSSI_KEY,
        translation_key=SENSOR_RSSI_KEY,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, _: _radio_value(data, ATTR_RSSI),
        exists_fn=_has(ATTR_RSSI),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_SNR_KEY,
        translation_key=SENSOR_SNR_KEY,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data, _: _radio_value(data, ATTR_SNR),
        exists_fn=_has(ATTR_SNR),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_COVERAGE_LEVEL_KEY,
        translation_key=SENSOR_COVERAGE_LEVEL_KEY,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data, _: _to_int(_get(data, ATTR_ECL)),
        exists_fn=_has(ATTR_ECL),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_TX_POWER_KEY,
        translation_key=SENSOR_TX_POWER_KEY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data, _: _radio_value(data, ATTR_TX_POWER),
        exists_fn=_has(ATTR_TX_POWER),
    ),
    EliotSensorEntityDescription(
        key=SENSOR_SUBSCRIPTION_EXPIRES_KEY,
        translation_key=SENSOR_SUBSCRIPTION_EXPIRES_KEY,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data, _: _to_timestamp(_get(data, ATTR_EXPIRES)),
        exists_fn=_has(ATTR_EXPIRES),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EliotConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ElioT sensors based on a config entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        EliotSensor(coordinator, description)
        for description in SENSORS
        if description.exists_fn(coordinator.data)
    )


class EliotSensor(CoordinatorEntity[EliotDataUpdateCoordinator], SensorEntity):
    """Representation of an ElioT sensor."""

    entity_description: EliotSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EliotDataUpdateCoordinator,
        description: EliotSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self.entity_description = description
        eui = coordinator.eui
        network = coordinator.data.measurement.get(ATTR_NETWORK)

        self._attr_unique_id = f"{eui}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, eui)},
            name="ElioT",
            manufacturer="VISIONQ.CZ",
            model=f"ElioT ({network})" if network else "ElioT Energy Monitor",
            serial_number=eui,
        )

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(
            self.coordinator.data, self.coordinator.config_entry.options
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator.data)
