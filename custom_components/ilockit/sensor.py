from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
        new_entities: list[ILockitBatterySensor] = []
        for device in coordinator.data or []:
            if device.device_id in added:
                continue
            new_entities.append(ILockitBatterySensor(coordinator, device.device_id))
            added.add(device.device_id)
        if new_entities:
            async_add_entities(new_entities)

    _sync_entities()
    coordinator.async_add_listener(_sync_entities)


class ILockitBatterySensor(ILockitEntity, SensorEntity):
    """Battery level sensor for an iLockit device."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "battery"

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = f"{device_id}-battery"

    @property
    def native_value(self) -> int | None:
        device = self._device
        return device.battery_level if device else None
