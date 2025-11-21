## Development notes

- The integration polls the iLockit Cloud API at a configurable interval (default 30s, min 10s, max 300s). Adjust via the integration Options in Home Assistant.
- Devices are discovered from `/api/devices`; positions from `/api/positions`; lock/battery/alarm data from `getLockInfo` (command id 5).
- Lock/unlock uses `locking` (command id 3) with the `direction` attribute.
- Dynamic entities: when the device list changes, new entities are added automatically on the next coordinator refresh.
- Debugging: enable debug logs in Home Assistant
  ```yaml
  logger:
    logs:
      custom_components.ilockit: debug
  ```
  Then restart and check Logs for request/response status info.
