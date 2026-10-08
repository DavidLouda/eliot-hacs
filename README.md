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
- Stav a odhad baterie, síla signálu a konec předplatného
- Opětovné přihlášení po změně hesla bez nutnosti integraci mazat
- Stažení diagnostiky pro snadné hlášení chyb

## Senzory

| Senzor | Popis |
|---|---|
| **Vysoký tarif (VT)** | Spotřeba energie ve vysokém tarifu v kWh |
| **Nízký tarif (NT)** | Spotřeba energie v nízkém tarifu v kWh |
| **Celkem** | Kombinovaná spotřeba energie (VT + NT) v kWh |
| **Čas odečtu** | Čas posledního měření zařízení |
| **Stav baterie** | Stav baterie hlášený zařízením (viz [Baterie](#baterie)) |
| **Odhad baterie** | Odhad zbývající kapacity baterie (viz [Baterie](#baterie)) |
| **Odeslané zprávy** | Počet zpráv odeslaných zařízením *(diagnostický)* |
| **Síla signálu (RSRP / RSSI)** | Síla signálu NB-IoT (RSRP) nebo LoRaWAN (RSSI) v dBm *(diagnostický)* |
| **Konec předplatného** | Datum vypršení datové služby *(diagnostický)* |
| **Spotřebovaný náboj baterie** | Jen ElioT PRO s čítačem náboje, v mAh *(diagnostický)* |
| **Odstup signálu od šumu, Úroveň pokrytí (ECL), Vysílací výkon** | Podrobnosti o rádiovém spojení *(diagnostické, ve výchozím stavu vypnuté)* |

Senzory se vytvoří jen tehdy, když je API pro dané zařízení vrací (např. RSSI jen u LoRaWAN, čítač náboje jen u PRO).

Všechny energetické senzory používají `state_class: total_increasing` pro správnou integraci do Energetického panelu.

### Baterie

API VISIONQ.CZ posílá stav baterie jako číslo 0–255 (`battery_state`):

- **1–254** se přepočítá na 0–100 % (254 = 100 %),
- **0** (externí napájení / neměřeno) a **255** (neznámý stav) se zobrazí jako *neznámý*.

**ElioT CLASSIC nemá obvod pro měření baterie**, takže hlásí 254 (100 %) prakticky po celou dobu životnosti baterie. Procenta na portálu VISIONQ.CZ jsou odhad, který API neposkytuje. Proto integrace nabízí senzor **Odhad baterie**:

- **Zařízení s čítačem náboje (ElioT PRO):** `100 % − spotřebovaný náboj / kapacita baterie` (výchozí kapacita 2600 mAh),
- **ostatní zařízení:** `100 % − odeslané zprávy / výdrž baterie` (výchozí výdrž 80 000 zpráv odpovídá odhadu portálu).

Pokud se odhad liší od portálu, upravte **Výdrž baterie (počet zpráv)** nebo **Kapacitu baterie** v nastavení integrace.

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

### Nastavení integrace

1. Přejděte do Nastavení → Zařízení a služby
2. Najděte integraci ElioT
3. Klikněte na "Konfigurovat"
4. Upravte:
   - **Interval aktualizace (minuty)**: minimum 15, výchozí 30, maximum 1440 (24 hodin)
   - **Výdrž baterie (počet zpráv)**: pro odhad baterie u zařízení bez čítače náboje (výchozí 80 000)
   - **Kapacita baterie (mAh)**: pro odhad baterie u zařízení s čítačem náboje (výchozí 2600)

### Změna hesla

Pokud změníte heslo k VISIONQ.CZ, Home Assistant zobrazí výzvu k opětovnému přihlášení. Stačí zadat nové údaje, integraci není třeba mazat.

## Podrobnosti o API

- **Endpointy**: https://app.visionq.cz/api/device_last_measurement.php (měření), https://app.visionq.cz/api/account_devices.php (seznam zařízení, signál, předplatné)
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

### Hlášení chyb s diagnostikou
- V Nastavení → Zařízení a služby → ElioT otevřete nabídku (tři tečky) a zvolte **Stáhnout diagnostiku**
- Soubor obsahuje surovou odpověď API; jméno, heslo, EUI a poloha jsou anonymizované
- Přiložte ho k hlášení chyby

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
- Battery state and estimate, signal strength and subscription expiry
- Re-authentication after a password change without removing the integration
- Diagnostics download for easy bug reports

## Sensors

| Sensor | Description |
|---|---|
| **High Rate (VT)** | High tariff energy consumption in kWh |
| **Low Rate (NT)** | Low tariff energy consumption in kWh |
| **Total** | Combined energy consumption (VT + NT) in kWh |
| **Reading Time** | Time of the last device measurement |
| **Battery State** | Battery state reported by the device (see [Battery](#battery)) |
| **Battery estimate** | Estimated remaining battery (see [Battery](#battery)) |
| **Messages sent** | Number of messages sent by the device *(diagnostic)* |
| **Signal strength (RSRP / RSSI)** | NB-IoT (RSRP) or LoRaWAN (RSSI) signal strength in dBm *(diagnostic)* |
| **Subscription expires** | Expiry date of the data service *(diagnostic)* |
| **Consumed battery charge** | ElioT PRO with a coulomb counter only, in mAh *(diagnostic)* |
| **Signal-to-noise ratio, Coverage enhancement level, Transmit power** | Radio link details *(diagnostic, disabled by default)* |

Sensors are only created when the API provides them for the device (e.g. RSSI for LoRaWAN only, coulomb counter for PRO only).

All energy sensors use `state_class: total_increasing` for proper Energy Dashboard integration.

### Battery

The VISIONQ.CZ API reports the battery as a number 0–255 (`battery_state`):

- **1–254** is converted to 0–100 % (254 = 100 %),
- **0** (external power / not measured) and **255** (unknown) are shown as *unknown*.

**ElioT CLASSIC has no battery measurement circuit**, so it reports 254 (100 %) for practically the whole battery life. The percentage on the VISIONQ.CZ portal is an estimate that the API does not provide. That is why the integration offers a **Battery estimate** sensor:

- **Devices with a coulomb counter (ElioT PRO):** `100 % − consumed charge / battery capacity` (default capacity 2600 mAh),
- **other devices:** `100 % − messages sent / battery life` (default battery life of 80,000 messages matches the portal estimate).

If the estimate differs from the portal, adjust **Battery life (number of messages)** or **Battery capacity** in the integration options.

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

### Options

1. Go to Settings → Devices & Services
2. Find the ElioT integration
3. Click "Configure"
4. Adjust:
   - **Update interval (minutes)**: minimum 15, default 30, maximum 1440 (24 hours)
   - **Battery life (number of messages)**: for the battery estimate on devices without a coulomb counter (default 80,000)
   - **Battery capacity (mAh)**: for the battery estimate on devices with a coulomb counter (default 2600)

### Password Change

If you change your VISIONQ.CZ password, Home Assistant asks you to re-authenticate. Just enter the new credentials; there is no need to remove the integration.

## API Details

- **Endpoints**: https://app.visionq.cz/api/device_last_measurement.php (measurement), https://app.visionq.cz/api/account_devices.php (device list, signal, subscription)
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

### Reporting Bugs with Diagnostics
- In Settings → Devices & Services → ElioT open the menu (three dots) and choose **Download diagnostics**
- The file contains the raw API response; username, password, EUI and location are redacted
- Attach it to your bug report

## Support

Report issues at: [GitHub Issues](https://github.com/DavidLouda/eliot-hacs/issues)
