from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ILockitDeviceState
from .const import DEFAULT_NAME, DOMAIN
from .coordinator import ILockitDataCoordinator


class ILockitEntity(CoordinatorEntity[ILockitDataCoordinator]):
    """Base entity shared by all iLockit platforms."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ILockitDataCoordinator, device_id: str) -> None:
        super().__init__(coordinator)
        self._device_id = device_id

    @property
    def _device(self) -> ILockitDeviceState | None:
        return next(
            (device for device in self.coordinator.data or [] if device.device_id == self._device_id),
            None,
        )

    @property
    def device_info(self) -> DeviceInfo:
        device = self._device
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=device.name if device else DEFAULT_NAME,
            entry_type=DeviceEntryType.DEVICE,
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        device = self._device
        return device.raw or {}

    @property
    def available(self) -> bool:
        return bool(self._device) and super().available
