[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/DavidLouda/eliot-hacs?style=for-the-badge)](LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=DavidLouda&repository=eliot-hacs&category=integration)

# Integrace ElioT Energy Monitor pro Home Assistant

Vlastní integrace (custom integration) pro zařízení na monitorování energie ElioT od VISIONQ.CZ.

## Funkce

- Konfigurace přes uživatelské rozhraní Home Assistant
- Podpora pro více zařízení ElioT
- Automatická aktualizace dat každých 30 minut (konfigurovatelné od 15 minut do 24 hodin)
- Senzory energie kompatibilní s Energetickým panelem (Energy Dashboard) v Home Assistant

## Senzory

Každé zařízení poskytuje 4 senzory:

1. **Vysoký tarif (VT)** - Spotřeba energie ve vysokém tarifu v kWh
2. **Nízký tarif (NT)** - Spotřeba energie v nízkém tarifu v kWh
3. **Celkem** - Kombinovaná spotřeba energie (VT + NT) v kWh
4. **Poslední aktivita** - Časové razítko poslední aktivity zařízení

Všechny energetické senzory používají `state_class: total_increasing` pro správnou integraci do Energetického panelu.

## Instalace

### HACS (Doporučeno)

1. Otevřete HACS v Home Assistant
2. Přejděte na "Integrace"
3. Klikněte na tři tečky v pravém horním rohu a vyberte "Vlastní repozitáře" (Custom repositories)
4. Přidejte URL tohoto repozitáře a vyberte "Integrace" jako kategorii
5. Klikněte na "Stáhnout" (Download / Install)
6. Restartujte Home Assistant

### Manuální instalace

1. Zkopírujte složku `custom_components/eliot` do vaší složky `custom_components` v Home Assistant
2. Restartujte Home Assistant

## Konfigurace

1. Přejděte do Nastavení → Zařízení a služby
2. Klikněte na "Přidat integraci"
3. Vyhledejte "ElioT Energy Monitor"
4. Zadejte své přihlašovací údaje k VISIONQ.CZ (**Uživatelské jméno** a **Heslo**).
5. V dalším kroku vyberte ze seznamu zařízení (EUI), které chcete přidat.
6. Klikněte na "Odeslat"

Pro přidání dalších zařízení (pokud jich máte více) opakujte proces znovu.

### Změna intervalu aktualizace

Můžete si přizpůsobit, jak často integrace stahuje data:

1. Přejděte do Nastavení → Zařízení a služby
2. Najděte integraci ElioT
3. Klikněte na "Konfigurovat"
4. Nastavte požadovaný interval aktualizace (v minutách)
   - **Minimum**: 15 minut
   - **Výchozí**: 30 minut
   - **Maximum**: 1440 minut (24 hodin)

## Podrobnosti o API

- **Endpoint**: https://app.visionq.cz/api/device_last_measurement.php
- **Autentizace**: HTTP Basic Auth
- **Výchozí interval aktualizace**: 30 minut
- **Konfigurovatelný rozsah**: 15 minut - 1440 minut (24 hodin)

## Řešení problémů

### Neúspěšná autentizace (Authentication Failed)
- Ověřte, že jsou vaše přihlašovací údaje k VISIONQ.CZ správné

### Žádná nalezená zařízení
- Ujistěte se, že váš účet má k dispozici aktivní zařízení ElioT

### Žádná data (No Data)
- Počkejte až 30 minut na první stažení dat (nebo podle vašeho nastaveného intervalu)
- Zkontrolujte, zda zařízení odesílá data do VISIONQ.CZ
- Zkontrolujte protokoly (logy) Home Assistant pro podrobnější chybové zprávy

## Podpora

Chyby nahlaste na: [GitHub Issues](https://github.com/DavidLouda/eliot-hacs/issues)

---

# ElioT Energy Monitor Integration for Home Assistant (English)

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
4. Enter your VISIONQ.CZ credentials (**Username** and **Password**).
5. In the next step, select the device (EUI) you want to add from the list.
6. Click "Submit"

To add additional devices, repeat the process.

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

### No devices found
- Ensure your account has active ElioT devices

### No Data
- Wait up to 30 minutes for the first data fetch (or your configured interval)
- Check the device is reporting data to VISIONQ.CZ
- Review Home Assistant logs for detailed error messages

## Support

Report issues at: [GitHub Issues](https://github.com/DavidLouda/eliot-hacs/issues)
