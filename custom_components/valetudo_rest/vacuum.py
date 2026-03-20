"""Vacuum platform for Valetudo REST."""

from __future__ import annotations

from typing import Any

from homeassistant.components.vacuum import StateVacuumEntity, VacuumActivity, VacuumEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CUSTOM_ORDER,
    ATTR_ITERATIONS,
    ATTR_SEGMENT_IDS,
    COMMAND_HOME,
    COMMAND_LOCATE,
    COMMAND_PAUSE,
    COMMAND_SEGMENT_CLEAN,
    COMMAND_START,
    COMMAND_STOP,
    MAP_VIEW_URL,
)
from .coordinator import ValetudoCoordinator
from .entity import ValetudoRestEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Valetudo vacuum entity."""
    coordinator: ValetudoCoordinator = entry.runtime_data
    async_add_entities([ValetudoRestVacuum(coordinator, entry.entry_id)])


class ValetudoRestVacuum(ValetudoRestEntity, StateVacuumEntity):
    """Representation of a Valetudo vacuum via REST."""

    _attr_name = None
    _attr_supported_features = (
        VacuumEntityFeature.START
        | VacuumEntityFeature.STOP
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.SEND_COMMAND
    )

    def __init__(self, coordinator: ValetudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_vacuum"

    @property
    def activity(self) -> VacuumActivity | None:
        """Return vacuum activity."""
        status = self.coordinator.data.get("status")
        dock_status = self.coordinator.data.get("dock_status")

        if status == "cleaning":
            return VacuumActivity.CLEANING
        if status == "paused":
            return VacuumActivity.PAUSED
        if status in {"returning", "docking"}:
            return VacuumActivity.RETURNING
        if status in {"idle", "docked"} or dock_status == "idle":
            return VacuumActivity.DOCKED
        return VacuumActivity.IDLE

    @property
    def battery_level(self) -> int | None:
        """Return battery level."""
        return self.coordinator.data.get("battery_level")

    @property
    def fan_speed(self) -> str | None:
        """Return current fan speed."""
        return self.coordinator.data.get("fan_speed")

    @property
    def fan_speed_list(self) -> list[str]:
        """Return available fan speeds."""
        return self.coordinator.data.get("fan_presets") or []

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        seg_props = self.coordinator.data.get("segment_properties") or {}
        
        # Safely handle iterationCount whether it's a dict or other type
        iteration_count_raw = seg_props.get("iterationCount")
        if isinstance(iteration_count_raw, dict):
            max_iterations = iteration_count_raw.get("max")
        else:
            max_iterations = None
        
        return {
            "dock_status": self.coordinator.data.get("dock_status"),
            "status_flag": self.coordinator.data.get("status_flag"),
            "battery_flag": self.coordinator.data.get("battery_flag"),
            "operation_mode": self.coordinator.data.get("operation_mode"),
            "water_grade": self.coordinator.data.get("water_grade"),
            "mop_attached": self.coordinator.data.get("mop_attached"),
            "segment_count": self.coordinator.data.get("segment_count"),
            "custom_order_supported": seg_props.get("customOrderSupport", False),
            "max_iterations": max_iterations,
            "map_nonce": self.coordinator.data.get("map_nonce"),
            "map_data_url": MAP_VIEW_URL.format(entry_id=self._entry_id),
        }

    async def async_start(self) -> None:
        """Start the vacuum."""
        await self.coordinator.client.basic_action("start")
        await self.coordinator.async_request_refresh()

    async def async_stop(self, **kwargs: Any) -> None:
        """Stop the vacuum."""
        await self.coordinator.client.basic_action("stop")
        await self.coordinator.async_request_refresh()

    async def async_pause(self) -> None:
        """Pause the vacuum."""
        await self.coordinator.client.basic_action("pause")
        await self.coordinator.async_request_refresh()

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Return the vacuum to base."""
        await self.coordinator.client.basic_action("home")
        await self.coordinator.async_request_refresh()

    async def async_locate(self, **kwargs: Any) -> None:
        """Locate the vacuum."""
        await self.coordinator.client.locate()
        await self.coordinator.async_request_refresh()

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set the fan speed."""
        await self.coordinator.client.set_fan_preset(fan_speed)
        await self.coordinator.async_request_refresh()

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send custom Valetudo commands."""
        handled = False
        
        if command == COMMAND_SEGMENT_CLEAN:
            data = params if isinstance(params, dict) else {}
            raw_segment_ids = data.get(ATTR_SEGMENT_IDS)
            
            # Ensure segment_ids is a list
            if not isinstance(raw_segment_ids, list):
                return
            if not raw_segment_ids:
                return
                
            segment_ids = [str(segment) for segment in raw_segment_ids]
            
            # Safely convert iterations to int, defaulting to 1
            try:
                iterations = int(data.get(ATTR_ITERATIONS) or 1)
            except (ValueError, TypeError):
                iterations = 1
                
            await self.coordinator.client.segment_clean(
                segment_ids=segment_ids,
                iterations=iterations,
                custom_order=bool(data.get(ATTR_CUSTOM_ORDER, True)),
            )
            handled = True
        elif command == COMMAND_LOCATE:
            await self.coordinator.client.locate()
            handled = True
        elif command == COMMAND_HOME:
            await self.coordinator.client.basic_action("home")
            handled = True
        elif command == COMMAND_PAUSE:
            await self.coordinator.client.basic_action("pause")
            handled = True
        elif command == COMMAND_STOP:
            await self.coordinator.client.basic_action("stop")
            handled = True
        elif command == COMMAND_START:
            await self.coordinator.client.basic_action("start")
            handled = True
        
        if handled:
            await self.coordinator.async_request_refresh()
