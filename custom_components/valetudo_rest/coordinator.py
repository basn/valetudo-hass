"""Coordinator for Valetudo REST."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ValetudoApiClient, ValetudoApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _attribute_value(attributes: list[dict[str, Any]], attr_type: str, key: str = "value") -> Any:
    for attr in attributes:
        if attr.get("__class") == attr_type:
            return attr.get(key)
    return None


def _preset_value(attributes: list[dict[str, Any]], preset_type: str) -> Any:
    for attr in attributes:
        if attr.get("__class") == "PresetSelectionStateAttribute" and attr.get("type") == preset_type:
            return attr.get("value")
    return None


def _attachment_state(attributes: list[dict[str, Any]], attachment_type: str) -> bool | None:
    for attr in attributes:
        if attr.get("__class") == "AttachmentStateAttribute" and attr.get("type") == attachment_type:
            return attr.get("attached")
    return None


def _battery_state(attributes: list[dict[str, Any]]) -> tuple[int | None, str | None]:
    for attr in attributes:
        if attr.get("__class") == "BatteryStateAttribute":
            return attr.get("level"), attr.get("flag")
    return None, None


def _status_state(attributes: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for attr in attributes:
        if attr.get("__class") == "StatusStateAttribute":
            return attr.get("value"), attr.get("flag")
    return None, None


class ValetudoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Valetudo REST data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: ValetudoApiClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{name}",
            update_interval=update_interval,
        )
        self.client = client
        self.device_name = name

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            raw = await self.client.fetch_all()
        except ValetudoApiError as err:
            raise UpdateFailed(str(err)) from err

        state = raw.get("state", {})
        attributes = state.get("attributes", [])
        battery_level, battery_flag = _battery_state(attributes)
        status, status_flag = _status_state(attributes)

        normalized = {
            "raw": raw,
            "raw_state": state,
            "battery_level": battery_level,
            "battery_flag": battery_flag,
            "dock_status": _attribute_value(attributes, "DockStatusStateAttribute"),
            "fan_speed": _preset_value(attributes, "fan_speed"),
            "water_grade": _preset_value(attributes, "water_grade"),
            "operation_mode": _preset_value(attributes, "operation_mode"),
            "status": status,
            "status_flag": status_flag,
            "mop_attached": _attachment_state(attributes, "mop"),
            "segment_count": len(raw.get("segments", [])),
            "segments": raw.get("segments", []),
            "segment_properties": raw.get("segment_properties", {}),
            "consumables": {
                f"{item.get('type', 'unknown')}_{item.get('subType', 'main')}": item.get("remaining", {}).get("value")
                for item in raw.get("consumables", [])
                if isinstance(item, dict)
            },
            "fan_presets": raw.get("fan_presets", []),
            "water_presets": raw.get("water_presets", []),
            "operation_mode_presets": raw.get("operation_mode_presets", []),
            "map_nonce": state.get("map", {}).get("metaData", {}).get("nonce"),
            "meta": {
                "pixel_size": state.get("map", {}).get("pixelSize"),
                "map_size": state.get("map", {}).get("size"),
            },
        }
        return normalized
