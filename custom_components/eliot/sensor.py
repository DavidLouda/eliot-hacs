"""Sensor platform for ElioT integration."""
from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_EUI,
    DOMAIN,
    SENSOR_HIGH_RATE,
    SENSOR_LAST_ACTIVITY_KEY,
    SENSOR_LOW_RATE,
    SENSOR_NT_KEY,
    SENSOR_TIMESTAMP,
    SENSOR_TOTAL_KEY,
    SENSOR_VT_KEY,
    SENSOR_BATTERY,
    SENSOR_BATTERY_KEY,
)
from .coordinator import EliotDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ElioT sensors based on a config entry."""
    coordinator: EliotDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    eui = entry.data[CONF_EUI]

    # Create sensor entities
    entities = [
        EliotEnergySensor(
            coordinator,
            eui,
            SENSOR_VT_KEY,
            "High Rate (VT)",
            SENSOR_HIGH_RATE,
        ),
        EliotEnergySensor(
            coordinator,
            eui,
            SENSOR_NT_KEY,
            "Low Rate (NT)",
            SENSOR_LOW_RATE,
        ),
        EliotTotalEnergySensor(coordinator, eui),
        EliotLastActivitySensor(coordinator, eui),
        EliotBatterySensor(coordinator, eui),
    ]

    async_add_entities(entities)


class EliotEnergySensor(CoordinatorEntity[EliotDataUpdateCoordinator], SensorEntity):
    """Representation of an ElioT energy sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EliotDataUpdateCoordinator,
        eui: str,
        sensor_key: str,
        default_name: str,
        api_key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._eui = eui
        self._sensor_key = sensor_key
        self._api_key = api_key

        # Entity attributes
        self._attr_translation_key = sensor_key
        self._attr_unique_id = f"{eui}_{sensor_key}"
        # Name format: [Translation] [EUI]
        # We rely on HA's translation system for the first part, but to enforce specific order with EUI
        # we might need to override 'name'. However, if we set has_entity_name=True, HA prepends device name.
        # If Device Name is "ElioT [EUI]", then entity name "High Rate" becomes "ElioT [EUI] High Rate".
        # The user wants "High Rate (VT) [EUI]".
        # So we should probably set the name explicitly.
        self._attr_name = f"{default_name} {eui}"

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, eui)},
            "name": f"ElioT {eui}",
            "manufacturer": "VISIONQ.CZ",
            "model": "ElioT Energy Monitor",
        }

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(self._api_key)

        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                _LOGGER.error("Invalid value for %s: %s", self._api_key, value)
                return None

        return None


class EliotTotalEnergySensor(CoordinatorEntity[EliotDataUpdateCoordinator], SensorEntity):
    """Representation of total energy (VT + NT)."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_has_entity_name = True
    _attr_translation_key = SENSOR_TOTAL_KEY

    def __init__(
        self,
        coordinator: EliotDataUpdateCoordinator,
        eui: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._eui = eui

        # Entity attributes
        self._attr_name = f"Total {eui}"
        self._attr_unique_id = f"{eui}_{SENSOR_TOTAL_KEY}"

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, eui)},
            "name": f"ElioT {eui}",
            "manufacturer": "VISIONQ.CZ",
            "model": "ElioT Energy Monitor",
        }

    @property
    def native_value(self) -> float | None:
        """Return the sum of high rate and low rate."""
        if self.coordinator.data is None:
            return None

        try:
            high_rate = float(self.coordinator.data.get(SENSOR_HIGH_RATE, 0))
            low_rate = float(self.coordinator.data.get(SENSOR_LOW_RATE, 0))
            return high_rate + low_rate
        except (ValueError, TypeError) as err:
            _LOGGER.error("Error calculating total energy: %s", err)
            return None


class EliotLastActivitySensor(CoordinatorEntity[EliotDataUpdateCoordinator], SensorEntity):
    """Representation of last activity timestamp."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_translation_key = SENSOR_LAST_ACTIVITY_KEY

    def __init__(
        self,
        coordinator: EliotDataUpdateCoordinator,
        eui: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._eui = eui

        # Entity attributes
        self._attr_name = f"Last Activity {eui}"
        self._attr_unique_id = f"{eui}_{SENSOR_LAST_ACTIVITY_KEY}"

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, eui)},
            "name": f"ElioT {eui}",
            "manufacturer": "VISIONQ.CZ",
            "model": "ElioT Energy Monitor",
        }

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp as datetime object."""
        if self.coordinator.data is None:
            return None

        timestamp = self.coordinator.data.get(SENSOR_TIMESTAMP)

        if timestamp is not None:
            try:
                # Convert Unix timestamp to datetime
                return datetime.fromtimestamp(int(timestamp))
            except (ValueError, TypeError, OSError) as err:
                _LOGGER.error("Invalid timestamp value: %s (%s)", timestamp, err)
                return None

        return None


class EliotBatterySensor(CoordinatorEntity[EliotDataUpdateCoordinator], SensorEntity):
    """Representation of battery state."""

    _attr_has_entity_name = True
    _attr_translation_key = SENSOR_BATTERY_KEY

    def __init__(
        self,
        coordinator: EliotDataUpdateCoordinator,
        eui: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._eui = eui

        # Entity attributes
        self._attr_name = f"Battery {eui}"
        self._attr_unique_id = f"{eui}_{SENSOR_BATTERY_KEY}"

        # Device info for grouping sensors
        self._attr_device_info = {
            "identifiers": {(DOMAIN, eui)},
            "name": f"ElioT {eui}",
            "manufacturer": "VISIONQ.CZ",
            "model": "ElioT Energy Monitor",
        }

    @property
    def native_value(self) -> int | None:
        """Return the battery state."""
        if self.coordinator.data is None:
            return None

        value = self.coordinator.data.get(SENSOR_BATTERY)
        
        if value is None:
            return None
            
        try:
            int_val = int(value)
            if int_val == 255:
                return None
            return int_val
        except (ValueError, TypeError):
            return None
