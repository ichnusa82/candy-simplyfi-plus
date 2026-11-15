# Candy Simply-Fi Plus

🇮🇹 [Italiano](README.md) · 🇬🇧 **English**

Custom integration for **Home Assistant** that connects **Candy simply-Fi** dishwashers **over the local network**, with no cloud and no Candy account.

It reads the dishwasher status every 30 seconds directly from its WiFi module and shows it in Home Assistant with ready-to-use sensors and a built-in dashboard card.

> ⚠️ Unofficial project, not affiliated with or endorsed by Candy / Haier.

![Candy Simply-Fi Plus card](images/card_stati.png)

---

## Tested models

| Brand | Model | Product code | App | Status |
|---|---|---|---|---|
| Candy | **CDIMN 4D622PBE** (built-in dishwasher, 15 place settings) | 32901467 | Candy simply-Fi | ✅ Working |

So far Candy Simply-Fi Plus has been tested **on this model only**. Other Candy simply-Fi dishwashers may work, but with different program and state codes (see [How to help](#how-to-help)).

**Not compatible:**
- appliances using the **Haier hOn** app: they have no local API;
- simply-Fi **washing machines, dryers and ovens**: they connect, but their fields are different and the sensors would stay empty (support planned).

---

## Features

- 🔌 **Local network only**: no cloud, no account, works without internet
- 🔐 **Automatic encryption handling**: detects whether the dishwasher encrypts its data and recovers the key by itself
- 📊 **Sensors**: wash state and phase, program, remaining time, end time, progress, delayed start, door, salt, rinse aid, options, errors
- 🃏 **Built-in dashboard card**: installed automatically together with the integration
- ⚡ **Energy**: link a power sensor (smart plug, W or kW) to get *Power*, *Consuming* and *Cycle energy* (kWh per wash)
- 📝 **Data log**: saves every change to a CSV file, useful to analyse wash cycles
- 🇮🇹 Italian and English interface

---

## Requirements

- Home Assistant **2026.3** or newer (needed for the integration icon; everything else also works on older versions)
- Dishwasher **already connected to WiFi** with the **Candy simply-Fi** app (only needed once)
- Dishwasher and Home Assistant on the **same network**
- Recommended: a **fixed IP** for the dishwasher (DHCP reservation on the router)

---

## Installation

### HACS (recommended)
1. In HACS open the **⋮ → Custom repositories** menu.
2. Add `https://github.com/ichnusa82/candy-simplyfi-plus` with type **Integration**.
3. Search for **Candy Simply-Fi Plus**, download it and restart Home Assistant.

### Manual
1. Download the [latest release](https://github.com/ichnusa82/candy-simplyfi-plus/releases) and take the `custom_components/candy_simplyfi_plus` folder.
2. Copy it to `/config/custom_components/candy_simplyfi_plus/`.
3. Restart Home Assistant.

---

## Configuration

1. **Switch the dishwasher on**: when it is off, the WiFi module does not respond.
2. Go to **Settings → Devices & services → Add integration → Candy Simply-Fi Plus**.
3. Enter the dishwasher's **IP address**.
4. Leave the **key** field empty: if the data is encrypted, the key is recovered automatically.

### Options (energy)
In **Candy Simply-Fi Plus → Configure** you can set:

| Option | Description |
|---|---|
| Power sensor | Sensor of the smart plug the dishwasher is plugged into (W or kW) |
| "Consuming" threshold | Value in W above which the dishwasher counts as *consuming* (default 5 W) |

With a power sensor configured, **Cycle energy** resets when each wash starts, adds up the kWh used and, at the end of the cycle, keeps the total until the next wash.

> Note: during the wash the pump uses very little power; with the default threshold *Consuming* turns on mainly while the dishwasher **heats the water**.

---

## Entities

All entities belong to the **Lavastoviglie Candy** device. Entity names follow the Home Assistant language (Italian or English).

![Device sensors](images/sensori.png)

### Sensors
| Entity | Description |
|---|---|
| State | Off, Cancelled, Idle, Ready, Delayed start, Wash, Rinse, Drying, Finished |
| Program | Program name (attributes: code, temperature, average duration) |
| Remaining time | Minutes to the end of the cycle |
| Cycle end | Expected end time (also with delayed start) |
| Delayed start | Minutes left before the start |
| Starts at | Start time with delayed start |
| Progress | Percentage of the cycle completed |
| Error | Error description (attribute: code) |
| Water softener | Water hardness level set on the dishwasher (S0–S7) (diagnostic) |
| Raw data | Every field read from the dishwasher, as attributes (diagnostic) |
| Power | Only with a power sensor configured |
| Cycle energy | kWh used by the running or last finished wash (attributes: program, start, end, duration). Only with a power sensor configured |

### Binary sensors
| Entity | Description |
|---|---|
| Running | On while washing |
| Door | Open / closed |
| Salt missing | Salt warning |
| Rinse aid missing | Rinse aid warning |
| TABS option | Combined detergent option active |
| Smart Door option | Automatic door opening active |
| Online | Dishwasher reachable |
| Beeps | Acoustic signals enabled (diagnostic) |
| Memo function | Last program memory enabled (diagnostic) |
| Consuming | Only with a power sensor configured |

---

## Dashboard card

The card is loaded automatically by the integration: **no HACS frontend download and no resources to add**.

In **Edit dashboard → Add card** search for **"Candy Simply-Fi Plus"**, or use:

```yaml
type: custom:candy-simplyfi-plus-card
```

Optional settings:

```yaml
type: custom:candy-simplyfi-plus-card
name: Dishwasher             # card title
show_programs: true          # show the program strip
power_entity: sensor.xxx     # power sensor other than the integration's one
colors:
  active: "#2E7DD7"          # ready
  running: "#52dca5"         # washing
  scheduled: "#FFB300"       # delayed start
  finished: "#43a047"        # finished
```

### Examples

| Dark theme | Light theme |
|---|---|
| ![Card states](images/card_stati.png) | ![Card in light theme](images/card_tema_chiaro.png) |

*Images were generated with sample data. The card labels are in Italian.*

The card shows state and phase, the highlighted program, remaining time and end time, an animated progress bar, power and warnings (door open, salt, rinse aid, TABS, Smart Door, errors). It follows the Home Assistant light/dark theme.

---

## Data log

Every time a value changes, Candy Simply-Fi Plus appends a line to:

```
/config/candy_simplyfi_plus_registro.csv
```

The file is rotated above 2 MB (`candy_simplyfi_plus_registro.old.csv`). It can be deleted at any time: it is recreated automatically.

---

## Protocol codes (CDIMN 4D622PBE)

Found through real tests and the user manual.

### Machine state (`StatoDWash`)
| Code | Meaning |
|---|---|
| 1 | Cancelled / reset in progress (a few seconds, `Program` = P0) |
| 2 | On, no program confirmed |
| 3 | Program started: waiting if `DelayStart` > 0, otherwise washing |
| 4 | Program selected, ready |
| 5 | Cycle finished |

### Wash phase (`r2`)
| Code | Phase |
|---|---|
| 0 | Waiting (delayed start) |
| 1 | Pre-wash *(to be confirmed)* |
| 2 | Wash |
| 3 | Rinse |
| 4 | Drying |
| 5 | End |

### Programs (`Program`)
| Code | Program | Temperature | Average duration |
|---|---|---|---|
| P8 | Eco | 45 °C | 3:52 |
| P2 | Intensive | 75 °C | 2:10 |
| P17 | Night | 55 °C | 4:00 |
| P5 | Universal | 60 °C | 2:00 |
| P16 | Auto | 55–65 °C | 1:35 |
| P9 | Delicate | 45 °C | 1:25 |
| P19 | Zoom | 60 °C | 0:39 |
| P20 | Rapid | 50 °C | 0:24 |
| P12 | Pre-wash | — | 0:05 |

### Other fields
| Field | Meaning |
|---|---|
| `RemTime` | Remaining minutes (back to the program duration at the end of the cycle) |
| `DelayStart` | Minutes to the delayed start |
| `OpenDoor` | Door: 1 open, 0 closed |
| `TreinUno` | TABS option |
| `OpenDoorOpt` | Smart Door option |
| `MissSalt` / `MissRinse` | Salt / rinse aid missing |
| `CodiceErrore` | E0 none, E2 no water intake, E3 no drain, E4 water leak, E8/Ei heater or clogged filter |
| `StatoWiFi` | Remote control (CONTROLLO REMOTO on the panel): 1 on, 0 read only |
| `Reset` | 1 for a few seconds after a cancellation (with `StatoDWash` = 1 and `Program` = P0) |
| `r1` | Program number as in the manual/panel (Eco 1, Intensive 2, Night 3, Auto 5…) |
| `r6` | Beeps: 1 on, 0 off |
| `r7` | Water softener level (S0–S7) |
| `r8` | Memo function: 1 on, 0 off |
| `StartStop` | Always 0 on this model |

---

## Known limitations

- The dishwasher **switches itself off** after 5 minutes with no program: it then shows as *Off*.
- The integration **only reads data**: starting and stopping from Home Assistant are not supported.
- Program and state codes are verified **on the tested model only**.

---

## How to help

Do you own another Candy simply-Fi dishwasher? You can help add it:

1. Install Candy Simply-Fi Plus and run a full wash.
2. Get the file `/config/candy_simplyfi_plus_registro.csv`.
3. Open an [issue](https://github.com/ichnusa82/candy-simplyfi-plus/issues) with the **model** (from the rating plate on the door edge), the **program used**, and attach the file.

---

## Credits

- The Home Assistant community for analysing the Candy simply-Fi protocol
- [ofalvai/home-assistant-candy](https://github.com/ofalvai/home-assistant-candy), the integration that paved the way

## Legal notice

### Trademarks
**Candy**, **Simply-Fi**, **hOn**, **Hoover** and **Haier** are registered trademarks of their respective owners (Candy Hoover Group S.r.l. / Haier Group). **Home Assistant** is a trademark of the Open Home Foundation.

These names are used **only to indicate which appliances this software is compatible with**. Their use does not imply any affiliation, sponsorship, endorsement or cooperation by the trademark owners.

**Candy Simply-Fi Plus is an independent, unofficial project.** It is not developed, supported or verified by Candy, Hoover or Haier. For support with the appliance, contact the official customer service only.

### Disclaimer
The software is provided **"as is"**, without warranty of any kind. It works by reading the data the dishwasher makes available on the local network; the protocol is not publicly documented and was reconstructed by observation.

The author is not liable for malfunctions, damage to the appliance, loss of warranty or any other problem arising from the use of this software.

This project contains no code, firmware or artwork from Candy / Haier.

## License

Released under the [MIT](LICENSE) license.
