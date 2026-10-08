"""Constants for the ElioT integration."""

DOMAIN = "eliot"
CONF_EUI = "eui"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_BATTERY_MESSAGE_BUDGET = "battery_message_budget"
CONF_BATTERY_CAPACITY = "battery_capacity_mah"

# API Configuration
API_ENDPOINT = "https://app.visionq.cz/api/device_last_measurement.php"
API_DEVICES_ENDPOINT = "https://app.visionq.cz/api/account_devices.php"
API_TIMEOUT = 30  # seconds
DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes in seconds
MIN_SCAN_INTERVAL = 900  # 15 minutes minimum
MAX_SCAN_INTERVAL = 86400  # 24 hours maximum (1440 minutes)

# Battery estimate
# Number of messages a battery lasts on devices without a coulomb counter.
# Calibrated against the VisionQ portal estimate (7223 messages -> 91 %).
DEFAULT_BATTERY_MESSAGE_BUDGET = 80000
MIN_BATTERY_MESSAGE_BUDGET = 1000
MAX_BATTERY_MESSAGE_BUDGET = 1000000
# Saft LS 14500 Li-SOCl2 (datasheet), used for the coulomb counter estimate
DEFAULT_BATTERY_CAPACITY = 2600
MIN_BATTERY_CAPACITY = 100
MAX_BATTERY_CAPACITY = 100000

# Raw battery_state byte (same meaning as LoRaWAN DevStatusAns)
BATTERY_STATE_EXTERNAL_POWER = 0  # external power or not measured
BATTERY_STATE_MAX = 254  # 100 %
BATTERY_STATE_UNKNOWN = 255  # unknown or powered from socket

# Keys of the device_last_measurement API response
SENSOR_HIGH_RATE = "high_rate_kwh"
SENSOR_LOW_RATE = "low_rate_kwh"
SENSOR_TIMESTAMP = "timestamp"
SENSOR_BATTERY = "battery_state"
ATTR_FCNT = "fcnt"
ATTR_RSRP = "rsrp"
ATTR_SNR = "snr"
ATTR_ECL = "ecl"
ATTR_TX_POWER = "tx_power"
ATTR_NETWORK = "network"

# Keys of the account_devices API response
ATTR_RSSI = "rssi"
ATTR_EXPIRES = "expires"
ATTR_LAST_ACTIVITY = "last_activity"
ATTR_COULOMB_COUNTER = "coulomb_counter"
ATTR_COULOMB_COUNTER_LSB = "coulomb_counter_lsb_mah"

# Sensor Entity IDs
SENSOR_VT_KEY = "high_rate"
SENSOR_NT_KEY = "low_rate"
SENSOR_TOTAL_KEY = "total"
SENSOR_LAST_ACTIVITY_KEY = "last_activity"
SENSOR_BATTERY_KEY = "battery_state"
SENSOR_BATTERY_ESTIMATE_KEY = "battery_estimate"
SENSOR_MESSAGES_SENT_KEY = "messages_sent"
SENSOR_RSRP_KEY = "signal_rsrp"
SENSOR_RSSI_KEY = "signal_rssi"
SENSOR_SNR_KEY = "signal_snr"
SENSOR_COVERAGE_LEVEL_KEY = "coverage_level"
SENSOR_TX_POWER_KEY = "tx_power"
SENSOR_CONSUMED_CHARGE_KEY = "consumed_charge"
SENSOR_SUBSCRIPTION_EXPIRES_KEY = "subscription_expires"
