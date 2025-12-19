# ElioT Energy Monitor Integration for Home Assistant

Custom integration for ElioT energy monitoring devices from VISIONQ.CZ.

## Features

- GUI configuration through Home Assistant UI
- Support for multiple ElioT devices
- Automatic data updates every 30 minutes (configurable from 15 minutes to 24 hours)
- Energy sensors compatible with Home Assistant Energy Dashboard

## Sensors

Each device provides 4 sensors:

1. **High Rate (VT)** - High tariff energy consumption in kWh
2. **Low Rate (NT)** - Low tariff energy consumption in kWh
3. **Total** - Combined energy consumption (VT + NT) in kWh
4. **Last Activity** - Timestamp of last device activity

All energy sensors use `state_class: total_increasing` for proper Energy Dashboard integration.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/eliot` directory to your Home Assistant `custom_components` folder
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "ElioT Energy Monitor"
4. Enter your credentials:
   - **Username**: Your VISIONQ.CZ account username
   - **Password**: Your VISIONQ.CZ account password
   - **Device EUI**: Your device EUI (e.g., 0901288001068943)
5. Click "Submit"

To add additional devices, repeat the process with different EUI values.

### Changing Update Interval

You can customize how often the integration fetches data:

1. Go to Settings → Devices & Services
2. Find the ElioT integration
3. Click "Configure"
4. Set the desired update interval (in minutes)
   - **Minimum**: 15 minutes
   - **Default**: 30 minutes
   - **Maximum**: 1440 minutes (24 hours)

## API Details

- **Endpoint**: https://app.visionq.cz/api/device_last_measurement.php
- **Authentication**: HTTP Basic Auth
- **Default Update Interval**: 30 minutes
- **Configurable Range**: 15 minutes - 1440 minutes (24 hours)

## Troubleshooting

### Authentication Failed
- Verify your VISIONQ.CZ credentials are correct
- Ensure your account has access to the specified device

### Invalid EUI
- Check the device EUI is entered correctly
- Verify the device exists in your VISIONQ.CZ account

### No Data
- Wait up to 30 minutes for the first data fetch (or your configured interval)
- Check the device is reporting data to VISIONQ.CZ
- Review Home Assistant logs for detailed error messages

## Support

Report issues at: [GitHub Issues](https://github.com/DavidLouda/eliot-hacs/issues)
