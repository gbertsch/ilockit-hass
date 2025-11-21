## iLockit – Home Assistant integration

Custom integration for I LOCK IT GPS locks. Exposes lock control, battery level, alarm status, and device location.

### Requirements
- Home Assistant Core 2023.10 or newer recommended
- I LOCK IT Cloud credentials (tracking.ilockit.bike)

### Installation (HACS - Custom repository)
1. In HACS → Integrations → Custom repositories, add `https://github.com/gbertsch/ilockit-hass` with category `Integration`.
2. Install “iLockit” from HACS, then restart Home Assistant.

### Configuration
- Settings → Devices & Services → Add Integration → search “iLockit”.
- Enter your cloud username/password.
- After setup, adjust polling interval in the integration Options (default 30s, min 10s, max 300s) to balance freshness vs. API limits.

### Entities
- Lock: lock/unlock per device.
- Sensor: battery level.
- Binary sensor: alarm armed/active status.
- Device tracker: GPS location.

### Notes
- API base: `https://tracking.ilockit.bike` (Basic Auth).
- Lock/unlock uses the `locking` command; device state is derived from `devices`, `positions`, and `getLockInfo` responses.
