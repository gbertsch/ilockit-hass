from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
import secrets
from typing import Any

from aiohttp import BasicAuth, ClientResponseError, ClientSession
from yarl import URL

from homeassistant.util import dt as dt_util

DEFAULT_API_BASE = "https://tracking.ilockit.bike"

_LOGGER = logging.getLogger(__name__)


class ILockitApiClientError(Exception):
    """General ILockit API error."""


class ILockitAuthenticationError(ILockitApiClientError):
    """Raised when authentication fails."""


@dataclass
class ILockitDeviceState:
    """Subset of state returned by the ILockit API."""

    device_id: str
    name: str
    firmware_version: float | None = None
    locked: bool | None = None
    battery_level: int | None = None
    alarm_active: bool | None = None
    latitude: float | None = None
    longitude: float | None = None
    updated_at: datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    firmware_available: str | None = None


class ILockitApiClient:
    """Async client for the I LOCK IT Cloud API."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        base_url: str | None = None,
    ) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._base_url = (base_url or DEFAULT_API_BASE).rstrip("/")
        self._auth = BasicAuth(self._username, self._password)
        self._firmware_cache: dict[str, tuple[datetime, dict[str, Any] | None]] = {}
        self._last_devices: list[ILockitDeviceState] = []

    async def async_validate_credentials(self) -> None:
        """Validate credentials against the API by fetching device list."""
        _LOGGER.debug("Validating credentials for %s", self._username)
        await self._request_json("GET", "/api/devices")

    async def async_get_devices(self) -> list[ILockitDeviceState]:
        """Return an overview of devices and their state."""
        devices = await self._request_json("GET", "/api/devices")
        positions = []
        try:
            positions = await self._request_json("GET", "/api/positions")
        except ILockitApiClientError as err:
            _LOGGER.warning(
                "Positions request failed, proceeding without positions: %s", err
            )
        if not isinstance(devices, list):
            devices = []
        if not isinstance(positions, list):
            positions = []
        position_by_device: dict[int, dict[str, Any]] = {
            pos["deviceId"]: pos for pos in positions if isinstance(pos, dict) and "deviceId" in pos
        }

        states: list[ILockitDeviceState] = []
        for device in devices:
            device_id = device["id"]
            name = device.get("name") or f"ILockit {device_id}"
            firmware_version = self._parse_firmware_version(
                device.get("attributes", {}).get("firmwareVersion")
            )
            state = ILockitDeviceState(
                device_id=str(device_id),
                name=name,
                firmware_version=firmware_version,
                updated_at=self._parse_datetime(device.get("lastUpdate")),
                raw=device,
            )
            pos = position_by_device.get(device_id)
            if pos:
                state.latitude = pos.get("latitude")
                state.longitude = pos.get("longitude")
                state.updated_at = self._parse_datetime(
                    pos.get("fixTime") or pos.get("serverTime")
                )

            lock_info = await self._safe_lock_info(device_id)
            if lock_info:
                state.battery_level = lock_info.get("batteryLevel")
                state.locked = self._parse_lock_state(lock_info.get("lockState"))
                state.alarm_active = (
                    lock_info.get("alarmArmed") == 1
                    if lock_info.get("alarmArmed") is not None
                    else None
                )
                state.raw["lockInfo"] = lock_info

            fw = await self._async_get_firmware_info(name)
            if fw:
                state.firmware_available = fw.get("version")
                state.raw["firmware"] = fw

            states.append(state)

        self._last_devices = states
        return states

    async def async_set_lock_state(self, device_id: str, locked: bool) -> None:
        """Lock or unlock the given device."""
        direction = "close" if locked else "open"
        device_state = next(
            (d for d in self._last_devices if d.device_id == device_id), None
        ) if hasattr(self, "_last_devices") else None
        firmware = device_state.firmware_version if device_state else None
        payload: dict[str, Any] = {
            "deviceId": int(device_id),
            "id": 3,  # locking command
            "attributes": {},
        }

        if firmware is not None and firmware < 34:
            raise ILockitApiClientError(
                f"Locking command not supported on firmware {firmware}"
            )

        if firmware is None or firmware < 35.5:
            payload["attributes"]["lockingSeed"] = self._generate_seed()

        payload["attributes"]["direction"] = direction

        resp = await self._request_json("POST", "/api/commands/send", json=payload)
        _LOGGER.debug(
            "Lock command response for %s (fw=%s): %s", device_id, firmware, resp
        )

    async def async_close(self) -> None:
        """Close any underlying resources if needed."""
        # aiohttp session is owned by HA; no action required.
        return None

    async def async_start_firmware_update(self, device_id: str) -> dict[str, Any]:
        """Start a firmware update for a specific device."""
        params = {"deviceId": int(device_id)}
        resp = await self._request_json("POST", "/api/devices/firmware", params=params)
        _LOGGER.debug("Firmware update response for %s: %s", device_id, resp)
        return resp

    async def _async_get_lock_info(self, device_id: int) -> dict[str, Any] | None:
        """Request lock info for a given device and fetch the response event."""
        payload = {"deviceId": device_id, "id": 5}
        try:
            resp = await self._request_json("POST", "/api/commands/send", json=payload)
        except ILockitApiClientError as err:
            _LOGGER.debug("Lock info request failed for %s: %s", device_id, err)
            return None
        event_id = resp.get("eventId")
        if not event_id:
            _LOGGER.debug("No eventId returned for lock info request on %s", device_id)
            return None

        try:
            event = await self._request_json(
                "GET", "/api/events", params={"eventId": event_id}
            )
        except ILockitApiClientError as err:
            _LOGGER.debug(
                "Failed to fetch lock info event %s for %s: %s", event_id, device_id, err
            )
            return None

        return event.get("attributes")

    async def _safe_lock_info(self, device_id: int) -> dict[str, Any] | None:
        """Wrapper to avoid failing the whole update if lock info fails."""
        try:
            return await self._async_get_lock_info(device_id)
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Lock info retrieval failed for %s: %s", device_id, err)
            return None

    async def _async_get_firmware_info(self, name: str) -> dict[str, Any] | None:
        """Fetch firmware info by device name with simple daily caching."""
        if not name:
            return None
        cached = self._firmware_cache.get(name)
        if cached:
            fetched_at, data = cached
            if fetched_at and (dt_util.utcnow() - fetched_at).total_seconds() < 86400:
                return data
        try:
            payload = await self._request_json(
                "GET", "/api/devices/firmware", params={"name": name}
            )
            firmware = payload.get("firmware") if isinstance(payload, dict) else None
            self._firmware_cache[name] = (dt_util.utcnow(), firmware)
            return firmware
        except ILockitApiClientError as err:
            _LOGGER.debug("Firmware info request failed for %s: %s", name, err)
            self._firmware_cache[name] = (dt_util.utcnow(), None)
            return None

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an HTTP request and return parsed JSON."""
        url = URL(self._base_url + path)
        try:
            async with self._session.request(
                method,
                url,
                auth=self._auth,
                params=params,
                json=json,
                headers={"accept": "application/json"},
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except ClientResponseError as err:
            body = ""
            try:
                body = await err.response.text()
            except Exception:  # noqa: BLE001
                body = ""
            if err.status == 401:
                raise ILockitAuthenticationError("Unauthorized") from err
            raise ILockitApiClientError(
                f"HTTP error {err.status}: {err.message or ''} {body}".strip()
            ) from err
        except Exception as err:  # noqa: BLE001
            raise ILockitApiClientError(str(err)) from err

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return dt_util.parse_datetime(value)

    @staticmethod
    def _parse_lock_state(lock_state: int | None) -> bool | None:
        """Map lockState numeric value to bool."""
        if lock_state is None:
            return None
        if lock_state == 2:
            return True
        if lock_state == 1:
            return False
        return None

    @staticmethod
    def _parse_firmware_version(raw: Any) -> float | None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _generate_seed() -> str:
        # 16-byte random hex string
        return secrets.token_hex(16)
