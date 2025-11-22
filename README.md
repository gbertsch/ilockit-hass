# ilockit-hass

Custom Home Assistant integration for the iLockit cloud API. Initial focus areas:
- lock/ unlock state
- battery level
- alarm status
- device location (device tracker)

## Current status
- Read-only location/identity: pulls devices from `/api/devices` (name, label, firmwareVersion) and latest positions from `/api/positions`; exposes device tracker entities only.
- Dynamic entity add: when devices are added to the account, they appear on the next refresh without reinstalling the integration.
- Polling interval is adjustable via the integration options (default 30s, clamped between 10s–300s).

## Repository layout
- `custom_components/ilockit/manifest.json` – integration metadata for Home Assistant.
- `custom_components/ilockit/api.py` – async client stub to be filled with the iLockit Cloud API authentication and state calls.
- `custom_components/ilockit/coordinator.py` – `DataUpdateCoordinator` for polling device state.
- `custom_components/ilockit/config_flow.py` – UI-based configuration (username/password).
- `custom_components/ilockit/*.py` – platform stubs (currently only device tracker is active).
- `custom_components/ilockit/translations/en.json` – config flow and entity labels.

## Development quickstart
1. Clone this repo where your Home Assistant `config` directory is reachable.
2. Copy or link `custom_components/ilockit` into `config/custom_components/ilockit`.
3. Restart Home Assistant.
4. Add the integration via Settings → Devices & Services → “Add Integration” → search for “iLockit.”
5. Enter your tracking.ilockit.bike username/password. Multiple accounts are supported by adding the integration again with different credentials.

## Implementation checklist (next iterations)
- Re-enable lock/battery/alarm/charging/theft entities once manager access is available and `lockInfo`/commands succeed.
- Add unit tests around the API client and coordinator once endpoints are known.
- Consider HACS metadata once the integration is functional.
