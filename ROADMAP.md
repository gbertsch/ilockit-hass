## iLockit Home Assistant integration – implementation plan

### Milestone 1: API client bring-up
- Extract authentication flow and endpoints for device list/status from `ILOCKIT_CLOUD_API_v1.18.pdf`.
- Implement `async_validate_credentials` to fail fast on bad login.
- Implement `async_get_devices` to return battery, lock state, alarm, GPS, and raw payload (for future entities).
- Add logging around rate limits and non-200 responses with structured errors.

### Milestone 2: Entity wiring and commands
- Populate Coordinator with real data and confirm entity creation for lock, battery, alarm, and tracker.
- Wire `async_set_lock_state` to lock/unlock endpoints; surface meaningful errors to HA notifications.
- Consider additional entities exposed by the API (e.g., ride status, connection state).

### Milestone 3: Quality and delivery
- Add unit tests for the API client and coordinator using recorded fixtures.
- Add config flow validation (e.g., duplicate prevention on device id, optional polling interval).
- Document setup/testing steps in README and consider HACS metadata once stable.
