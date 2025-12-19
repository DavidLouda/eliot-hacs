"""Constants for the ElioT integration."""

DOMAIN = "eliot"
CONF_EUI = "eui"
CONF_SCAN_INTERVAL = "scan_interval"

# API Configuration
API_ENDPOINT = "https://app.visionq.cz/api/device_last_measurement.php"
DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes in seconds
MIN_SCAN_INTERVAL = 900  # 15 minutes minimum
MAX_SCAN_INTERVAL = 86400  # 24 hours maximum (1440 minutes)

# Sensor Keys from API
SENSOR_HIGH_RATE = "high_rate_kwh"
SENSOR_LOW_RATE = "low_rate_kwh"
SENSOR_TIMESTAMP = "timestamp"

# Sensor Entity IDs
SENSOR_VT_KEY = "high_rate"
SENSOR_NT_KEY = "low_rate"
SENSOR_TOTAL_KEY = "total"
SENSOR_LAST_ACTIVITY_KEY = "last_activity"
