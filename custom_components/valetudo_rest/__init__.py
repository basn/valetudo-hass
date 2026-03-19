"""The Valetudo REST integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .api import ValetudoApiClient
from .const import CONF_SCAN_INTERVAL, DEFAULT_NAME, DOMAIN, PLATFORMS
from .coordinator import ValetudoCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Valetudo REST from a config entry."""
    session = async_get_clientsession(hass)
    client = ValetudoApiClient(session, entry.data[CONF_HOST])
    coordinator = ValetudoCoordinator(
        hass,
        client,
        entry.data.get(CONF_NAME, DEFAULT_NAME),
        timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 10))),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer="Valetudo",
        model=coordinator.data.get("meta", {}).get("model", "Vacuum Robot"),
        name=entry.data.get(CONF_NAME, DEFAULT_NAME),
        configuration_url=f"http://{entry.data[CONF_HOST]}",
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
