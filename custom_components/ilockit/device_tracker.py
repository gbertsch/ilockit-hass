from __future__ import annotations

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.components.device_tracker.const import SourceType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    added: set[str] = set()

    @callback
    def _sync_entities() -> None:
        new_entities: list[ILockitDeviceTrackerEntity] = []
        for device in coordinator.data or []:
            if device.device_id in added:
                continue
            new_entities.append(
                ILockitDeviceTrackerEntity(coordinator, device.device_id)
            )
            added.add(device.device_id)
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.async_add_listener(_sync_entities)


class ILockitDeviceTrackerEntity(ILockitEntity, TrackerEntity):
    """Device tracker for an iLockit device."""

    _attr_translation_key = "location"
    _attr_should_poll = False
    _attr_icon = "mdi:map-marker"

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Location"
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
