from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
        new_entities: list[ILockitAlarmBinarySensor] = []
        for device in coordinator.data or []:
            if device.device_id in added:
                continue
            new_entities.append(
                ILockitAlarmBinarySensor(coordinator, device.device_id)
            )
            added.add(device.device_id)
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.async_add_listener(_sync_entities)


class ILockitAlarmBinarySensor(ILockitEntity, BinarySensorEntity):
    """Alarm status sensor for an iLockit device."""

    _attr_device_class = BinarySensorDeviceClass.SAFETY
    _attr_translation_key = "alarm"
    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_name = "Alarm"
        self._attr_unique_id = f"{device_id}-alarm"

    @property
    def is_on(self) -> bool | None:
        device = self._device
        return device.alarm_active if device else None

    @property
    def extra_state_attributes(self) -> dict:
        attrs = super().extra_state_attributes
        device = self._device
        if device and device.firmware_version is not None:
            attrs = {**attrs, "firmware_version": device.firmware_version}
        return attrs
