# Changelog

## 1.1.0

### Baterie

- **Stav baterie** hodnoty 0 (externí napájení / neměřeno) a 255 (neznámý stav) nově zobrazuje jako *neznámý* místo 0 % ([#1](https://github.com/DavidLouda/eliot-hacs/issues/1)). Surová hodnota z API je v atributu `raw_value`.
- ElioT CLASSIC nemá obvod pro měření baterie a hlásí 100 % prakticky po celou dobu její životnosti. Procenta na portálu VISIONQ.CZ jsou odhad, který API neposkytuje. Nový senzor **Odhad baterie** počítá:
  - u ElioT PRO s čítačem náboje: `100 % − spotřebovaný náboj / kapacita baterie`,
  - u ostatních zařízení: `100 % − odeslané zprávy / výdrž baterie` (výchozích 80 000 zpráv odpovídá odhadu portálu).
- Výdrž baterie (počet zpráv) a kapacitu baterie lze upravit v nastavení integrace.

### Nové senzory

Vytvoří se jen tehdy, když je API pro dané zařízení vrací:

- Odeslané zprávy, Konec předplatného
- Síla signálu RSRP (NB-IoT) / RSSI (LoRaWAN)
- Spotřebovaný náboj baterie (ElioT PRO)
- Odstup signálu od šumu, Úroveň pokrytí (ECL), Vysílací výkon (ve výchozím stavu vypnuté)

### Vylepšení

- Opětovné přihlášení po změně hesla bez nutnosti integraci mazat
- Stažení diagnostiky se surovou odpovědí API (jméno, heslo, EUI a poloha jsou anonymizované)
- Senzor Celkem funguje i bez nízkého tarifu
- Integrace používá sdílené HTTP spojení Home Assistantu a nová API místo zastaralých
- Unique ID stávajících senzorů se nemění, historie i Energetický panel zůstávají zachované
- Testy a GitHub Actions (testy, HACS, hassfest)

**Vyžaduje Home Assistant 2025.1.0 nebo novější.**

### English

- **Battery State** now reports 0 (external power / not measured) and 255 (unknown) as *unknown* instead of 0 % ([#1](https://github.com/DavidLouda/eliot-hacs/issues/1)).
- ElioT CLASSIC does not measure its battery and reports 100 % for practically its whole life. New **Battery estimate** sensor: coulomb counter / battery capacity on ElioT PRO, otherwise messages sent / battery life (default 80,000 messages, matches the VISIONQ.CZ portal). Both parameters are configurable in the options.
- New sensors when provided by the API: messages sent, subscription expiry, RSRP / RSSI, consumed battery charge (PRO), SNR, coverage level and transmit power (disabled by default).
- Re-authentication flow, diagnostics download, total energy without low rate, shared HTTP session, modern Home Assistant APIs, unchanged unique IDs.
- **Requires Home Assistant 2025.1.0 or newer.**

## 1.0.0

- First release: high rate, low rate, total, reading time and battery state sensors, device selection, configurable update interval.
