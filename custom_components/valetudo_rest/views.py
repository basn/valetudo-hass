"""HTTP views for Valetudo REST."""

from __future__ import annotations

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class ValetudoMapView(HomeAssistantView):
    """Serve raw Valetudo map payloads to the frontend card."""

    url = "/api/valetudo_rest/{entry_id}/map"
    name = "api:valetudo_rest:map"
    requires_auth = True

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        """Return current map payload for a config entry."""
        hass: HomeAssistant = request.app["hass"]
        entry: ConfigEntry | None = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != DOMAIN or entry.runtime_data is None:
            return self.json_message("Unknown Valetudo REST entry", status_code=404)

        coordinator = entry.runtime_data
        map_data = coordinator.data.get("raw_state", {}).get("map")
        if not map_data:
            return self.json_message("Map payload unavailable", status_code=404)

        return web.json_response(
            {
                "map": map_data,
                "status": coordinator.data.get("status"),
                "status_flag": coordinator.data.get("status_flag"),
                "battery_level": coordinator.data.get("battery_level"),
                "dock_status": coordinator.data.get("dock_status"),
            }
        )
