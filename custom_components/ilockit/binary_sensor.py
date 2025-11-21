from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    entities: list[ILockitAlarmBinarySensor] = [
        ILockitAlarmBinarySensor(coordinator, device.device_id)
        for device in coordinator.data or []
    ]
    async_add_entities(entities)


class ILockitAlarmBinarySensor(ILockitEntity, BinarySensorEntity):
    """Alarm status sensor for an iLockit device."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "alarm"

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}-alarm"

    @property
    def is_on(self) -> bool | None:
        device = self._device
        return device.alarm_active if device else None
