from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import ILockitDataCoordinator
from .entity import ILockitEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ILockitDataCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    entities: list[ILockitDeviceTrackerEntity] = [
        ILockitDeviceTrackerEntity(coordinator, device.device_id)
        for device in coordinator.data or []
    ]
    async_add_entities(entities)


class ILockitDeviceTrackerEntity(ILockitEntity, TrackerEntity):
    """Device tracker for an iLockit device."""

    _attr_translation_key = "location"
    _attr_should_poll = False

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}-tracker"

    @property
    def latitude(self) -> float | None:
        device = self._device
        return device.latitude if device else None

    @property
    def longitude(self) -> float | None:
        device = self._device
        return device.longitude if device else None

    @property
    def source_type(self) -> SourceType:
        return SourceType.GPS
