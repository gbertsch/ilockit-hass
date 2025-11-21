from __future__ import annotations

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import ILockitApiClient
from .const import DATA_API, DATA_COORDINATOR, DOMAIN
from .coordinator import ILockitDataCoordinator
from .entity import ILockitEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: ILockitDataCoordinator = data[DATA_COORDINATOR]
    api: ILockitApiClient = data[DATA_API]

    added: set[str] = set()

    @callback
    def _sync_entities() -> None:
        new_entities: list[ILockitLockEntity] = []
        for device in coordinator.data or []:
            if device.device_id in added:
                continue
            new_entities.append(ILockitLockEntity(coordinator, api, device.device_id))
            added.add(device.device_id)
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.async_add_listener(_sync_entities)


class ILockitLockEntity(ILockitEntity, LockEntity):
    """Representation of an iLockit lock."""

    _attr_translation_key = "lock"

    def __init__(
        self,
        coordinator: ILockitDataCoordinator,
        api: ILockitApiClient,
        device_id: str,
    ) -> None:
        super().__init__(coordinator, device_id)
        self._api = api
        self._attr_unique_id = f"{device_id}-lock"

    @property
    def is_locked(self) -> bool | None:
        device = self._device
        return device.locked if device else None

    async def async_lock(self, **kwargs) -> None:
        await self._api.async_set_lock_state(self._device_id, True)
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs) -> None:
        await self._api.async_set_lock_state(self._device_id, False)
        await self.coordinator.async_request_refresh()
