from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ILockitApiClient,
    ILockitApiClientError,
    ILockitAuthenticationError,
    ILockitDeviceState,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ILockitDataCoordinator(DataUpdateCoordinator[list[ILockitDeviceState]]):
    """Coordinate data updates from the ILockit API."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: ILockitApiClient,
        update_interval,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} data",
            update_interval=update_interval,
        )
        self.entry = entry
        self.api = api

    async def _async_update_data(self) -> list[ILockitDeviceState]:
        """Fetch data from API endpoint."""
        try:
            return await self.api.async_get_devices()
        except ILockitAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except ILockitApiClientError as err:
            raise UpdateFailed(str(err)) from err
