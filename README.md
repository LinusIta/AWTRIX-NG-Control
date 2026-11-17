# AWTRIX NG Control

**Advanced Home Assistant Custom Integration for AWTRIX NG**

AWTRIX NG Control is a custom Home Assistant integration designed to provide centralized control and management of AWTRIX NG devices.

Developed primarily for the **Ulanzi TC002**, it combines HTTP API and MQTT functionality to manage applications, notifications, visual effects, Berry scripts, audio, multimedia files, backups and device maintenance.

**Version:** 1.2.1  
**Languages:** English and Italian  
**Installation:** HACS or manual

## Features

### Display and Applications
- Display power and brightness
- Clock face selection
- Automatic application rotation
- Application selection, activation and individual enable/disable controls
- RGB indicators
- Transition effects and duration settings

### Notifications
- Standard and advanced notifications
- Custom multi-region layouts
- Text, colors, icons, sounds and scrolling
- Notification duration and stacking
- Dismiss notifications by name

### Visual Effects
- Animated backgrounds
- Effects and color palettes
- Weather-style overlays
- Application transition animations
- Immediate display of newly created applications

### Berry Scripts
- List and inspect installed scripts
- Install, update and remove scripts
- Read and modify script configuration
- Export and restore supported script settings

### Audio and Internet Radio
- Home Assistant TTS to AWTRIX NG MP3 playback (v1.2.0)
- Radio station selection and playback controls
- Audio status and diagnostics
- MP3 management
- RTTTL melodies
- Audio volume and playback control

### File Management
- Browse device files
- Upload and download supported multimedia files
- Delete files
- Manage icons, MP3s, palettes and melodies
- Monitor storage usage

### Backup, Restore and Maintenance
- Create and inspect backup archives
- Verify archive integrity
- Selectively restore supported files, scripts and settings
- Device health and system diagnostics
- Controlled reboot

**Note:** The integration's selective backup is not a replacement for the firmware's native full backup.

## Installation via HACS

1. Open **HACS** in Home Assistant.
2. Open the menu and select **Custom repositories**.
3. Add this repository:

   `https://github.com/LinusIta/AWTRIX-NG-Control`

4. Select **Integration** as the repository type.
5. Find **AWTRIX NG Control** and select **Download**.
6. Restart Home Assistant.
7. Open **Settings → Devices & Services → Add Integration**.
8. Search for **AWTRIX NG Control** and follow the configuration flow.

An existing configuration entry should be preserved when upgrading.

## Manual Installation

Copy the directory:

`custom_components/awtrix_ng_control`

into your Home Assistant configuration directory:

`/config/custom_components/awtrix_ng_control`

Restart Home Assistant and add the integration through **Settings → Devices & Services**.

## Usage Examples

List applications installed on the device:

```yaml
action: awtrix_ng_control.app_list_http
data:
  device: tc002
```

Display an application immediately:

```yaml
action: awtrix_ng_control.app_show_http
data:
  device: tc002
  name: Beautiful-Weather
  fast: true
```

Retrieve Berry script configuration:

```yaml
action: awtrix_ng_control.script_config_get
data:
  device: tc002
  name: Beautiful-Weather
```

## Documentation

- [Manuale completo in italiano](MANUALE_IT.md)
- [Full English User Guide](MANUALE_EN.md)

Both guides include available actions, configuration parameters and YAML examples.

## Compatibility

Developed primarily for **Ulanzi TC002 running AWTRIX NG**.

Compatibility with other AWTRIX NG devices and firmware versions may vary.

## Development and Testing Status

This is a feature-complete initial release. Core features have been tested on an Ulanzi TC002, including application selection, Berry script configuration retrieval, audio diagnostics, visual application creation and file listing.

Some advanced operations, particularly backup restoration, file modification and device maintenance, still require additional validation on physical hardware.

**Use destructive actions and restore operations with care.**

## Feedback and Contributions

Bug reports, feature requests and contributions are welcome through [GitHub Issues](https://github.com/LinusIta/AWTRIX-NG-Control/issues).

This project was developed with the assistance of ChatGPT.

## Acknowledgements

Thanks to the AWTRIX NG developers for creating the firmware and providing the APIs that make this integration possible.


## Live Screen — AWTRIX 3 and AWTRIX NG (v1.1.6)

Mirror the physical display in a Home Assistant dashboard with approximately one update per second, using MQTT and the Home Assistant WebSocket API. No camera, PNG snapshots, or disk writes are required.

- **TC001 / AWTRIX 3 v0.98:** 32 × 8 LED matrix.
- **TC002 / AWTRIX NG:** 52 × 16 LED matrix.
- Pixel-by-pixel LED rendering with a dark gap and a compact device-style bezel.
- On-demand polling while at least one Live Screen card is open; one polling session is shared across viewers.
- The Live Screen card requires a Home Assistant administrator account.

### Configure the dashboard resource

In **Dashboard → Edit → Resources**, register the following URL as a **JavaScript module**:

```text
/awtrix-ng-control/awtrix-live-screen.js
```

No query-string version suffix is required. When updating the JavaScript, reload the dashboard and, if necessary, clear the browser cache.

### TC002 — AWTRIX NG

```yaml
type: custom:awtrix-live-screen-card
prefix: tc002
firmware: awtrix_ng
title: TC002 · Live Screen
```

### TC001 — AWTRIX 3 (including firmware v0.98)

```yaml
type: custom:awtrix-live-screen-card
prefix: YOUR_TC001_MQTT_PREFIX
firmware: awtrix3
title: TC001 · Live Screen
```

Replace `YOUR_TC001_MQTT_PREFIX` with the real MQTT topic prefix configured on the TC001.

### MQTT diagnostics

| Firmware | Request topic | Response topic |
| --- | --- | --- |
| AWTRIX 3 | `<prefix>/sendscreen` | `<prefix>/screen` |
| AWTRIX NG | `<prefix>/cmd/screen/get` | `<prefix>/state/screen` |

Both TC001 and TC002 Live Screen views have been tested on physical devices. Some other advanced integration features still require testing; see the full manuals.

See [Live Screen instructions (Italian and English)](LIVE_SCREEN_IT_EN.md).

## Text-to-Speech (v1.2.0)

The `awtrix_ng_control.say` action synthesizes speech using an existing Home Assistant TTS entity and sends an MP3 clip directly to an **AWTRIX NG** device via its HTTP API. It has been tested on TC002 with `tts.edge_tts`. The Google AI TTS provider has not yet been confirmed on-device. The AWTRIX 3 Live Screen feature is unchanged; this TTS service is intended for AWTRIX NG HTTP devices.

Select an AWTRIX NG device with the graphical Home Assistant device selector (`device_id`), **or** provide its MQTT prefix (`device`, e.g. `tc002`), but not both. The selected device must have an accessible HTTP address.

```yaml
action: awtrix_ng_control.say
data:
  device: tc002
  engine: tts.edge_tts
  message: "This is a voice notification from Home Assistant."
```

Optional fields: `language`, `cache`, and provider-specific `options`. Generated clips must not exceed 2 MiB. TTS entities depend on the user's Home Assistant configuration.

## Version 1.2.1 — Localization update

- Complete English and Italian translations for Home Assistant entity names and 74 actions, including TTS.
- Translate radio, display, notification and HTTP diagnostic labels.
- Show **None** / **Default** in the English UI for existing **Nessuno** / **Predefinito** select values, without changing their raw values.
- Preserve entity unique IDs and existing automation targets.
- The HTTP diagnostic sensor now exposes canonical raw states (`not_configured`, `unreachable`, `partial`, `connected`); automations matching the previous Italian text need updating.

Thanks to [DaveBKC](https://github.com/DaveBKC) for contributing the broader localization work in PR #1.
