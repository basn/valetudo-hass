"""Select entities for Valetudo REST."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ValetudoCoordinator
from .entity import ValetudoRestEntity, format_operation_mode, normalize_operation_mode


@dataclass(frozen=True, kw_only=True)
class ValetudoSelectDescription(SelectEntityDescription):
    """Valetudo select description."""

    options_key: str
    value_key: str
    setter: str


SELECTS: tuple[ValetudoSelectDescription, ...] = (
    ValetudoSelectDescription(
        key="fan_speed",
        name="Fan speed",
        options_key="fan_presets",
        value_key="fan_speed",
        setter="set_fan_preset",
    ),
    ValetudoSelectDescription(
        key="water_grade",
        name="Water grade",
        options_key="water_presets",
        value_key="water_grade",
        setter="set_water_preset",
    ),
    ValetudoSelectDescription(
        key="operation_mode",
        name="Operation mode",
        options_key="operation_mode_presets",
        value_key="operation_mode",
        setter="set_operation_mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Valetudo selects."""
    coordinator: ValetudoCoordinator = entry.runtime_data
    async_add_entities(ValetudoSelect(coordinator, entry.entry_id, description) for description in SELECTS)


class ValetudoSelect(ValetudoRestEntity, SelectEntity):
    """Valetudo select entity."""

    entity_description: ValetudoSelectDescription

    def __init__(
        self,
        coordinator: ValetudoCoordinator,
        entry_id: str,
        description: ValetudoSelectDescription,
    ) -> None:
        super().__init__(coordinator, entry_id)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"

    @property
    def current_option(self) -> str | None:
        raw_value = self.coordinator.data.get(self.entity_description.value_key)

        if self.entity_description.key == "operation_mode":
            return format_operation_mode(raw_value) or raw_value

        return raw_value

    @property
    def options(self) -> list[str]:
        raw_options = self.coordinator.data.get(self.entity_description.options_key, []) or []

        if self.entity_description.key != "operation_mode":
            return list(raw_options)

        display_options: list[str] = []
        for raw_option in raw_options:
            display = format_operation_mode(raw_option) or raw_option
            if display not in display_options:
                display_options.append(display)
        return display_options

    async def async_select_option(self, option: str) -> None:
        if self.entity_description.key == "operation_mode":
            option = self._coerce_operation_mode_option(option)

        await getattr(self.coordinator.client, self.entity_description.setter)(option)
        await self.coordinator.async_request_refresh()

    def _coerce_operation_mode_option(self, option: str) -> str:
        raw_options = self.coordinator.data.get("operation_mode_presets", []) or []

        if option in raw_options:
            return option

        normalized = normalize_operation_mode(option)
        for raw_option in raw_options:
            if normalize_operation_mode(raw_option) == normalized:
                return raw_option

        return option
