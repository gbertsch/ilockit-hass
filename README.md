# ilockit-hass

Custom Home Assistant integration for the iLockit cloud API. Initial focus areas:
- lock/ unlock state
- battery level
- alarm status
- device location (device tracker)

## Current status
- Scaffolding for a Home Assistant config flow, coordinator, and entity platforms (lock, battery sensor, alarm binary sensor, device tracker).
- API client now talks to `https://tracking.ilockit.bike` with basic auth, pulls devices, latest positions, and issues `getLockInfo` commands to derive battery/lock/alarm state; lock/unlock uses the `locking` command (id 3) with direction attribute.
- Translation strings and placeholders are in place for UI configuration.
- Polling interval is adjustable via the integration options (default 30s, clamped between 10s–300s) so we can align update rate with the cloud API, especially for location freshness.
- Dynamic entity add: when devices are added to the account, they appear on the next refresh without reinstalling the integration.
- Firmware info: fetched daily via `/api/devices/firmware` and exposed in entity attributes; available version shown if provided by API.

## Repository layout
- `custom_components/ilockit/manifest.json` – integration metadata for Home Assistant.
- `custom_components/ilockit/api.py` – async client stub to be filled with the iLockit Cloud API authentication and state calls.
- `custom_components/ilockit/coordinator.py` – `DataUpdateCoordinator` for polling device state.
- `custom_components/ilockit/config_flow.py` – UI-based configuration (username/password, optional API base URL).
- `custom_components/ilockit/*.py` – platform stubs (lock, battery sensor, alarm binary sensor, device tracker).
- `custom_components/ilockit/translations/en.json` – config flow and entity labels.

## Development quickstart
1. Clone this repo where your Home Assistant `config` directory is reachable.
2. Copy or link `custom_components/ilockit` into `config/custom_components/ilockit`.
3. Restart Home Assistant.
4. Add the integration via Settings → Devices & Services → “Add Integration” → search for “iLockit.”
5. Enter your tracking.ilockit.bike username/password. Multiple accounts are supported by adding the integration again with different credentials.

## Implementation checklist (next iterations)
- Verify lock-info/position polling cadence vs. API limits; consider caching or throttling lock-info requests per device if needed.
- Add unit tests around the API client and coordinator once endpoints are known.
- Consider HACS metadata once the integration is functional.
