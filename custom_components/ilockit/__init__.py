from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from .api import ILockitApiClient
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DATA_API,
    DATA_COORDINATOR,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    MAX_SCAN_INTERVAL_SECONDS,
    MIN_SCAN_INTERVAL_SECONDS,
    PLATFORMS,
)
from .coordinator import ILockitDataCoordinator

ILockitConfigEntry = ConfigEntry


def _entry_update_interval(entry: ILockitConfigEntry) -> timedelta:
    seconds = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_SECONDS)
    # Basic guardrails; final limits should match API rate limits once known.
    if seconds < MIN_SCAN_INTERVAL_SECONDS:
        seconds = MIN_SCAN_INTERVAL_SECONDS
    if seconds > MAX_SCAN_INTERVAL_SECONDS:
        seconds = MAX_SCAN_INTERVAL_SECONDS
    return timedelta(seconds=seconds)


async def async_setup_entry(hass: HomeAssistant, entry: ILockitConfigEntry) -> bool:
    """Set up iLockit from a config entry."""
    session = async_get_clientsession(hass)
    api = ILockitApiClient(
        session=session,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    coordinator = ILockitDataCoordinator(
        hass, entry, api, update_interval=_entry_update_interval(entry)
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        DATA_API: api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_request_position(call) -> None:
        device_id = str(call.data["device_id"])
        await api.async_request_position(device_id)
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "request_position",
        handle_request_position,
        schema=vol.Schema({vol.Required("device_id"): vol.Coerce(str)}),
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ILockitConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
