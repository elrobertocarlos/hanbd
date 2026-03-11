# HANBD Home Assistant Integration

Custom integration for HANBD smart litter boxes.

This integration connects to the HANBD cloud API and exposes your device data and controls in Home Assistant.

## Features

- Config flow setup from UI (phone + password)
- Cloud polling integration (`iot_class: cloud_polling`)
- Device entities created per HANBD device
- Button control:
  - `Clean` button (`CLEAN` operation)
- Sensors:
  - Status (`activeStateName`)
  - Firmware version
  - Waste box level (`number1`)
  - Litter level (`number2`)
  - Uses today (`number3`)
  - Cat weight (`number4`)
  - Number 5 (`number5`)
  - Number 6 (`number6`)
- Binary sensors:
  - Online
  - Roller Full
- Busy-state handling for clean command with user-friendly Home Assistant error message

## Requirements

- Home Assistant `2025.2.4` or newer
- HACS `2.0.5` or newer

## Installation

### HACS (recommended)

1. Open HACS.
2. Add this repository as a custom repository:
   - URL: `https://github.com/elrobertocarlos/hanbd`
   - Category: `Integration`
3. Install `hanbd`.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/hanbd` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to Settings > Devices & Services.
2. Click Add Integration.
3. Search for `hanbd`.
4. Enter your HANBD account phone number and password.

## Notes on Updates and Polling

The official app appears to use regular HTTP polling (`/member/device/list` and `/member/device/get`) rather than a push channel.

This integration currently uses a coordinator update interval of 1 hour and also refreshes after operations. If you need faster updates, this can be tuned in a future update.

## Known Limitations

- Quiet Mode switch does not yet send on/off commands because the exact control payload/endpoint mapping is still being finalized.
- Some numeric sensor fields (`number5`, `number6`) are currently unknown labels and may be renamed when their semantics are confirmed.

## Development

Useful scripts:

- `scripts/setup` - Prepare dev environment
- `scripts/lint` - Lint project
- `scripts/develop` - Start local Home Assistant development flow

## Troubleshooting

- Authentication fails:
  - Verify phone number and password.
  - Confirm account can log in via official app.
- Device appears busy when pressing Clean:
  - The device may already be cleaning or in another active operation. Wait and retry.
- No entities shown:
  - Reconfigure integration and check Home Assistant logs for `custom_components.hanbd`.

## Disclaimer

This is an unofficial integration and is not affiliated with HANBD.

## License

See `LICENSE`.
